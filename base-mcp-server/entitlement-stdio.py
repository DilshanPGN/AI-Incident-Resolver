import asyncio
import os
import time
from dotenv import load_dotenv
from typing import Any, Optional, List, Dict
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from fastmcp import FastMCP
import uuid
import mysql.connector
from mysql.connector import Error

# OAuth configuration
class OAuthConfig:
    def __init__(self):
        load_dotenv()
        self.token_url = os.getenv( "WILEY_TOKEN_URL")
        self.client_id = os.getenv("WILEY_CLIENT_ID", "")
        self.client_secret = os.getenv("WILEY_CLIENT_SECRET", "")
        self.base_url = os.getenv("WILEY_ALM_BASE_URL")
        self.grant_type = "client_credentials"

# Database configuration
class DBConfig:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("DB_HOST", "alm-dev-db.alm.private.wiley.host")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.database = os.getenv("DB_NAME", "order_management")
        self.user = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")

# Product Service configuration
class ProductServiceConfig:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8083")

# Order Service configuration
class OrderServiceConfig:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("ORDER_SERVICE_URL", "http://localhost:8081")

# Token cache
class TokenCache:
    def __init__(self):
        self.token: Optional[str] = None
        self.expiry: float = 0

    def is_valid(self) -> bool:
        return self.token is not None and time.time() < self.expiry

    def set_token(self, token: str, expires_in: int):
        self.token = token
        # Set expiry with 5-minute buffer
        self.expiry = time.time() + expires_in - 300

# Initialize configuration and cache
oauth_config = OAuthConfig()
token_cache = TokenCache()
db_config = DBConfig()
product_service_config = ProductServiceConfig()
order_service_config = OrderServiceConfig()

# Get OAuth access token
async def get_access_token() -> str:
    # Return cached token if still valid
    if token_cache.is_valid():
        return token_cache.token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            oauth_config.token_url,
            data={
                "grant_type": oauth_config.grant_type,
                "client_id": oauth_config.client_id,
                "client_secret": oauth_config.client_secret,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"OAuth token request failed: {response.status_code} {response.text}"
            )

        data = response.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)

        token_cache.set_token(token, expires_in)
        return token

# Generic API call function
async def call_wiley_api(endpoint: str, params: dict) -> dict:
    token = await get_access_token()

    # Filter out None values from params
    filtered_params = {k: v for k, v in params.items() if v is not None}

    url = f"{oauth_config.base_url}{endpoint}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=filtered_params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-request-id": f"mcp_{uuid.uuid4()}"
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"API request failed: {response.status_code} {response.text}"
            )

        return response.json()

# Search license entitlements
async def search_license_entitlements(search_params: dict) -> dict:
    return await call_wiley_api(
        "/v1/institutions/entitlements",
        search_params
    )

# Search institutions with flexible parameters
async def search_institutions(search_params: dict) -> dict:
    return await call_wiley_api("/v1/institutions", search_params)

# Database helper functions
def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password
        )
        return connection
    except Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

async def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute a SQL query and return results as list of dictionaries"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        
        return results
    except Error as e:
        raise Exception(f"Query execution failed: {str(e)}")
    finally:
        if connection and connection.is_connected():
            connection.close()

