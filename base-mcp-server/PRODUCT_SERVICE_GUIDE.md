# Product Service MCP Tools Guide

This guide explains how to use the Product Service tools exposed through the MCP server.

## Prerequisites

1. Ensure your Product Service is running at `http://localhost:8083`
2. If using a different URL, set the `PRODUCT_SERVICE_URL` environment variable in your `.env` file

## Available Tools

### 1. create_product

Creates a new product in the product service.

#### Minimal Example

```json
{
  "productId": "PROD-001",
  "description": "Basic Product",
  "productType": "DIGITAL"
}
```

#### Complete Example

```json
{
  "productId": "PROD-002",
  "description": "Premium Digital Course",
  "productType": "DIGITAL",
  "materialNumber": "MAT-12345",
  "startDate": "2026-01-01",
  "endDate": "2026-12-31",
  "contents": [
    {
      "contentId": "CONT-001",
      "contentType": "VIDEO",
      "contentUrl": "https://example.com/video1.mp4",
      "description": "Introduction to Advanced Topics",
      "order": 1
    },
    {
      "contentId": "CONT-002",
      "contentType": "PDF",
      "contentUrl": "https://example.com/workbook.pdf",
      "description": "Course Workbook",
      "order": 2
    }
  ],
  "metadata": {
    "category": "education",
    "level": "advanced",
    "language": "en",
    "duration": "30 hours"
  },
  "priority": "HIGH",
  "processed": false
}
```

#### Product Types

The `productType` field must be one of:
- `PHYSICAL` - Physical products that require shipping
- `DIGITAL` - Digital products delivered electronically
- `SUBSCRIPTION` - Subscription-based products with recurring access

#### Response

On success (HTTP 201):
```json
{
  "success": true,
  "status_code": 201,
  "data": {
    "productId": "PROD-002",
    "materialNumber": "MAT-12345",
    "description": "Premium Digital Course",
    "productType": "DIGITAL",
    "startDate": "2026-01-01",
    "endDate": "2026-12-31",
    "contents": [...],
    "metadata": {...},
    "priority": "HIGH",
    "processed": false,
    "createdAt": "2026-01-26 10:30:00",
    "updatedAt": "2026-01-26 10:30:00"
  }
}
```

On error:
```json
{
  "success": false,
  "status_code": 400,
  "error": "Error message details"
}
```

### 2. get_product

Retrieves a product by its product ID.

#### Example

```json
{
  "productId": "PROD-001"
}
```

#### Response

On success (HTTP 200):
```json
{
  "success": true,
  "status_code": 200,
  "data": {
    "productId": "PROD-001",
    "description": "Basic Product",
    "productType": "DIGITAL",
    "createdAt": "2026-01-26 09:15:30",
    "updatedAt": "2026-01-26 09:15:30"
  }
}
```

On product not found (HTTP 404):
```json
{
  "success": false,
  "status_code": 404,
  "error": "Product with ID 'PROD-999' not found"
}
```

## Testing the Tools

### Using Cursor Chat

You can test these tools directly in Cursor by asking the AI assistant:

1. **Create a product:**
   ```
   Create a new product with ID "TEST-001", description "Test Product", and type "DIGITAL"
   ```

2. **Get a product:**
   ```
   Get the product with ID "TEST-001"
   ```

3. **Create a complex product:**
   ```
   Create a subscription product with ID "SUB-001", description "Monthly Newsletter", 
   type "SUBSCRIPTION", start date "2026-02-01", end date "2027-02-01", and metadata 
   with key "frequency" set to "monthly"
   ```

### Using HTTP Directly

If you want to test the Product Service API directly (without MCP):

```bash
# Create a product
curl -X POST http://localhost:8083/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "PROD-001",
    "description": "Test Product",
    "productType": "DIGITAL"
  }'

# Get a product
curl http://localhost:8083/api/products/PROD-001
```

## Error Handling

The tools handle various error scenarios:

1. **Invalid Product Type:**
   - Returns error message listing valid types: PHYSICAL, DIGITAL, SUBSCRIPTION

2. **Product Not Found:**
   - Returns 404 status with clear error message

3. **Validation Errors:**
   - Returns 400 status with validation error details from the service

4. **Service Unavailable:**
   - Returns connection error if the product service is not running

5. **Duplicate Product:**
   - Returns 409 status if a product with the same ID already exists

## Date Format

All dates should be in the format: `yyyy-MM-dd`

Examples:
- `2026-01-26`
- `2026-12-31`
- `2025-03-15`

## Best Practices

1. **Unique Product IDs:** Always use unique product IDs to avoid conflicts
2. **Descriptive Names:** Use clear, descriptive product descriptions
3. **Proper Types:** Choose the appropriate product type for your use case
4. **Date Validation:** Ensure end dates are after start dates
5. **Content Ordering:** Use the `order` field in contents to maintain proper sequence
6. **Metadata:** Use metadata for flexible, extensible product properties

## Troubleshooting

### Product Service Not Running

If you get connection errors:
```json
{
  "success": false,
  "error": "Connection refused..."
}
```

**Solution:** Start the product service:
```bash
cd product-service
mvn spring-boot:run
```

### Invalid Environment Variable

If the service URL is incorrect, update your `.env` file:
```env
PRODUCT_SERVICE_URL=http://localhost:8083
```

Then restart the MCP server.

## Integration with Other Tools

The product service tools can be combined with database queries for comprehensive analysis:

```
Query the database for all orders, then create products for any missing product IDs
```

This enables powerful workflows that leverage both the database and the product service.


