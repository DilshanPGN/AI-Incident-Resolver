package com.example.order;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class OrderService {

    private final List<Order> orders = new ArrayList<>();
    private final AtomicLong idGenerator = new AtomicLong(1);

    public Order createOrder(OrderRequest request) {
        Order order = new Order(
                idGenerator.getAndIncrement(),
                request.getProductName(),
                request.getQuantity(),
                request.getPrice(),
                "PENDING"
        );
        orders.add(order);
        return order;
    }

    public List<Order> getAllOrders() {
        return new ArrayList<>(orders);
    }

    public Optional<Order> getOrderById(Long id) {
        return orders.stream()
                .filter(order -> order.getId().equals(id))
                .findFirst();
    }

    public Optional<Order> updateOrder(Long id, OrderRequest request) {
        return getOrderById(id).map(order -> {
            order.setProductName(request.getProductName());
            order.setQuantity(request.getQuantity());
            order.setPrice(request.getPrice());
            return order;
        });
    }

    public boolean deleteOrder(Long id) {
        return orders.removeIf(order -> order.getId().equals(id));
    }
}
