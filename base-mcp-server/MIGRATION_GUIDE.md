# Migration Guide - Reorganized MCP Server Structure

## What Changed?

All Wiley ALM MCP server files have been moved to a dedicated `base-mcp-server` directory for better organization.

## Files Moved

The following files were moved from `AI-Incident-Resolver/` to `AI-Incident-Resolver/base-mcp-server/`:

- ✅ `entitlement-stdio.py` - Main MCP server (stdio transport)
- ✅ `entitlement-sse.py` - Alternative MCP server (SSE transport)
- ✅ `pyproject.toml` - Python project configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `env.example` - Environment variable template
- ✅ `SETUP.md` - Setup instructions
- ✅ `PRODUCT_SERVICE_GUIDE.md` - Product service usage guide
- ✅ `CHANGES.md` - Changelog
- ✅ `test_product_tools.py` - Product service test script

## Required Updates

### 1. Update Cursor MCP Configuration

**Old path in `mcp.json`:**
```json
{
  "mcpServers": {
    "wiley-alm-server": {
      "command": "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\entitlement-stdio.py"
      ]
    }
  }
}
```

**New path in `mcp.json`:**
```json
{
  "mcpServers": {
    "wiley-alm-server": {
      "command": "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\cwijesekar\\OneDrive - Wiley\\Desktop\\wiley\\ALM\\sources\\Innovation_week\\FY26Q3\\AI-Incident-Resolver\\base-mcp-server\\entitlement-stdio.py"
      ],
      "env": {
        "WILEY_TOKEN_URL": "https://alm-external-sso-dev.alm.private.wiley.host/auth/realms/wiley/protocol/openid-connect/token",
        "WILEY_CLIENT_ID": "ALM-API",
        "WILEY_CLIENT_SECRET": "c9c60c12-b1c1-40e0-bf95-e15dbd99469e",
        "WILEY_ALM_BASE_URL": "https://almapi-dev.alm.private.wiley.host",
        "PRODUCT_SERVICE_URL": "http://localhost:8083"
      }
    }
  }
}
```

**Key changes:**
- Added `\\base-mcp-server` to the args path
- Added `PRODUCT_SERVICE_URL` environment variable

### 2. Move Your .env File (If You Have One)

If you have a `.env` file in the root `AI-Incident-Resolver` directory:

```powershell
Move-Item -Path "C:\Users\cwijesekar\OneDrive - Wiley\Desktop\wiley\ALM\sources\Innovation_week\FY26Q3\AI-Incident-Resolver\.env" -Destination "C:\Users\cwijesekar\OneDrive - Wiley\Desktop\wiley\ALM\sources\Innovation_week\FY26Q3\AI-Incident-Resolver\base-mcp-server\.env"
```

Or create a new `.env` file in `base-mcp-server/` based on `env.example`.

### 3. Update Test Script Paths

If you run the test script manually:

**Old command:**
```powershell
cd AI-Incident-Resolver
python test_product_tools.py
```

**New command:**
```powershell
cd AI-Incident-Resolver\base-mcp-server
python test_product_tools.py
```

## Step-by-Step Migration

### Step 1: Update Cursor MCP Config

1. Open `C:\Users\cwijesekar\.cursor\mcp.json`
2. Update the `args` path to include `\\base-mcp-server\\`
3. Add `PRODUCT_SERVICE_URL` to the `env` section
4. Save the file

### Step 2: Move or Create .env File

Option A - If you have an existing .env:
```powershell
Move-Item ".env" "base-mcp-server\.env"
```

Option B - Create new .env:
```powershell
cd base-mcp-server
Copy-Item "env.example" ".env"
# Then edit .env with your credentials
```

### Step 3: Restart Cursor

1. Close Cursor completely
2. Reopen Cursor
3. The MCP server will start automatically with the new path

### Step 4: Verify It Works

Test in Cursor chat:
```
How many products are in the database?
```

Or run the test script:
```powershell
cd base-mcp-server
python test_product_tools.py
```

## Benefits of New Structure

✅ **Better Organization** - MCP files are in their own directory  
✅ **Clearer Separation** - MCP server is separate from other services  
✅ **Easier Maintenance** - All related files in one place  
✅ **Scalability** - Easy to add more MCP server variants  
✅ **Documentation** - Self-contained with its own README  

## Rollback (If Needed)

If you need to rollback to the old structure:

```powershell
cd base-mcp-server
Move-Item * ..
cd ..
Remove-Item base-mcp-server
```

Then update your `mcp.json` back to the old path.

## Troubleshooting

### "Module not found" error

**Cause:** Python can't find the dependencies  
**Solution:** Reinstall dependencies in the new location
```powershell
cd base-mcp-server
pip install -r requirements.txt
```

### MCP server not starting in Cursor

**Cause:** Path in `mcp.json` is incorrect  
**Solution:** 
1. Check the path includes `\\base-mcp-server\\entitlement-stdio.py`
2. Use absolute paths, not relative paths
3. Restart Cursor after updating

### Environment variables not loading

**Cause:** `.env` file in wrong location  
**Solution:** 
1. Ensure `.env` is in the `base-mcp-server/` directory
2. Or set all variables in `mcp.json` env section

## Need Help?

If you encounter issues during migration:
1. Check that all paths are correct
2. Verify file permissions
3. Restart Cursor completely
4. Check Cursor logs for error messages

## Summary

The migration is simple:
1. ✅ Files already moved to `base-mcp-server/`
2. 🔧 Update `mcp.json` path
3. 🔧 Add `PRODUCT_SERVICE_URL` to config
4. 🔄 Restart Cursor
5. ✅ Done!





