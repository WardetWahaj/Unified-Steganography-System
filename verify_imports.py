#!/usr/bin/env python3
"""
Import Verification Script for Reorganized Project
Tests that all module imports work correctly after reorganization
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 70)
print(" " * 10 + "🔍 IMPORT VERIFICATION - Project Reorganization Check")
print("=" * 70)
print()

test_results = []

def test_import(import_statement, description):
    """Test an import and record result"""
    try:
        exec(import_statement)
        print(f"✅ {description}")
        test_results.append(True)
        return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {str(e)}")
        test_results.append(False)
        return False

# Test all critical imports
print("[*] Testing core steganography module imports...")
test_import("from core.unified_stego import UnifiedSteganography", "Core: UnifiedSteganography")
test_import("from core.optimized_stego import OptimizedUnifiedSteganography", "Core: OptimizedUnifiedSteganography")
test_import("from core.nine_concepts_stego import NineConceptsSteganography", "Core: NineConceptsSteganography")
test_import("from core.user_stego import UserSteganography", "Core: UserSteganography")

print("\n[*] Testing crypto module imports...")
test_import("from crypto.aes_handler import AESHandler", "Crypto: AESHandler")
test_import("from crypto.rsa_handler import RSAHandler", "Crypto: RSAHandler")
test_import("from crypto.hybrid_crypto import HybridCrypto", "Crypto: HybridCrypto")

print("\n[*] Testing steganography methods imports...")
test_import("from steganography.image_stego import ImageSteganography", "Stego: ImageSteganography")
test_import("from steganography.audio_stego import AudioSteganography", "Stego: AudioSteganography")
test_import("from steganography.video_stego import VideoSteganography", "Stego: VideoSteganography")

print("\n[*] Testing database module...")
test_import("from models import Database, UserManager", "Database: Database & UserManager")

print("\n[*] Testing API module imports...")
test_import("from api.app import app", "API: FastAPI app")
test_import("from api.auth_endpoints import auth_router, user_router, public_router", "API: Auth routers")

print("\n[*] Testing utility modules...")
test_import("from utils.logging_util import setup_logger", "Utils: setup_logger")

print("\n" + "=" * 70)

# Summary
passed = sum(test_results)
total = len(test_results)
print(f"\n[*] Test Results: {passed}/{total} passed")

if passed == total:
    print("\n✅ SUCCESS: All imports working correctly!")
    print("   The project reorganization is complete and functional.")
    print("\n[+] To start the server, run: python run.py")
    sys.exit(0)
else:
    print(f"\n❌ FAILED: {total - passed} import(s) failed")
    print("   Please review errors above and fix import paths.")
    sys.exit(1)
