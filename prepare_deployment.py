#!/usr/bin/env python3
"""
Deployment Helper Script for Unified Steganography System
Validates project and generates deployment configurations
"""

import os
import sys
import json
from pathlib import Path

class DeploymentValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / 'backend'
        self.checks_passed = 0
        self.checks_failed = 0
        
    def print_header(self, msg):
        print(f"\n{'='*60}")
        print(f"  {msg}")
        print(f"{'='*60}\n")
        
    def check(self, condition, success_msg, failure_msg):
        if condition:
            print(f"✅ {success_msg}")
            self.checks_passed += 1
        else:
            print(f"❌ {failure_msg}")
            self.checks_failed += 1
            
    def validate_project_structure(self):
        self.print_header("1. Validating Project Structure")
        
        required_dirs = [
            'backend/api',
            'backend/core',
            'backend/crypto',
            'backend/steganography',
            'backend/config',
            'backend/templates',
            'backend/static',
        ]
        
        for d in required_dirs:
            path = self.project_root / d
            self.check(
                path.exists(),
                f"Found {d}/",
                f"Missing {d}/ directory"
            )
            
        required_files = [
            'backend/config/requirements.txt',
            'backend/api/app.py',
            'backend/models.py',
            'README.md',
            'DEPLOYMENT.md',
        ]
        
        for f in required_files:
            path = self.project_root / f
            self.check(
                path.exists(),
                f"Found {f}",
                f"Missing {f}"
            )
            
    def validate_requirements(self):
        self.print_header("2. Validating Requirements.txt")
        
        req_file = self.backend_dir / 'config' / 'requirements.txt'
        
        if not req_file.exists():
            print(f"❌ requirements.txt not found at {req_file}")
            return
            
        with open(req_file) as f:
            content = f.read()
            
        required_packages = [
            'fastapi',
            'uvicorn',
            'pycryptodome',
            'Pillow',
            'opencv-python',
            'numpy',
        ]
        
        for pkg in required_packages:
            self.check(
                pkg.lower() in content.lower(),
                f"Found {pkg} in requirements",
                f"Missing {pkg} in requirements"
            )
            
    def validate_dependencies(self):
        self.print_header("3. Checking Installed Dependencies")
        
        packages_to_check = ['fastapi', 'pycryptodome', 'Pillow', 'cv2']
        
        for pkg in packages_to_check:
            try:
                __import__(pkg)
                self.check(True, f"{pkg} is installed", "")
            except ImportError:
                self.check(False, "", f"{pkg} is NOT installed")
                
    def validate_python_version(self):
        self.print_header("4. Checking Python Version")
        
        version = sys.version_info
        required_major = 3
        required_minor = 8
        
        is_valid = version.major >= required_major and version.minor >= required_minor
        
        self.check(
            is_valid,
            f"Python {version.major}.{version.minor} (Required: 3.8+)",
            f"Python {version.major}.{version.minor} is too old (Required: 3.8+)"
        )
        
    def validate_git(self):
        self.print_header("5. Checking Git Repository")
        
        git_dir = self.project_root / '.git'
        self.check(
            git_dir.exists(),
            "Git repository initialized",
            "Git repository not found - Initialize with: git init"
        )
        
        # Check if commits exist
        git_config = self.project_root / '.git' / 'config'
        self.check(
            git_config.exists(),
            "Git configured",
            "Git not properly configured"
        )
        
    def generate_checklist(self):
        self.print_header("📋 Pre-Deployment Checklist")
        
        checklist = [
            ("Code committed to Git", "git status"),
            ("No sensitive data in code", "grep -r 'password\\|api_key' backend/"),
            (".env file created", "cp .env.example .env"),
            ("Secret key generated", "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""),
            ("Requirements updated", "pip freeze > backend/config/requirements.txt"),
            ("Application tested locally", "python3 backend/run.py"),
            ("API docs accessible", "http://localhost:5001/docs"),
            ("Authentication working", "Register and login on web UI"),
        ]
        
        print("\nBefore deploying, ensure:")
        for i, (task, cmd) in enumerate(checklist, 1):
            print(f"  {i}. [ ] {task}")
            if cmd:
                print(f"     Run: {cmd}")
                
    def generate_render_guide(self):
        self.print_header("🚀 Quick Render.com Deployment")
        
        guide = """
Steps to deploy on Render:

1. Create account at https://dashboard.render.com/

2. Connect GitHub repository:
   - Dashboard → New + → Web Service
   - Select your repository
   - Authorize Render

3. Configure service:
   - Name: steganography
   - Environment: Python 3
   - Region: Oregon
   - Root Directory: . (leave empty)
   - Build Command:
     pip install -r backend/config/requirements.txt
   - Start Command:
     cd backend && gunicorn -w 2 -k uvicorn.workers.UvicornWorker \\
     api.app:app --bind 0.0.0.0:$PORT --timeout 120

4. Add Environment Variables:
   - PYTHON_VERSION = 3.11
   - PYTHONUNBUFFERED = 1
   - SECRET_KEY = (generate one: python -c "import secrets; print(secrets.token_urlsafe(32))")

5. Deploy:
   - Click "Create Web Service"
   - Wait for deployment (2-5 mins)

6. Access your API:
   - https://steganography.onrender.com
   - https://steganography.onrender.com/docs
"""
        print(guide)
        
    def generate_deployment_config(self):
        self.print_header("📝 Generating Deployment Files")
        
        # Create render.yaml if not exists
        render_yaml_path = self.backend_dir / 'config' / 'render.yaml'
        
        if not render_yaml_path.exists():
            render_yaml_content = """services:
  - type: web
    name: steganography
    runtime: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT --timeout 120
    envVars:
      - key: RENDEREXTERNAL_URL
        fromService:
          name: steganography
          property: host
      - key: PYTHONUNBUFFERED
        value: "1"
"""
            
            with open(render_yaml_path, 'w') as f:
                f.write(render_yaml_content)
            print(f"✅ Generated {render_yaml_path}")
        else:
            print(f"✅ {render_yaml_path} already exists")
            
    def print_summary(self):
        self.print_header("📊 Validation Summary")
        
        total = self.checks_passed + self.checks_failed
        percentage = (self.checks_passed / total * 100) if total > 0 else 0
        
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Total Checks: {total}")
        print(f"Success Rate: {percentage:.1f}%")
        
        if self.checks_failed == 0:
            print("\n✅ Your project is ready for deployment!")
            print("\nRecommended next steps:")
            print("  1. Review DEPLOYMENT.md for detailed instructions")
            print("  2. Set up .env file with your configuration")
            print("  3. Test locally: python backend/run.py")
            print("  4. Push to GitHub: git push origin main")
            print("  5. Deploy to Render: Follow above guide")
        else:
            print(f"\n⚠️  Please fix the {self.checks_failed} issue(s) before deploying")
            
    def run(self):
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║  🚀 UNIFIED STEGANOGRAPHY SYSTEM - DEPLOYMENT VALIDATOR  ║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        
        self.validate_project_structure()
        self.validate_requirements()
        self.validate_dependencies()
        self.validate_python_version()
        self.validate_git()
        self.generate_checklist()
        self.generate_render_guide()
        self.generate_deployment_config()
        self.print_summary()

if __name__ == '__main__':
    validator = DeploymentValidator()
    validator.run()
