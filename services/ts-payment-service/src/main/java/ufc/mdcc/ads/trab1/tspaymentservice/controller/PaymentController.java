package ufc.mdcc.ads.trab1.tspaymentservice.controller;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import ufc.mdcc.ads.trab1.tspaymentservice.model.Payment;
import ufc.mdcc.ads.trab1.tspaymentservice.service.PaymentService;

@RestController
@RequestMapping("/api/v1/paymentservice")
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @GetMapping("/payment")
    public ResponseEntity<Map<String, Object>> getPayment() {
        return ResponseEntity.ok(paymentService.getPaymentWithTravel());
    }

    @PostMapping("/payment")
    public ResponseEntity<Payment> createPayment(@RequestBody Payment payment) {
        return ResponseEntity.ok(paymentService.createPayment(payment));
    }

    @GetMapping("/welcome")
    public ResponseEntity<String> welcome() {
        return ResponseEntity.ok("Welcome to ts-payment-service");
    }
}