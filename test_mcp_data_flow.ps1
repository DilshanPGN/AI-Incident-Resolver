# Test script to verify MCP server receives data from order-service and payment-service
# This script invokes APIs and checks if telemetry data is received

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing MCP Server Data Reception" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test order-service
Write-Host "Testing order-service..." -ForegroundColor Yellow
Write-Host "1. Creating an order..." -ForegroundColor Gray
try {
    $orderResponse = Invoke-RestMethod -Uri "http://localhost:8080/orders" -Method POST -ContentType "application/json" -Body '{"productName":"Test Product","quantity":2,"price":29}'
    Write-Host "   ✓ Order created: ID=$($orderResponse.id)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to create order: $_" -ForegroundColor Red
}

Write-Host "2. Getting all orders..." -ForegroundColor Gray
try {
    $orders = Invoke-RestMethod -Uri "http://localhost:8080/orders" -Method GET
    Write-Host "   ✓ Retrieved $($orders.Count) orders" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to get orders: $_" -ForegroundColor Red
}

Write-Host "3. Getting order by ID..." -ForegroundColor Gray
try {
    $order = Invoke-RestMethod -Uri "http://localhost:8080/orders/1" -Method GET
    Write-Host "   ✓ Retrieved order ID=$($order.id)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to get order: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing payment-service..." -ForegroundColor Yellow
Write-Host "1. Creating a payment..." -ForegroundColor Gray
try {
    $paymentResponse = Invoke-RestMethod -Uri "http://localhost:8081/api/payments" -Method POST -ContentType "application/json" -Body '{"amount":59.98,"currency":"USD","paymentMethod":"credit_card","description":"Test payment"}'
    Write-Host "   ✓ Payment created: ID=$($paymentResponse.id)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to create payment: $_" -ForegroundColor Red
}

Write-Host "2. Getting all payments..." -ForegroundColor Gray
try {
    $payments = Invoke-RestMethod -Uri "http://localhost:8081/api/payments" -Method GET
    Write-Host "   ✓ Retrieved $($payments.Count) payments" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to get payments: $_" -ForegroundColor Red
}

Write-Host "3. Processing payment..." -ForegroundColor Gray
try {
    $payment = Invoke-RestMethod -Uri "http://localhost:8081/api/payments/1/process" -Method POST
    Write-Host "   ✓ Payment processed: ID=$($payment.id)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to process payment: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Check the debug log at: .cursor\debug.log" -ForegroundColor Gray
Write-Host "2. Use MCP tools to query telemetry data:" -ForegroundColor Gray
Write-Host "   - get_recent_traces" -ForegroundColor Gray
Write-Host "   - get_recent_logs" -ForegroundColor Gray
Write-Host "   - get_recent_metrics" -ForegroundColor Gray
Write-Host "   - get_service_health" -ForegroundColor Gray
