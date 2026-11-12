package ufc.mdcc.ads.trab1.tspaymentservice.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import ufc.mdcc.ads.trab1.tspaymentservice.model.Payment;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, String> {
}