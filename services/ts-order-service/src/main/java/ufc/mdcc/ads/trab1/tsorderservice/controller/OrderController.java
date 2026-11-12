package ufc.mdcc.ads.trab1.tsorderservice.controller;

import java.util.Map;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import ufc.mdcc.ads.trab1.tsorderservice.model.Order;
import ufc.mdcc.ads.trab1.tsorderservice.service.OrderService;

@RestController
@RequestMapping("/api/v1/orderservice")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/order")
    public ResponseEntity<Map<String, Object>> getOrder() {
        return ResponseEntity.ok(orderService.getOrderWithPayment());
    }

    @PostMapping("/order")
    public ResponseEntity<Order> createOrder(@RequestBody Order order) {
        return ResponseEntity.ok(orderService.createOrder(order));
    }

    @GetMapping("/welcome")
    public ResponseEntity<String> welcome() {
        return ResponseEntity.ok("Welcome to ts-order-service");
    }
}