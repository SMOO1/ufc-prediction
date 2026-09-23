package com.smoo1.ufcprediction.service;

public class FighterNotFoundException extends RuntimeException {
    public FighterNotFoundException(String message) {
        super(message);
    }
}
