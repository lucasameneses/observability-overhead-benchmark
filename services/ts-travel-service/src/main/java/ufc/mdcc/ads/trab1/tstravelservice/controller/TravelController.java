package ufc.mdcc.ads.trab1.tstravelservice.controller;

import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import ufc.mdcc.ads.trab1.tstravelservice.model.Trip;
import ufc.mdcc.ads.trab1.tstravelservice.model.TripId;
import ufc.mdcc.ads.trab1.tstravelservice.model.TravelResult;
import ufc.mdcc.ads.trab1.tstravelservice.service.TravelService;

@RestController
@RequestMapping("/api/v1/travelservice")
public class TravelController {

    private final TravelService travelService;

    public TravelController(TravelService travelService) {
        this.travelService = travelService;
    }

    @GetMapping("/travel")
    public ResponseEntity<Map<String, Object>> getTravel() {
        List<Trip> trips = travelService.getAllTrips();
        return ResponseEntity.ok(Map.of("trips", trips));
    }

    @GetMapping("/trips")
    public ResponseEntity<List<Trip>> getAllTrips() {
        return ResponseEntity.ok(travelService.getAllTrips());
    }

    @PostMapping("/trips/left")
    public ResponseEntity<TravelResult> getTravelResult(@RequestBody TripId tripId) {
        return ResponseEntity.ok(travelService.getTravelResult(tripId));
    }

    @PostMapping("/trips")
    public ResponseEntity<Trip> createTrip(@RequestBody Trip trip) {
        return ResponseEntity.ok(travelService.createTrip(trip));
    }

    @GetMapping("/welcome")
    public ResponseEntity<String> welcome() {
        return ResponseEntity.ok("Welcome to ts-travel-service");
    }
}