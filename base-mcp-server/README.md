# Base MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to entitlement/institution APIs, database queries, and product/order service operations.

## Overview

This MCP server exposes 12 powerful tools for interacting with external APIs and services:

- **API Tools** (2 tools) - Search entitlements and institutions
- **Database Query Tools** (3 tools) - Execute SQL queries on the order management database
- **Product Service Tools** (2 tools) - Create and retrieve products from the product microservice
- **Order Service Tools** (5 tools) - Full CRUD operations for orders from the order microservice

## Directory Structure

```
base-mcp-server/
├── entitlement-stdio.py        # Main MCP server (stdio transport for Cursor)
├── entitlement-sse.py          # Alternative MCP server (SSE transport)
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Python dependencies
├── env.example                 # Environment variable template
├── test_product_tools.py       # Test script for product service integration
├── SETUP.md                    # Detailed setup instructions
├── CHANGES.md                  # Changelog of recent updates
└── README.md                   # This file
```

## Quick Start

### 1. Install Dependencies

```powershell
cd base-mcp-server
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in this directory:

```env
# API Configuration (OAuth)
WILEY_TOKEN_URL=https://your-oauth-endpoint/token
WILEY_CLIENT_ID=your_client_id
WILEY_CLIENT_SECRET=your_client_secret
WILEY_ALM_BASE_URL=https://your-api-base-url

# Database Configuration
DB_HOST=your-database-host
DB_PORT=3306
DB_NAME=order_management
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Product Service Configuration
PRODUCT_SERVICE_URL=http://localhost:8083

