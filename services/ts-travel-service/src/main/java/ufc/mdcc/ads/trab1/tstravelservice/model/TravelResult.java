package ufc.mdcc.ads.trab1.tstravelservice.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TravelResult {

    private Trip trip;
    private String startPlace;
    private String endPlace;
    private String departureTime;
    private String price;
}