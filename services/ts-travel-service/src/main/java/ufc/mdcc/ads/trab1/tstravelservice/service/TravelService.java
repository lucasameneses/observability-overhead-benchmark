package ufc.mdcc.ads.trab1.tstravelservice.service;

import java.util.List;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import ufc.mdcc.ads.trab1.tstravelservice.model.Trip;
import ufc.mdcc.ads.trab1.tstravelservice.model.TripId;
import ufc.mdcc.ads.trab1.tstravelservice.model.TravelResult;
import ufc.mdcc.ads.trab1.tstravelservice.repository.TripRepository;

@Service
@RequiredArgsConstructor
@Slf4j
public class TravelService {

    private final TripRepository tripRepository;

    @Cacheable(value = "trips", key = "'allTrips'")
    public List<Trip> getAllTrips() {
        log.info("TravelService: fetching all trips from database (cache miss)");
        return tripRepository.findAll();
    }

    @Cacheable(value = "trips", key = "#tripId.trainTypeName + ':' + #tripId.tripId")
    public TravelResult getTravelResult(TripId tripId) {
        log.info("TravelService: fetching travel result for trip {} (cache miss)", tripId);
        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new RuntimeException("Trip not found: " + tripId));

        return TravelResult.builder()
                .trip(trip)
                .startPlace(trip.getStartStationName())
                .endPlace(trip.getTerminalStationName())
                .departureTime(trip.getStartTime())
                .price("250.00")
                .build();
    }

    @CacheEvict(value = "trips", allEntries = true)
    public Trip createTrip(Trip trip) {
        log.info("TravelService: creating trip {}", trip.getId());
        return tripRepository.save(trip);
    }
}