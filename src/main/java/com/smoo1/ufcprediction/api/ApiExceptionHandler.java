package com.smoo1.ufcprediction.api;

import com.smoo1.ufcprediction.service.FighterNotFoundException;
import com.smoo1.ufcprediction.service.PredictionEngineException;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ApiError> invalidRequest(MethodArgumentNotValidException exception) {
        String message = exception.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(error -> error.getDefaultMessage())
                .orElse("Check the submitted values");
        return ResponseEntity.badRequest().body(ApiError.of(400, "Invalid request", message));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<ApiError> invalidArgument(IllegalArgumentException exception) {
        return ResponseEntity.badRequest().body(ApiError.of(400, "Invalid request", exception.getMessage()));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<ApiError> unreadableRequest() {
        return ResponseEntity.badRequest()
                .body(ApiError.of(400, "Invalid request", "Check the fight date and submitted values"));
    }

    @ExceptionHandler(FighterNotFoundException.class)
    ResponseEntity<ApiError> fighterNotFound(FighterNotFoundException exception) {
        return ResponseEntity.status(HttpStatusCode.valueOf(422))
                .body(ApiError.of(422, "Fighter not found", exception.getMessage()));
    }

    @ExceptionHandler(PredictionEngineException.class)
    ResponseEntity<ApiError> predictionFailure(PredictionEngineException exception) {
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
                .body(ApiError.of(502, "Prediction unavailable", exception.getMessage()));
    }
}
