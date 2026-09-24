package com.smoo1.ufcprediction.service;

import com.smoo1.ufcprediction.api.PredictionRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

@Service
public class PredictionService {

    private static final Duration TIMEOUT = Duration.ofSeconds(60);

    private final ObjectMapper objectMapper;
    private final Path projectRoot;
    private final String configuredPython;

    public PredictionService(
            ObjectMapper objectMapper,
            @Value("${ufc.python.project-root:.}") String projectRoot,
            @Value("${ufc.python.executable:}") String configuredPython
    ) {
        this.objectMapper = objectMapper;
        this.projectRoot = Path.of(projectRoot).toAbsolutePath().normalize();
        this.configuredPython = configuredPython == null ? "" : configuredPython.trim();
    }

    public JsonNode predict(PredictionRequest request) {
        Path script = projectRoot.resolve("regression.py");
        if (!Files.isRegularFile(script)) {
            throw new PredictionEngineException("Prediction engine is not configured on this server");
        }

        List<String> command = new ArrayList<>();
        command.add(resolvePython());
        command.add(script.toString());
        command.add(request.fighter1().trim());
        command.add(request.fighter2().trim());
        command.add("--date");
        command.add(LocalDate.now().toString());
        command.add("--rounds");
        command.add("3");
        command.add("--json");

        try {
            Process process = new ProcessBuilder(command)
                    .directory(projectRoot.toFile())
                    .start();
            CompletableFuture<String> stdout = readAsync(process.getInputStream());
            CompletableFuture<String> stderr = readAsync(process.getErrorStream());

            boolean finished = process.waitFor(TIMEOUT.toSeconds(), TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new PredictionEngineException("The prediction timed out. Please try again.");
            }

            String output = stdout.join().trim();
            String error = stderr.join().trim();
            if (process.exitValue() != 0) {
                String message = cleanEngineError(error.isBlank() ? output : error);
                if (message.contains("No UFCStats fighter found") || message.contains("Enter a full fighter name")) {
                    throw new FighterNotFoundException(message);
                }
                throw new PredictionEngineException(message);
            }
            return objectMapper.readTree(output);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new PredictionEngineException("The prediction was interrupted", exception);
        } catch (IOException exception) {
            throw new PredictionEngineException("Could not start the prediction engine", exception);
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
                throw new PredictionEngineException("Could not read the prediction response", exception);
            }
        });
    }

    private String cleanEngineError(String error) {
        String marker = "error: ";
        int index = error.lastIndexOf(marker);
        if (index >= 0) {
            return error.substring(index + marker.length()).trim();
        }
        return error.isBlank() ? "The prediction engine returned no result" : error;
    }
}
