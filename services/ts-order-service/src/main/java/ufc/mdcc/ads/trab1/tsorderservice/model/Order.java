package ufc.mdcc.ads.trab1.tsorderservice.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
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
@Table(name = "orders")
public class Order {

    @Id
    private String id;

    @Column(name = "bought_date")
    private String boughtDate;

    @Column(name = "travel_date")
    private String travelDate;

    @Column(name = "travel_time")
    private String travelTime;

    @Column(name = "account_id")
    private String accountId;

    @Column(name = "contacts_name")
    private String contactsName;

    @Column(name = "document_type")
    private Integer documentType;

    @Column(name = "train_number")
    private String trainNumber;

    @Column(name = "coach_number")
    private Integer coachNumber;

    @Enumerated(EnumType.ORDINAL)
    @Column(name = "seat_class")
    private SeatClass seatClass;

    @Column(name = "seat_number")
    private String seatNumber;

    @Column(name = "from_station")
    private String fromStation;

    @Column(name = "to_station")
    private String toStation;

    @Enumerated(EnumType.ORDINAL)
    private OrderStatus status;

    private String price;

    public enum SeatClass {
        NONE, BUSINESS, FIRSTCLASS, SECONDCLASS
    }

    public enum OrderStatus {
        NOTPAID, PAID, CHANGE, CANCEL
    }
}