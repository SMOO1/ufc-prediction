package com.smoo1.ufcprediction.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

@Service
public class UpcomingFightService {

    private static final Duration TIMEOUT = Duration.ofSeconds(120);
    private static final Duration CACHE_TIME = Duration.ofHours(1);

    private final ObjectMapper objectMapper;
    private final Path projectRoot;
    private final String configuredPython;
    private JsonNode cachedResponse;
    private Instant cacheExpiresAt = Instant.EPOCH;

    public UpcomingFightService(
            ObjectMapper objectMapper,
            @Value("${ufc.python.project-root:.}") String projectRoot,
            @Value("${ufc.python.executable:}") String configuredPython
    ) {
        this.objectMapper = objectMapper;
        this.projectRoot = Path.of(projectRoot).toAbsolutePath().normalize();
        this.configuredPython = configuredPython == null ? "" : configuredPython.trim();
    }

    public synchronized JsonNode upcoming() {
        if (cachedResponse != null && Instant.now().isBefore(cacheExpiresAt)) {
            return cachedResponse;
        }

        Path script = projectRoot.resolve("upcoming_predictions.py");
        if (!Files.isRegularFile(script)) {
            throw new PredictionEngineException("Upcoming fight predictions are not configured on this server");
        }

        try {
            Process process = new ProcessBuilder(List.of(resolvePython(), script.toString()))
                    .directory(projectRoot.toFile())
                    .start();
            CompletableFuture<String> stdout = readAsync(process.getInputStream());
            CompletableFuture<String> stderr = readAsync(process.getErrorStream());
            boolean finished = process.waitFor(TIMEOUT.toSeconds(), TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new PredictionEngineException("Upcoming fight predictions timed out");
            }
            String output = stdout.join().trim();
            String error = stderr.join().trim();
            if (process.exitValue() != 0) {
                throw new PredictionEngineException(cleanEngineError(error.isBlank() ? output : error));
            }
            cachedResponse = objectMapper.readTree(output);
            cacheExpiresAt = Instant.now().plus(CACHE_TIME);
            return cachedResponse;
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new PredictionEngineException("Upcoming fight predictions were interrupted", exception);
        } catch (IOException exception) {
            throw new PredictionEngineException("Could not load upcoming fight predictions", exception);
        }
    }

    private String resolvePython() {
        if (!configuredPython.isBlank()) {
            return configuredPython;
        }
        Path virtualEnvironment = projectRoot.resolve(".venv/bin/python3");
        return Files.isExecutable(virtualEnvironment) ? virtualEnvironment.toString() : "python3";
    }

    private CompletableFuture<String> readAsync(InputStream stream) {
        return CompletableFuture.supplyAsync(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                return reader.lines().reduce("", (left, right) -> left + right + System.lineSeparator());
            } catch (IOException exception) {
                throw new PredictionEngineException("Could not read upcoming fight predictions", exception);
            }
        });
    }

    private String cleanEngineError(String error) {
        int index = error.lastIndexOf("error: ");
        return index >= 0 ? error.substring(index + 7).trim() : error;
    }
}
