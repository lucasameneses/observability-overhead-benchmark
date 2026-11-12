package ufc.mdcc.ads.trab1.tspaymentservice.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
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
@Table(name = "payments")
public class Payment {

    @Id
    private String id;

    @Column(name = "order_id", length = 36)
    private String orderId;

    @Column(name = "user_id", length = 36)
    private String userId;

    @Column(name = "payment_price")
    private String price;
}