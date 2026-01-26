# MCP Server Setup Guide

## Environment Variables Configuration

Update your `.env` file with the following configuration:

### API Configuration (Wiley ALM)
```env
WILEY_TOKEN_URL=your_token_url_here
WILEY_CLIENT_ID=your_client_id_here
WILEY_CLIENT_SECRET=your_client_secret_here
WILEY_ALM_BASE_URL=your_base_url_here
```

### Database Configuration (MySQL)
```env
DB_HOST=alm-dev-db.alm.private.wiley.host
DB_PORT=3306
DB_NAME=order_management
DB_USER=alm_poc_user
DB_PASSWORD=UFDFbCQrfJz@nn$gK6Kg
```

## Available Tools

Once configured, your MCP server will expose 5 powerful tools:

### API Tools
1. **search_license_entitlements** - Search for license entitlements using various criteria
2. **search_institutions** - Search for institutions using various criteria

### Database Tools
3. **query_database** - Execute SQL SELECT queries on the order_management database
   - Only SELECT queries allowed for security
   - Automatic LIMIT enforcement (max 1000 rows)
   - Prevents dangerous operations (DROP, DELETE, UPDATE, etc.)

4. **list_database_tables** - List all tables in the order_management database
   - Shows table names, row counts, and metadata

5. **describe_table** - Get detailed schema and sample data for a specific table
   - Shows column names, data types, keys, defaults
   - Includes 5 sample rows

## Usage in Cursor

### Configuration
Add to Cursor Settings → Features → MCP Servers:

```json
{
  "wiley-alm-server": {
    "command": "python",
    "args": [
      "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\.venv\\Scripts\\python.exe",
      "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\entitlement-stdio.py"
    ]
  }
}
```

### Example Queries

**List all tables:**
- "Show me all tables in the database"
- Cursor will call `list_database_tables()`

**Describe a table:**
- "Describe the orders table"
- Cursor will call `describe_table(table_name="orders")`

**Query data:**
- "Show me the first 10 orders from the orders table"
- Cursor will call `query_database(sql_query="SELECT * FROM orders", limit=10)`

**Search entitlements:**
- "Find entitlements for license ID XYZ123"
- Cursor will call `search_license_entitlements(licenseId="XYZ123")`

## Security Features

✅ **Read-only database access** - Only SELECT queries allowed
✅ **Automatic query validation** - Blocks dangerous SQL keywords
✅ **Result limiting** - Prevents large data dumps
✅ **OAuth token caching** - Secure API authentication
✅ **Environment variable isolation** - Credentials stored in .env

## Running Manually

**STDIO version (for Cursor):**
```bash
python entitlement-stdio.py
```

**SSE version (web server on port 8000):**
```bash
python entitlement-sse.py
```

## Troubleshooting

**Database connection issues:**
- Verify VPN/network access to `alm-dev-db.alm.private.wiley.host`
- Check credentials in `.env` file
- Ensure MySQL port 3306 is accessible

**API authentication issues:**
- Verify WILEY_CLIENT_ID and WILEY_CLIENT_SECRET
- Check token URL is correct
- Ensure API base URL is accessible

**Module not found errors:**
- Run: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
- Or install individually: `pip install fastmcp httpx python-dotenv mcp mysql-connector-python pymysql`