# Order Service Configuration
ORDER_SERVICE_URL=http://localhost:8081
```

See `env.example` for a template.

### 3. Configure Cursor MCP

Update your Cursor MCP configuration (`~/.cursor/mcp.json` or `C:\Users\{username}\.cursor\mcp.json`):

```json
{
  "mcpServers": {
    "base-mcp-server": {
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\AI-Incident-Resolver\\base-mcp-server\\entitlement-stdio.py"
      ],
      "env": {
        "WILEY_TOKEN_URL": "https://your-oauth-endpoint/token",
        "WILEY_CLIENT_ID": "your-client-id",
        "WILEY_CLIENT_SECRET": "your-secret",
        "WILEY_ALM_BASE_URL": "https://your-api-base-url",
        "DB_HOST": "your-database-host",
        "DB_PORT": "3306",
        "DB_NAME": "order_management",
        "DB_USER": "your_db_user",
        "DB_PASSWORD": "your_db_password",
        "PRODUCT_SERVICE_URL": "http://localhost:8083",
        "ORDER_SERVICE_URL": "http://localhost:8081"
      }
    }
  }
}
```

**Note:** You can use either `.env` file or environment variables in `mcp.json`. Environment variables in `mcp.json` take precedence.

### 4. Run the MCP Server

```powershell
python entitlement-stdio.py
```

For Cursor integration, the server will start automatically when Cursor launches.

## Available Tools

### 1. API Tools (Entitlements & Institutions)

#### `search_license_entitlements`
Search for license entitlements with various filters.

**Parameters:**
- `licenseId` (string, optional) - License ID
- `entitledToId` (string, optional) - Entitled to ID
- `entitlementStartDate` (string, optional) - Start date filter
- `entitlementEndDate` (string, optional) - End date filter
- `contentStartDate` (string, optional) - Content start date filter
- `contentEndDate` (string, optional) - Content end date filter
- `entitlementType` (string, optional) - Type of entitlement
- `orderNumber` (string, optional) - Order number
- `orderLineItemId` (string, optional) - Order line item ID
- `status` (string, optional) - Status filter
- `assetId` (string, optional) - Asset ID
- `limit` (integer, default: 100) - Maximum results per page
- `page` (integer, default: 0) - Page number

**Example:**
```
Search for entitlements with license ID "LIC-12345"
```

**Returns:**
- List of entitlements matching the search criteria

#### `search_institutions`
Search for institutions by ID, name, or other criteria.

**Parameters:**
- `institutionId` (string, optional) - Institution ID
- `bpId` (string, optional) - Business partner ID
- `institutionName` (string, optional) - Institution name (partial match)
- `wintouchId` (string, optional) - WinTouch ID
- `institutionType` (string, optional) - Type of institution
- `status` (string, optional) - Status filter
- `ipAddress` (string, optional) - IP address
- `derivedExternalId` (string, optional) - Derived external ID
- `adminEmail` (string, optional) - Admin email
- `institutionLoginId` (string, optional) - Institution login ID
- `limit` (integer, default: 100) - Maximum results per page
- `offset` (integer, default: 0) - Offset for pagination

**Example:**
```
Find institutions with name containing "University"
```

**Returns:**
- List of institutions matching the search criteria

### 2. Database Query Tools

#### `query_database`
Execute SELECT queries on the order_management database.

**Parameters:**
- `sql_query` (string, required) - The SQL SELECT query to execute
- `limit` (integer, default: 100, max: 1000) - Maximum number of rows to return

**Security Features:**
- Only SELECT queries allowed
- Blocks dangerous keywords: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE
- Automatic LIMIT enforcement (max 1000 rows)
- Query validation before execution

**Example:**
```
Query the database: SELECT * FROM products WHERE product_type = 'DIGITAL' LIMIT 10
```

**Returns:**
- Query results as list of dictionaries
- Row count
- Success status and error message (if failed)

#### `list_database_tables`
List all available tables in the database.

**Parameters:** None

**Example:**
```
Show me all tables in the database
```

**Returns:**
- List of tables with:
  - Table name
  - Row count
  - Create time
  - Update time
  - Table comment

#### `describe_table`
Get detailed schema information and sample data for a specific table.

**Parameters:**
- `table_name` (string, required) - Name of the table to describe

**Example:**
```
Describe the products table
```

**Returns:**
- Table schema with:
  - Column names
  - Data types
  - Nullable status
  - Keys (PRIMARY, FOREIGN, UNIQUE)
  - Default values
  - Column comments
- Sample data (5 rows)

### 3. Product Service Tools

#### `create_product`
Create a new product in the product service.

**Parameters:**
- `productId` (string, required) - Unique product identifier
- `description` (string, required) - Product description
- `productType` (string, required) - Must be one of: PHYSICAL, DIGITAL, SUBSCRIPTION
- `materialNumber` (string, optional) - Material number
- `startDate` (string, optional) - Start date in format yyyy-MM-dd
- `endDate` (string, optional) - End date in format yyyy-MM-dd
- `contents` (list, optional) - List of content objects with:
  - `contentId` (string)
  - `contentType` (string)
  - `contentUrl` (string)
  - `description` (string)
  - `order` (integer)
- `metadata` (dict, optional) - Additional metadata as key-value pairs
- `priority` (string, optional) - Priority level
- `processed` (boolean, default: false) - Whether the product has been processed

**Example:**
```
Create a product with ID "PROD-001", description "Test Product", and type "DIGITAL"
```

**Returns:**
- Created product object with all fields
- Success status and HTTP status code

#### `get_product`
Retrieve a product by its ID.

**Parameters:**
- `productId` (string, required) - The unique product identifier

**Example:**
```
Get product with ID "PROD-001"
```

**Returns:**
- Product object with all fields
- Success status and HTTP status code

### 4. Order Service Tools

#### `create_order`
Create a new order in the order service.

**Parameters:**
- `productName` (string, required) - Name of the product being ordered
- `quantity` (integer, required) - Quantity of the product
- `price` (integer, required) - Price of the product (in cents or smallest currency unit)

**Example:**
```
Create an order for product "Laptop" with quantity 2 and price 1000
```

**Returns:**
- Created order object with:
  - Order ID
  - Product name
  - Quantity
  - Price
  - Timestamp
- Success status and HTTP status code

#### `get_all_orders`
Retrieve all orders from the order service.

**Parameters:** None

**Example:**
```
Get all orders
```

**Returns:**
- List of all orders with full details

#### `get_order_by_id`
Retrieve an order by its ID.

**Parameters:**
- `orderId` (integer, required) - The unique order identifier

**Example:**
```
Get order with ID 1
```

**Returns:**
- Order object with full details
- Success status and HTTP status code

#### `update_order`
Update an existing order.

**Parameters:**
- `orderId` (integer, required) - The unique order identifier
- `productName` (string, required) - Updated product name
- `quantity` (integer, required) - Updated quantity
- `price` (integer, required) - Updated price (in cents or smallest currency unit)

**Example:**
```
Update order 1 with product name "Desktop", quantity 1, and price 1500
```

**Returns:**
- Updated order object with all fields
- Success status and HTTP status code

#### `delete_order`
Delete an order by its ID.

**Parameters:**
- `orderId` (integer, required) - The unique order identifier

**Example:**
```
Delete order with ID 1
```

**Returns:**
- Deletion status
- Success status and HTTP status code

## Testing

### Test Product Service Integration

```powershell
python test_product_tools.py
```

This will verify that:
- Product service is running and accessible
- Create product endpoint works
- Get product endpoint works

### Manual Testing with Cursor

Once configured, you can test the tools directly in Cursor chat:

**Database Queries:**
```
How many PHYSICAL products are in the database?
```

**Product Operations:**
```
Create a new digital product called "Test eBook" with ID "EBOOK-001"
```

```
Get the details of product PROD-020
```

**Order Operations:**
```
Create an order for product "Laptop" with quantity 2 and price 1000
```

```
Show me all orders
```

```
Update order 1 with product name "Desktop", quantity 1, and price 1500
```

## Documentation

- **SETUP.md** - Detailed setup and configuration guide
- **CHANGES.md** - Recent changes and updates
- **env.example** - Environment variable template

## Architecture

```
Cursor AI Client
    ↓ (stdio)
