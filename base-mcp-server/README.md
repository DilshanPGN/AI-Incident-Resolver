# Wiley ALM Base MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Wiley ALM APIs, database queries, and product service operations.

## Overview

This MCP server exposes 7 powerful tools for interacting with Wiley's ALM ecosystem:

- **Wiley ALM API Tools** - Search entitlements and institutions
- **Database Query Tools** - Execute SQL queries on the order management database
- **Product Service Tools** - Create and retrieve products from the product microservice

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
├── PRODUCT_SERVICE_GUIDE.md    # Product service tools usage guide
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
# Wiley ALM API Configuration
WILEY_TOKEN_URL=https://your-oauth-endpoint/token
WILEY_CLIENT_ID=your_client_id
WILEY_CLIENT_SECRET=your_client_secret
WILEY_ALM_BASE_URL=https://your-alm-api-base-url

# Database Configuration
DB_HOST=alm-dev-db.alm.private.wiley.host
DB_PORT=3306
DB_NAME=order_management
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Product Service Configuration
PRODUCT_SERVICE_URL=http://localhost:8083
```

See `env.example` for a template.

### 3. Configure Cursor MCP

Update your Cursor MCP configuration (`~/.cursor/mcp.json` or `C:\Users\{username}\.cursor\mcp.json`):

```json
{
  "mcpServers": {
    "wiley-alm-server": {
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\AI-Incident-Resolver\\base-mcp-server\\entitlement-stdio.py"
      ],
      "env": {
        "WILEY_TOKEN_URL": "https://alm-external-sso-dev.alm.private.wiley.host/auth/realms/wiley/protocol/openid-connect/token",
        "WILEY_CLIENT_ID": "ALM-API",
        "WILEY_CLIENT_SECRET": "your-secret",
        "WILEY_ALM_BASE_URL": "https://almapi-dev.alm.private.wiley.host",
        "PRODUCT_SERVICE_URL": "http://localhost:8083"
      }
    }
  }
}
```

### 4. Run the MCP Server

```powershell
python entitlement-stdio.py
```

For Cursor integration, the server will start automatically when Cursor launches.

## Available Tools

### 1. Wiley ALM API Tools

#### `search_license_entitlements`
Search for license entitlements with various filters.

**Example:**
```
Search for entitlements with license ID "LIC-12345"
```

#### `search_institutions`
Search for institutions by ID, name, or other criteria.

**Example:**
```
Find institutions with name containing "University"
```

### 2. Database Query Tools

#### `query_database`
Execute SELECT queries on the order_management database.

**Example:**
```
Query the database: SELECT * FROM products WHERE product_type = 'DIGITAL'
```

#### `list_database_tables`
List all available tables in the database.

#### `describe_table`
Get schema information and sample data for a specific table.

**Example:**
```
Describe the products table
```

### 3. Product Service Tools

#### `create_product`
Create a new product in the product service.

**Example:**
```
Create a product with ID "PROD-001", description "Test Product", and type "DIGITAL"
```

#### `get_product`
Retrieve a product by its ID.

**Example:**
```
Get product with ID "PROD-001"
```

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

```
How many PHYSICAL products are in the database?
```

```
Create a new digital product called "Test eBook" with ID "EBOOK-001"
```

```
Get the details of product PROD-020
```

## Documentation

- **SETUP.md** - Detailed setup and configuration guide
- **PRODUCT_SERVICE_GUIDE.md** - Complete guide for product service tools
- **CHANGES.md** - Recent changes and updates

## Architecture

```
Cursor AI Client
    ↓ (stdio)
MCP Server (entitlement-stdio.py)
    ├── → Wiley ALM APIs (OAuth + REST)
    ├── → MySQL Database (order_management)
    └── → Product Service (Spring Boot @ :8083)
```

## Features

- **OAuth Token Caching** - Automatically manages and refreshes OAuth tokens
- **Request Tracking** - Each API call includes `x-request-id` for tracing
- **Error Handling** - Comprehensive error handling with detailed messages
- **Type Validation** - Validates product types and other inputs
- **Security** - Database queries restricted to SELECT statements only
- **Async Operations** - All I/O operations use async/await for performance

## Requirements

- Python 3.10+
- Access to Wiley ALM APIs
- MySQL database access
- Product Service running on localhost:8083 (optional)

## Dependencies

- `fastmcp` - FastMCP framework for building MCP servers
- `httpx` - Async HTTP client
- `python-dotenv` - Environment variable management
- `mysql-connector-python` - MySQL database connectivity
- `mcp` - Model Context Protocol SDK

## Troubleshooting

### MCP Server Not Connecting

1. Check that the path in `mcp.json` is correct
2. Verify Python executable path is correct
3. Restart Cursor after updating configuration

### Database Connection Failed

1. Verify DB credentials in `.env` or `mcp.json`
2. Check network access to database host
3. Ensure database user has appropriate permissions

### Product Service Connection Failed

1. Start the product service: `cd product-service && mvn spring-boot:run`
2. Verify service is running at configured URL
3. Check `PRODUCT_SERVICE_URL` environment variable

## License

Wiley Internal Use Only

## Support

For questions or issues, contact the ALM team.





