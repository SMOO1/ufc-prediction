package com.smoo1.ufcprediction.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record PredictionRequest(
        @NotBlank(message = "Enter the first fighter's full name")
        @Size(max = 100, message = "Fighter names must be under 100 characters")
        @Pattern(regexp = "[\\p{L}\\p{N}_ .'’-]+", message = "The first fighter name contains unsupported characters")
        String fighter1,

        @NotBlank(message = "Enter the second fighter's full name")
        @Size(max = 100, message = "Fighter names must be under 100 characters")
        @Pattern(regexp = "[\\p{L}\\p{N}_ .'’-]+", message = "The second fighter name contains unsupported characters")
        String fighter2,

        @NotNull(message = "Select a fight date")
        LocalDate date,

        @NotNull(message = "Select three or five rounds")
        Integer rounds,

        boolean titleBout,
        boolean womensBout
) {
}
