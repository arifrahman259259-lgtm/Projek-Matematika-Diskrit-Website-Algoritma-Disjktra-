"""
Startup script untuk SmarterASP.NET
"""
import os
import sys

# Set working directory ke root project
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)

# Add modules to path
sys.path.insert(0, ROOT_DIR)

# Import server module
from importlib.machinery import SourceFileLoader
server_module = SourceFileLoader("server", os.path.join(ROOT_DIR, "modules", "server.py")).load_module()

if __name__ == "__main__":
    # Initialize database
    server_module.db_init()
    server_module.preload_from_file()
    
    # Get port from environment variable (SmarterASP.NET sets HTTP_PLATFORM_PORT)
    port = int(os.environ.get("HTTP_PLATFORM_PORT", os.environ.get("PORT", "5000")))
    
    print(f"Starting server on port {port}")
    from http.server import HTTPServer
    HTTPServer(("", port), server_module.Handler).serve_forever()

