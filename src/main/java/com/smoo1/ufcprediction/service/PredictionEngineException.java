package com.smoo1.ufcprediction.service;

public class PredictionEngineException extends RuntimeException {
    public PredictionEngineException(String message) {
        super(message);
    }

    public PredictionEngineException(String message, Throwable cause) {
        super(message, cause);
    }
}
