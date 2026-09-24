package com.smoo1.ufcprediction.api;

import com.smoo1.ufcprediction.service.UpcomingFightService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import tools.jackson.databind.JsonNode;

@RestController
@RequestMapping("/api/upcoming")
public class UpcomingFightController {

    private final UpcomingFightService upcomingFightService;

    public UpcomingFightController(UpcomingFightService upcomingFightService) {
        this.upcomingFightService = upcomingFightService;
    }

    @GetMapping
    public ResponseEntity<JsonNode> upcoming() {
        return ResponseEntity.ok(upcomingFightService.upcoming());
    }
}