MCP Server (entitlement-stdio.py)
    ├── → Entitlement/Institution APIs (OAuth + REST)
    ├── → MySQL Database (order_management)
    ├── → Product Service (Spring Boot @ :8083)
    └── → Order Service (Spring Boot @ :8081)
```

## Features

### OAuth Token Management
- **Automatic Token Caching** - Tokens are cached and automatically refreshed
- **Token Expiry Handling** - Tokens are refreshed 5 minutes before expiry
- **Request Tracking** - Each API call includes `x-request-id` for tracing

### Database Security
- **Read-only Access** - Only SELECT queries allowed
- **Query Validation** - Blocks dangerous SQL keywords
- **Result Limiting** - Prevents large data dumps (max 1000 rows)
- **Automatic LIMIT** - Adds LIMIT clause if not present

### Error Handling
- **Comprehensive Error Messages** - Detailed error information for debugging
- **Type Validation** - Validates product types and other inputs
- **HTTP Status Codes** - Returns appropriate status codes for all operations

### Performance
- **Async Operations** - All I/O operations use async/await for performance
- **Connection Pooling** - Database connections are managed efficiently
- **Request Batching** - Multiple requests can be processed concurrently

## Requirements

- Python 3.10+
- Access to entitlement/institution APIs (OAuth credentials)
- MySQL database access (order_management database)
- Product Service running on localhost:8083 (optional, for product tools)
- Order Service running on localhost:8081 (optional, for order tools)

## Dependencies

- `fastmcp` - FastMCP framework for building MCP servers
- `httpx` - Async HTTP client for API calls
- `python-dotenv` - Environment variable management
- `mysql-connector-python` - MySQL database connectivity
- `mcp` - Model Context Protocol SDK

## Configuration

### Environment Variables

All configuration is done via environment variables. You can set them in:
1. `.env` file in the `base-mcp-server` directory
2. `mcp.json` environment variables (takes precedence)

**Required Variables:**
- `WILEY_TOKEN_URL` - OAuth token endpoint
- `WILEY_CLIENT_ID` - OAuth client ID
- `WILEY_CLIENT_SECRET` - OAuth client secret
- `WILEY_ALM_BASE_URL` - Base URL for the API

**Database Variables:**
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 3306)
- `DB_NAME` - Database name (default: order_management)
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password

**Service URLs:**
- `PRODUCT_SERVICE_URL` - Product service URL (default: http://localhost:8083)
- `ORDER_SERVICE_URL` - Order service URL (default: http://localhost:8081)

## Troubleshooting

### MCP Server Not Connecting

1. Check that the path in `mcp.json` is correct
2. Verify Python executable path is correct
3. Restart Cursor after updating configuration
4. Check Cursor's MCP server logs for errors

### Database Connection Failed

1. Verify DB credentials in `.env` or `mcp.json`
2. Check network access to database host
3. Ensure database user has appropriate permissions
4. Test connection manually:
   ```powershell
   mysql -h your-database-host -u your_user -p order_management
   ```

### API Authentication Issues

1. Verify `WILEY_CLIENT_ID` and `WILEY_CLIENT_SECRET` are correct
2. Check token URL is correct
3. Ensure API base URL is accessible
4. Check OAuth token response in logs

### Product Service Connection Failed

1. Start the product service: `cd product-service && mvn spring-boot:run`
2. Verify service is running at configured URL
3. Check `PRODUCT_SERVICE_URL` environment variable
4. Test service manually:
   ```powershell
   curl http://localhost:8083/api/products
   ```

### Order Service Connection Failed

1. Start the order service: `cd order-service && mvn spring-boot:run`
2. Verify service is running at configured URL (default: http://localhost:8081)
3. Check `ORDER_SERVICE_URL` environment variable
4. Test service manually:
   ```powershell
   curl http://localhost:8081/api/orders
   ```

### Module Not Found Errors

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Or install individually:
   ```powershell
   pip install fastmcp httpx python-dotenv mcp mysql-connector-python
   ```

3. Verify you're using the correct Python interpreter (the one Cursor uses)

### Query Validation Errors

If you get "Only SELECT queries are allowed":
- Ensure your query starts with `SELECT`
- Remove any dangerous keywords (DROP, DELETE, UPDATE, etc.)
- Use `query_database` tool, not direct SQL execution

## Security Best Practices

1. **Never commit `.env` files** - Add `.env` to `.gitignore`
2. **Use environment variables in `mcp.json`** - For production deployments
3. **Limit database permissions** - Database user should only have SELECT permissions
4. **Rotate OAuth credentials** - Regularly update client secrets
5. **Monitor API usage** - Track request IDs for auditing

## License

Internal Use Only

## Support

For questions or issues:
- Check the troubleshooting section above
- Review SETUP.md for detailed configuration
- Contact the development team
