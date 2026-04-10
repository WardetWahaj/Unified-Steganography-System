#!/usr/bin/env python3
"""
Steganography System - Root Entry Point
Launches the backend server from the backend folder
"""
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory
os.chdir(backend_path)

# Now import and run the app
if __name__ == '__main__':
    import uvicorn
    from api.app import app
    
    print("=" * 70)
    print(" " * 10 + "UNIFIED STEGANOGRAPHY SYSTEM - FastAPI Server")
    print("=" * 70)
    print(f"\n[+] Working directory: {os.getcwd()}")
    print("[+] Starting Uvicorn server...")
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