async def get_table_schema(table_name: str) -> List[Dict]:
    """Get schema information for a table"""
    query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            COLUMN_DEFAULT,
            EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """
    return await execute_query(query, (db_config.database, table_name))

# Create FastMCP server at the top level
mcp = FastMCP("wiley-alm-server")

# Replace @server.list_tools() with @mcp.tool()
@mcp.tool()
async def search_license_entitlements(
        licenseId: str = None,
        entitledToId: str = None,
        entitlementStartDate: str = None,
        entitlementEndDate: str = None,
        contentStartDate: str = None,
        contentEndDate: str = None,
        entitlementType: str = None,
        orderNumber: str = None,
        orderLineItemId: str = None,
        status: str = None,
        assetId: str = None,
        limit: int = 100,
        page: int = 0
) -> dict:
    """Search License entitlement using various criteria."""
    arguments = {
        "licenseId": licenseId,
        "entitledToId": entitledToId,
        "entitlementStartDate": entitlementStartDate,
        "entitlementEndDate": entitlementEndDate,
        "contentStartDate": contentStartDate,
        "contentEndDate": contentEndDate,
        "entitlementType": entitlementType,
        "orderNumber": orderNumber,
        "orderLineItemId": orderLineItemId,
        "status": status,
        "assetId": assetId,
        "limit": limit,
        "page": page
    }

    # Filter out None values
    search_params = {k: v for k, v in arguments.items() if v is not None}

    if not any(k not in ["limit", "page"] for k in search_params.keys()):
        raise ValueError("At least one search parameter must be provided")

    return await call_wiley_api("/v1/institutions/entitlements", arguments)

@mcp.tool()
async def search_institutions(
        institutionId: str = None,
        bpId: str = None,
        institutionName: str = None,
        wintouchId: str = None,
        institutionType: str = None,
        status: str = None,
        ipAddress: str = None,
        derivedExternalId: str = None,
        adminEmail: str = None,
        institutionLoginId: str = None,
        limit: int = 100,
        offset: int = 0
) -> dict:
    """Search institutions using various criteria."""
    arguments = {
        "institutionId": institutionId,
        "bpId": bpId,
        "institutionName": institutionName,
        "wintouchId": wintouchId,
        "institutionType": institutionType,
        "status": status,
        "ipAddress": ipAddress,
        "derivedExternalId": derivedExternalId,
        "adminEmail": adminEmail,
        "institutionLoginId": institutionLoginId,
        "limit": limit,
        "offset": offset
    }

    # Filter out None values
    search_params = {k: v for k, v in arguments.items() if v is not None}

    if not any(k not in ["limit", "offset"] for k in search_params.keys()):
        raise ValueError("At least one search parameter must be provided")

    return await call_wiley_api("/v1/institutions", arguments)

@mcp.tool()
async def query_database(
        sql_query: str,
        limit: int = 100
) -> dict:
    """Execute a SQL query on the order_management database.
    
    Args:
        sql_query: The SQL SELECT query to execute (only SELECT queries are allowed)
        limit: Maximum number of rows to return (default 100, max 1000)
    
    Returns:
        Dictionary with query results and metadata
    """
    # Security: Only allow SELECT queries
    sql_query_upper = sql_query.strip().upper()
    if not sql_query_upper.startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    # Prevent dangerous operations
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in sql_query_upper:
            raise ValueError(f"Query contains forbidden keyword: {keyword}")
    
    # Apply limit
    limit = min(limit, 1000)  # Cap at 1000
    if 'LIMIT' not in sql_query_upper:
        sql_query = f"{sql_query.rstrip(';')} LIMIT {limit}"
    
    try:
        results = await execute_query(sql_query)
        return {
            "success": True,
            "row_count": len(results),
            "data": results,
            "query": sql_query
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": sql_query
        }

@mcp.tool()
async def list_database_tables() -> dict:
    """List all tables in the order_management database"""
    query = """
        SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME, UPDATE_TIME, TABLE_COMMENT
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
    """
    try:
        results = await execute_query(query, (db_config.database,))
        return {
            "success": True,
            "database": db_config.database,
            "table_count": len(results),
            "tables": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def describe_table(table_name: str) -> dict:
    """Get detailed schema information for a specific table
    
    Args:
        table_name: Name of the table to describe
    
    Returns:
        Dictionary with table schema information
    """
    try:
        schema = await get_table_schema(table_name)
        
        # Also get sample data
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_data = await execute_query(sample_query)
        
        return {
            "success": True,
            "table_name": table_name,
            "schema": schema,
            "sample_data": sample_data,
            "column_count": len(schema)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table_name": table_name
        }

@mcp.tool()
async def create_product(
        productId: str,
        description: str,
        productType: str,
        materialNumber: str = None,
        startDate: str = None,
        endDate: str = None,
        contents: list = None,
        metadata: dict = None,
        priority: str = None,
        processed: bool = False
) -> dict:
    """Create a new product in the product service.
    
    Args:
        productId: Unique product identifier (required)
        description: Product description (required)
        productType: Type of product - must be one of: PHYSICAL, DIGITAL, SUBSCRIPTION (required)
        materialNumber: Optional material number
        startDate: Start date in format yyyy-MM-dd
        endDate: End date in format yyyy-MM-dd
        contents: List of content objects with contentId, contentType, contentUrl, description, order
        metadata: Additional metadata as key-value pairs
        priority: Priority level
        processed: Whether the product has been processed (default: false)
    
    Returns:
        Dictionary with product creation response
    """
    # Validate productType
    valid_types = ["PHYSICAL", "DIGITAL", "SUBSCRIPTION"]
    if productType.upper() not in valid_types:
        return {
            "success": False,
            "error": f"Invalid productType. Must be one of: {', '.join(valid_types)}"
        }
    
    # Build request payload
    payload = {
        "productId": productId,
        "description": description,
        "productType": productType.upper(),
        "processed": processed
    }
    
    # Add optional fields if provided
    if materialNumber:
        payload["materialNumber"] = materialNumber
    if startDate:
        payload["startDate"] = startDate
    if endDate:
        payload["endDate"] = endDate
    if contents:
        payload["contents"] = contents
    if metadata:
        payload["metadata"] = metadata
    if priority:
        payload["priority"] = priority
    
    url = f"{product_service_config.base_url}/api/products"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_product(productId: str) -> dict:
    """Retrieve a product by its product ID.
    
    Args:
        productId: The unique product identifier
    
    Returns:
        Dictionary with product details
    """
    url = f"{product_service_config.base_url}/api/products/{productId}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Product with ID '{productId}' not found"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def create_order(
        productName: str,
        quantity: int,
        price: int
) -> dict:
    """Create a new order in the order service.
    
    Args:
        productName: Name of the product being ordered (required)
        quantity: Quantity of the product (required)
        price: Price of the product (required)
    
    Returns:
        Dictionary with order creation response
    """
    # Build request payload
    payload = {
        "productName": productName,
        "quantity": quantity,
        "price": price
    }
    
    url = f"{order_service_config.base_url}/orders"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_all_orders() -> dict:
    """Retrieve all orders from the order service.
    
    Returns:
        Dictionary with list of all orders
    """
    url = f"{order_service_config.base_url}/orders"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_order_by_id(orderId: int) -> dict:
    """Retrieve an order by its ID.
    
    Args:
        orderId: The unique order identifier
    
    Returns:
        Dictionary with order details
    """
    url = f"{order_service_config.base_url}/orders/{orderId}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Order with ID '{orderId}' not found"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def update_order(
        orderId: int,
        productName: str,
        quantity: int,
        price: int
) -> dict:
    """Update an existing order.
    
    Args:
        orderId: The unique order identifier (required)
        productName: Updated product name (required)
        quantity: Updated quantity (required)
        price: Updated price (required)
    
    Returns:
        Dictionary with updated order details
    """
    # Build request payload
    payload = {
        "productName": productName,
        "quantity": quantity,
        "price": price
    }
    
    url = f"{order_service_config.base_url}/orders/{orderId}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Order with ID '{orderId}' not found"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def delete_order(orderId: int) -> dict:
    """Delete an order by its ID.
    
    Args:
        orderId: The unique order identifier
    
    Returns:
        Dictionary with deletion status
    """
    url = f"{order_service_config.base_url}/orders/{orderId}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-request-id": f"mcp_{uuid.uuid4()}"
                }
            )
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": f"Order with ID '{orderId}' deleted successfully"
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Order with ID '{orderId}' not found"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Validate required environment variables
    if not oauth_config.client_id or not oauth_config.client_secret:
        print("Warning: WILEY_CLIENT_ID and WILEY_CLIENT_SECRET not set - API tools will not work")
    
    if not db_config.user or not db_config.password:
        print("Warning: DB_USER and DB_PASSWORD not set - Database tools will not work")
    
    print(f"Product Service URL: {product_service_config.base_url}")
    print(f"Order Service URL: {order_service_config.base_url}")

    # Run with stdio transport for desktop clients like Cursor
    mcp.run(transport="stdio")


