package ufc.mdcc.ads.trab1.tstravelservice.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import ufc.mdcc.ads.trab1.tstravelservice.model.Trip;
import ufc.mdcc.ads.trab1.tstravelservice.model.TripId;

@Repository
public interface TripRepository extends JpaRepository<Trip, TripId> {
}