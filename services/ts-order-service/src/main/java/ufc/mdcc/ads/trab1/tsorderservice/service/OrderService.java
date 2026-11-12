package ufc.mdcc.ads.trab1.tsorderservice.service;

import java.util.List;
import java.util.Map;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import ufc.mdcc.ads.trab1.tsorderservice.model.Order;
import ufc.mdcc.ads.trab1.tsorderservice.model.Order.OrderStatus;
import ufc.mdcc.ads.trab1.tsorderservice.repository.OrderRepository;

@Service
@Slf4j
public class OrderService {

    private final OrderRepository orderRepository;
    private final RestTemplate restTemplate;
    private final String paymentServiceUrl;

    public OrderService(OrderRepository orderRepository, RestTemplate restTemplate,
                        @Value("${payment-service.url}") String paymentServiceUrl) {
        this.orderRepository = orderRepository;
        this.restTemplate = restTemplate;
        this.paymentServiceUrl = paymentServiceUrl;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getOrderWithPayment() {
        log.info("OrderService: fetching order with payment info");
        Map<String, Object> paymentResult = restTemplate.getForObject(
                paymentServiceUrl + "/api/v1/paymentservice/payment", Map.class);
        List<Order> orders = orderRepository.findAll();

        return Map.of(
            "orders", orders,
            "payment", paymentResult != null ? paymentResult : Map.of()
        );
    }

    public Order createOrder(Order order) {
        log.info("OrderService: creating order for account {}", order.getAccountId());
        order.setId(java.util.UUID.randomUUID().toString());
        order.setStatus(OrderStatus.NOTPAID);
        Order saved = orderRepository.save(order);

        Map<String, Object> paymentResult = restTemplate.getForObject(
                paymentServiceUrl + "/api/v1/paymentservice/payment", Map.class);
        log.info("OrderService: payment result for order {} = {}", saved.getId(), paymentResult);

        return saved;
    }
}