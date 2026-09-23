package com.smoo1.ufcprediction.api;

import com.smoo1.ufcprediction.service.PredictionService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import tools.jackson.databind.JsonNode;

import java.text.Normalizer;
import java.util.Locale;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @PostMapping
    public ResponseEntity<JsonNode> predict(@Valid @RequestBody PredictionRequest request) {
        if (request.rounds() != 3 && request.rounds() != 5) {
            throw new IllegalArgumentException("Rounds must be either 3 or 5");
        }
        if (canonicalName(request.fighter1()).equals(canonicalName(request.fighter2()))) {
            throw new IllegalArgumentException("Choose two different fighters");
        }
        return ResponseEntity.ok(predictionService.predict(request));
    }

    private String canonicalName(String name) {
        return Normalizer.normalize(name, Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "")
                .replace('_', ' ')
                .replaceAll("[^\\p{Alnum}\\s]", "")
                .replaceAll("\\s+", " ")
                .trim()
                .toLowerCase(Locale.ROOT);
    }
}
