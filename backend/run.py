#!/usr/bin/env python3
"""
Entry Point for Unified Steganography System
Launches FastAPI server with proper path configuration
"""
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the app
if __name__ == '__main__':
    import uvicorn
    from api.app import app
    
    print("=" * 70)
    print(" " * 10 + "UNIFIED STEGANOGRAPHY SYSTEM - FastAPI Server")
    print("=" * 70)
    print("\n[+] Starting Uvicorn server...")
    print("[+] API will be available at: http://localhost:5001")
    print("[+] API docs at: http://localhost:5001/docs")
    print("[+] ReDoc at: http://localhost:5001/redoc")
    print("\n[*] Press Ctrl+C to stop the server\n")
    
    # Run Uvicorn server
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=5001,
        reload=False,
        log_level='info'
    )
