package ufc.mdcc.ads.trab1.tspaymentservice.service;

import java.util.List;
import java.util.Map;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import ufc.mdcc.ads.trab1.tspaymentservice.model.Payment;
import ufc.mdcc.ads.trab1.tspaymentservice.repository.PaymentRepository;

@Service
@Slf4j
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final RestTemplate restTemplate;
    private final String travelServiceUrl;

    public PaymentService(PaymentRepository paymentRepository, RestTemplate restTemplate,
                          @Value("${travel-service.url}") String travelServiceUrl) {
        this.paymentRepository = paymentRepository;
        this.restTemplate = restTemplate;
        this.travelServiceUrl = travelServiceUrl;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getPaymentWithTravel() {
        log.info("PaymentService: fetching payment with travel info");
        Map<String, Object> travelResult = restTemplate.getForObject(
                travelServiceUrl + "/api/v1/travelservice/travel", Map.class);
        List<Payment> payments = paymentRepository.findAll();

        return Map.of(
            "payments", payments,
            "travel", travelResult != null ? travelResult : Map.of()
        );
    }

    public Payment createPayment(Payment payment) {
        log.info("PaymentService: creating payment for order {}", payment.getOrderId());
        payment.setId(java.util.UUID.randomUUID().toString());
        Payment saved = paymentRepository.save(payment);

        Map<String, Object> travelResult = restTemplate.getForObject(
                travelServiceUrl + "/api/v1/travelservice/travel", Map.class);
        log.info("PaymentService: travel result for payment {} = {}", saved.getId(), travelResult);

        return saved;
    }
}