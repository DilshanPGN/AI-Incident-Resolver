package com.example.payment;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class PaymentService {

    private final Map<Long, Payment> paymentStore = new ConcurrentHashMap<>();
    private final AtomicLong idGenerator = new AtomicLong(1);

    /**
     * Create a new payment
     */
    public Payment createPayment(PaymentRequest request) {
        Payment payment = new Payment();
        payment.setId(idGenerator.getAndIncrement());
        payment.setTransactionId(UUID.randomUUID().toString());
        payment.setAmount(request.getAmount());
        payment.setCurrency(request.getCurrency());
        payment.setPaymentMethod(request.getPaymentMethod());
        payment.setDescription(request.getDescription());
        payment.setStatus("PENDING");
        payment.setCreatedAt(LocalDateTime.now());
        payment.setUpdatedAt(LocalDateTime.now());

        paymentStore.put(payment.getId(), payment);
        return payment;
    }

    /**
     * Get all payments
     */
    public List<Payment> getAllPayments() {
        return new ArrayList<>(paymentStore.values());
    }

    /**
     * Get payment by ID
     */
    public Optional<Payment> getPaymentById(Long id) {
        return Optional.ofNullable(paymentStore.get(id));
    }

    /**
     * Update payment
     */
    public Optional<Payment> updatePayment(Long id, PaymentRequest request) {
        Payment existingPayment = paymentStore.get(id);
        if (existingPayment == null) {
            return Optional.empty();
        }

        existingPayment.setAmount(request.getAmount());
        existingPayment.setCurrency(request.getCurrency());
        existingPayment.setPaymentMethod(request.getPaymentMethod());
        existingPayment.setDescription(request.getDescription());
        existingPayment.setUpdatedAt(LocalDateTime.now());

        paymentStore.put(id, existingPayment);
        return Optional.of(existingPayment);
    }

    /**
     * Update payment status
     */
    public Optional<Payment> updatePaymentStatus(Long id, String status) {
        Payment existingPayment = paymentStore.get(id);
        if (existingPayment == null) {
            return Optional.empty();
        }

        existingPayment.setStatus(status);
        existingPayment.setUpdatedAt(LocalDateTime.now());

        paymentStore.put(id, existingPayment);
        return Optional.of(existingPayment);
    }

    /**
     * Delete payment
     */
    public boolean deletePayment(Long id) {
        return paymentStore.remove(id) != null;
    }

    /**
     * Process payment (simulate payment processing)
     */
    public Optional<Payment> processPayment(Long id) {
        Payment payment = paymentStore.get(id);
        if (payment == null) {
            return Optional.empty();
        }

        // Simulate payment processing
        payment.setStatus("COMPLETED");
        payment.setUpdatedAt(LocalDateTime.now());

        paymentStore.put(id, payment);
        return Optional.of(payment);
    }
}
