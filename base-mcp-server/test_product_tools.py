"""
Test script for Product Service MCP tools
Run this to verify the product service integration is working correctly
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8083")

async def test_create_product():
    """Test creating a product"""
    print("\n=== Testing Create Product ===")
    
    url = f"{PRODUCT_SERVICE_URL}/api/products"
    payload = {
        "productId": "MCP-TEST-001",
        "description": "MCP Test Product",
        "productType": "DIGITAL",
        "materialNumber": "MAT-MCP-001",
        "startDate": "2026-01-26",
        "endDate": "2026-12-31",
        "priority": "HIGH",
        "processed": False,
        "metadata": {
            "createdBy": "MCP Test Script",
            "environment": "test"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 201:
                print("✓ Product created successfully!")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"✗ Failed to create product: {response.text}")
                return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

async def test_get_product():
    """Test retrieving a product"""
    print("\n=== Testing Get Product ===")
    
    product_id = "MCP-TEST-001"
    url = f"{PRODUCT_SERVICE_URL}/api/products/{product_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✓ Product retrieved successfully!")
                print(f"Response: {response.json()}")
                return True
            elif response.status_code == 404:
                print(f"✗ Product not found: {product_id}")
                return False
            else:
                print(f"✗ Failed to retrieve product: {response.text}")
                return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

async def test_service_health():
    """Test if the product service is running"""
    print("\n=== Testing Product Service Health ===")
    
    try:
        async with httpx.AsyncClient() as client:
            # Try to access a non-existent product to check if service responds
            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/api/products/HEALTH_CHECK",
                headers={"Content-Type": "application/json"}
            )
            
            # Any response (even 404) means the service is running
            print(f"✓ Product service is running at {PRODUCT_SERVICE_URL}")
            return True
    except httpx.ConnectError:
        print(f"✗ Product service is NOT running at {PRODUCT_SERVICE_URL}")
        print("  Please start the service with: cd product-service && mvn spring-boot:run")
        return False
    except Exception as e:
        print(f"✗ Error checking service: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Product Service MCP Tools - Integration Test")
    print("=" * 60)
    print(f"Product Service URL: {PRODUCT_SERVICE_URL}")
    
    # Test service health first
    service_running = await test_service_health()
    
    if not service_running:
        print("\n" + "=" * 60)
        print("TESTS ABORTED - Service not running")
        print("=" * 60)
        return
    
    # Test create product
    create_success = await test_create_product()
    
    # Test get product (only if create was successful)
    if create_success:
        await asyncio.sleep(0.5)  # Brief pause
        await test_get_product()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Service Health: {'✓ PASS' if service_running else '✗ FAIL'}")
    print(f"Create Product: {'✓ PASS' if create_success else '✗ FAIL'}")
    print("=" * 60)
    
    if service_running and create_success:
        print("\n✓ All tests passed! The MCP tools should work correctly.")
        print("\nYou can now use these tools in Cursor:")
        print("  - create_product(productId, description, productType, ...)")
        print("  - get_product(productId)")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())


