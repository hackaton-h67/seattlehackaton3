#!/usr/bin/env python3
"""Simple API test without needing to start the server."""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_api_structure():
    print("="*60)
    print("API GATEWAY STRUCTURE TEST")
    print("="*60)
    print()

    try:
        # Import FastAPI app
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "api_gateway",
            Path(__file__).parent / "services" / "api-gateway" / "main.py"
        )
        api_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_module)

        app = api_module.app

        print("✓ API Gateway application loaded")
        print(f"  Title: {app.title}")
        print(f"  Version: {app.version}")
        print()

        # List routes
        print("Available Routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'N/A'
                print(f"  {methods:12} {route.path}")

        print()
        print("="*60)
        print("✓ API Gateway is ready!")
        print("="*60)
        print()
        print("To start the server manually:")
        print("  cd services/api-gateway")
        print("  ../../venv/bin/python main.py")
        print()
        print("Or use:")
        print("  ./start_api.sh")
        print()
        print("Then test with:")
        print("  curl http://localhost:8000/health")
        print("="*60)

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_structure()
    sys.exit(0 if success else 1)
