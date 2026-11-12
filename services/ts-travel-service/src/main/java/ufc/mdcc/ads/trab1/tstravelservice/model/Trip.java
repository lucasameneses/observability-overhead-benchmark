package ufc.mdcc.ads.trab1.tstravelservice.model;

import jakarta.persistence.Column;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "trips")
public class Trip {

    @EmbeddedId
    private TripId id;

    @Column(name = "route_id")
    private String routeId;

    @Column(name = "start_station_name")
    private String startStationName;

    @Column(name = "stations_name")
    private String stationsName;

    @Column(name = "terminal_station_name")
    private String terminalStationName;

    @Column(name = "start_time")
    private String startTime;

    @Column(name = "end_time")
    private String endTime;
}