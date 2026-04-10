# 🔒 Unified Steganography System

> A comprehensive, production-ready steganography application that combines **audio**, **image**, **video**, and **document** steganography with **hybrid RSA/AES encryption** for secure and covert data hiding.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [API Documentation](#api-documentation)
9. [Usage Guide](#usage-guide)
10. [Architecture](#architecture)
11. [Security Considerations](#security-considerations)
12. [Troubleshooting](#troubleshooting)
13. [Contributing](#contributing)
14. [License](#license)

---

## Overview

The **Unified Steganography System** is an advanced data security solution that enables you to hide sensitive information (files, text, or data) within various multimedia formats. It employs sophisticated steganographic techniques combined with military-grade encryption to ensure:

- **Confidentiality**: Data is encrypted using hybrid RSA/AES encryption
- **Integrity**: Metadata validation ensures tamper detection
- **User Isolation**: Each user has isolated RSA key pairs and file access
- **Multi-Format Support**: Hide data in audio, images, videos, or documents
- **Production-Ready**: Built with FastAPI for scalability and performance

### Use Cases

- **Privacy Protection**: Securely hide sensitive files within innocent-looking media
- **Covert Communication**: Send hidden messages embedded in public files
- **Content Protection**: Embed watermarks or metadata in digital content
- **Secure File Distribution**: Hide encrypted files in media before transmission

---

## ✨ Features

### 🎵 Multi-Format Steganography

| Format | Input | Output | Capacity |
|--------|-------|--------|----------|
| **Audio** | WAV, MP3 | WAV | Up to 20% of file size |
| **Image** | PNG, BMP, TIFF, JPG | PNG | Up to 25% of file size |
| **Video** | MP4, AVI, MOV | MP4 | Up to 1-3% of file size |
| **Document** | PDF, DOCX | Original format | Up to 5% of file size |

### 🔐 Hybrid Encryption System

- **RSA Encryption**:
  - 2048-bit RSA key pairs
  - Direct encryption for small files (≤245 bytes)
  - Public-key cryptography for secure key exchange
  - Ideal for key distribution

- **AES-256 Encryption**:
  - 256-bit symmetric encryption
  - PBKDF2 key derivation from passwords
  - Counter (CTR) mode for streaming
  - Ideal for large files

- **Hybrid Approach**:
  - Combines RSA and AES for maximum security
  - RSA encrypts AES key, AES encrypts data
  - Best of both worlds: security and performance

### 👥 User Authentication & Authorization

- **User Registration**: Create accounts with secure password hashing
- **Login Authentication**: Session-based authentication with JWT support
- **Access Control**: User can only access their own files and keys
- **Admin Dashboard**: Administrative controls for user management
- **Key Management**: Each user has isolated RSA key pairs

### 🌐 Dual Interface

- **Web Interface**: User-friendly browser-based GUI
  - Intuitive file upload/download
  - Live progress tracking
  - Responsive design
  
- **REST API**: Programmatic access
  - FastAPI with automatic documentation
  - Async/await for performance
  - Comprehensive error handling

### 🛡️ Advanced Security Features

- **GPU Video Processing**: CUDA support for fast video encoding/decoding
- **Streaming Encryption**: Process large files without loading to memory
- **Robust Steganography**: Resistant to common attacks
- **Metadata Preservation**: Maintain file properties
- **Tamper Detection**: Verify file integrity

### ⚙️ Production-Ready Architecture

- **Async Processing**: FastAPI + Uvicorn for concurrent requests
- **Task Queuing**: Redis Queue support for background jobs
- **Database Management**: SQLite with proper schema design
- **Error Handling**: Comprehensive logging and error reporting
- **Scalability**: Designed for horizontal scaling

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.100+
- **Server**: Uvicorn with Gunicorn
- **Python**: 3.8+

### Cryptography & Security
- **Encryption**: PyCryptodome
- **Key Management**: RSA 2048-bit, AES-256
- **Code Signing**: ECDSA support

### Media Processing
- **Image**: Pillow, OpenCV, imageio, piexif, scipy
- **Audio**: Native Python wave module
- **Video**: OpenCV, FFmpeg
- **Document**: PyPDF2, pdfplumber, python-docx

### Database & Caching
- **Database**: SQLite3
- **Task Queue**: Redis + RQ (optional, for production)

### Frontend
- **HTML/CSS/JavaScript**: Responsive vanilla web interface
- **Icons/UI**: Bootstrap-compatible CSS

### DevOps & Utilities
- **Process Management**: Gunicorn
- **Logging**: Python native logging
- **CORS**: FastAPI CORS middleware

---

## Project Structure

```
SteganoGraphy/
├── backend/                         # Main backend application
│   ├── api/                         # API endpoints and routers
│   │   ├── __init__.py
│   │   ├── app.py                   # FastAPI main application
│   │   ├── auth_endpoints.py        # Authentication routes (login, register)
│   │   ├── admin_endpoints.py       # Admin management routes
│   │   ├── operations_endpoints.py  # Steganography operation routes
│   │   ├── document_operations.py   # Document-specific operations
│   │   └── worker.py                # Background job worker
│   │
│   ├── core/                        # Core algorithms
│   │   ├── __init__.py
│   │   ├── optimized_stego.py       # Optimized steganography algorithms
│   │   ├── user_stego.py            # User-based steganography wrapper
│   │   ├── document_concepts_stego.py # Document steganography (16 concepts)
│   │   ├── nine_concepts_stego.py   # Advanced algorithms
│   │   └── unified_stego.py         # Unified interface
│   │
│   ├── crypto/                      # Encryption modules
│   │   ├── __init__.py
│   │   ├── rsa_handler.py           # RSA encryption/decryption
│   │   ├── aes_handler.py           # AES encryption/decryption
│   │   ├── hybrid_crypto.py         # Hybrid RSA+AES system
│   │   └── streaming_crypto.py      # Streaming encryption for large files
│   │
│   ├── steganography/               # Media-specific steganography
│   │   ├── __init__.py
│   │   ├── image_stego.py           # Image steganography (LSB, DCT, etc.)
│   │   ├── audio_stego.py           # Audio steganography (LSB, PQMF)
│   │   ├── video_stego.py           # Video frame steganography
│   │   ├── gpu_video_stego.py       # GPU-accelerated video processing
│   │   ├── document_stego.py        # PDF/DOCX steganography
│   │   ├── transmission_robust_stego.py # Robust against transmission
│   │   └── parallel_processor.py    # Parallel frame processing
│   │
│   ├── database/                    # Database management
│   │   └── __init__.py
│   │
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   └── logging_util.py          # Centralized logging
│   │
│   ├── config/                      # Configuration files
│   │   ├── requirements.txt         # Python dependencies
│   │   ├── requirements-render.txt  # Production requirements
│   │   └── render.yaml              # Deployment config
│   │
│   ├── templates/                   # HTML templates
│   │   ├── index.html               # Main interface
│   │   ├── signin.html              # Login page
│   │   └── signup.html              # Registration page
│   │
│   ├── static/                      # Static files (CSS, JS)
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   ├── script.js
│   │   │   └── script_new.js
│   │   ├── uploads/                 # User-uploaded files
│   │   ├── outputs/                 # Generated stego files
│   │   └── temp_gpu_video/          # Temporary GPU processing
│   │
│   ├── models.py                    # Database models and schema
│   ├── main.py                      # Alternative entry point
│   └── run.py                       # FastAPI runner script
│
├── docs/                            # Documentation
│   ├── README.md
│   └── FRONTEND_PROJECT_PROMPT.txt
│
├── keys/                            # System-wide RSA keys
├── user_keys/                       # Per-user RSA keys
├── temp_gpu_video/                  # Temporary GPU processing storage
│
├── setup_admin.py                   # Admin user setup script
├── validate_production_ready.py     # Production validation
├── verify_imports.py                # Dependency verification
├── app_flask_backup.py              # Legacy Flask version
├── enhanced_whatsapp_methods.py     # WhatsApp integration (optional)
│
├── run.py                           # Root entry point
├── start-dev.bat                    # Windows development startup
├── start-dev.sh                     # Linux/Mac development startup
│
└── README.md                        # This file (project documentation)
```

### Key Directories Explained

- **`backend/api/`**: REST API endpoints organized by functionality
- **`backend/core/`**: Core algorithm implementations (abstracted complexity)
- **`backend/crypto/`**: Encryption/decryption logic (RSA, AES, hybrid)
- **`backend/steganography/`**: Media format handlers (image, audio, video, doc)
- **`backend/static/`**: Web UI assets and file storage
- **`keys/` & `user_keys/`**: RSA key storage (isolated per user)

---

## Installation & Setup

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **pip** package manager
- **FFmpeg** (optional, for advanced video processing)
- **CUDA Toolkit 11.8+** (optional, for GPU video processing)
- **Redis** (optional, for production deployment)

### Step 1: Clone/Download Project

```bash
# Navigate to project directory
cd SteganoGraphy
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install from requirements file
pip install -r backend/config/requirements.txt

# Optional: GPU support (CUDA-enabled systems)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Optional: Production requirements
pip install -r backend/config/requirements-render.txt
```

### Step 4: Initialize Database

```bash
# The database initializes automatically on first run
# Or manually:
python backend/models.py
```

### Step 5: Setup Admin User (First Time Only)

```bash
# Create initial admin account
python setup_admin.py

# Follow prompts to set admin username and password
```

### Step 6: Verify Installation

```bash
# Check all imports and dependencies
python verify_imports.py

# Validate production readiness
python validate_production_ready.py
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Flask/FastAPI Configuration
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///database/stego_system.db

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# Server
HOST=0.0.0.0
PORT=5001

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5001
MAX_FILE_SIZE=500000000  # 500MB

# GPU Processing (Optional)
USE_GPU=False
CUDA_DEVICE=0
```

### Configuration Files

#### `backend/config/requirements.txt`
Core dependencies for development

#### `backend/config/requirements-render.txt`
Production dependencies (optimized for Render.com deployment)

#### `backend/config/render.yaml`
Deployment configuration for Render.com platform

---

## Deployment

> **Ready to deploy?** Check these guides:
> 
> - 📘 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (Render, Railway, Fly.io, VPS, Vercel)
> - ⚡ **[VERCEL_SETUP.md](VERCEL_SETUP.md)** - Vercel-specific workaround (not recommended)
> - 🔧 **[.env.example](.env.example)** - Configuration template
> - ✅ **Quick Validator**: `python prepare_deployment.py`

### Quick Deployment (Render)

```bash
# 1. Prepare code
git add .
git commit -m "Ready for Render deployment"
git push origin main

# 2. Create account at https://dashboard.render.com/

# 3. Connect repository and fill in:
#    Build: pip install -r backend/config/requirements.txt
#    Start: cd backend && gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT

# 4. Deploy!
```

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed instructions on all platforms.

---

## Running the Application

### Development Mode

#### Quick Start (All-in-One)

```bash
# Windows
start-dev.bat

# Linux/Mac
bash start-dev.sh
```

#### Manual Startup

```bash
# Terminal 1: Start FastAPI server
cd backend
python run.py

# Server will be available at:
# - Web UI: http://localhost:5001
# - API Docs: http://localhost:5001/docs
# - ReDoc: http://localhost:5001/redoc
```

#### With Redis Queue (Optional)

```bash
# Terminal 1: Redis server
redis-server

# Terminal 2: FastAPI server
cd backend
python run.py

# Terminal 3: RQ Worker
cd backend
python -m rq worker steganography --url redis://localhost:6379/0
```

### Production Deployment

#### Using Gunicorn

```bash
# Start Gunicorn with 4 workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:5001 \
  --access-logfile - \
  --error-logfile - \
  backend.api.app:app
```

#### Docker Deployment

```bash
# Build image
docker build -t stego-system .

# Run container
docker run -p 5001:5001 stego-system
```

#### Render.com Deployment (Recommended)

Render.com is **recommended** for this project (configured in `backend/config/render.yaml`):

```bash
# Step 1: Push code to GitHub
git add .
git commit -m "Ready for Render deployment"
git push origin main

# Step 2: Connect to Render.com
# 1. Go to https://dashboard.render.com/
# 2. Click "New +" → "Web Service"
# 3. Connect your GitHub repository
# 4. Fill in details:
#    - Name: sentinelx-steganography
#    - Environment: Python 3
#    - Root Directory: . (or path to backend if subdirectory)
#    - Build Command: pip install -r backend/config/requirements.txt
#    - Start Command: gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.api.app:app --bind 0.0.0.0:$PORT
# 5. Add environment variables:
#    - Use free tier for testing or paid for production

# Step 3: Deploy
# Render auto-deploys on each push to main
```

**Render Advantages:**
- ✅ Long-running processes supported
- ✅ Persistent storage option
- ✅ Better for heavy computation
- ✅ Free tier available for testing
- ✅ Native Python support

#### Vercel Deployment (Not Recommended - See Below)

Vercel is **NOT ideal** for FastAPI applications. See [Why Not Vercel?](#why-vercel-is-not-ideal) section for details.

---

## API Documentation

### Auto-Generated Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:5001/docs
- **ReDoc**: http://localhost:5001/redoc
- **OpenAPI JSON**: http://localhost:5001/openapi.json

### Authentication Endpoints

#### Register User
```
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password_123",
  "fullname": "John Doe"
}

Response: { "user_id": 1, "token": "jwt_token_here" }
```

#### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password_123"
}

Response: { "access_token": "jwt_token", "token_type": "bearer" }
```

#### Get Current User
```
GET /api/auth/me
Authorization: Bearer <token>

Response: { "id": 1, "username": "john_doe", "email": "john@example.com" }
```

### Steganography Operations

#### Hide File in Image
```
POST /api/operations/hide/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

Parameters:
- carrier_file: <image file>
- secret_file: <file to hide>
- encryption_method: "hybrid" (or "rsa", "aes")
- password: <optional password>

Response: { "status": "success", "stego_file": "url_to_download" }
```

#### Extract File from Image
```
POST /api/operations/extract/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

Parameters:
- stego_file: <image with hidden data>
- encryption_method: "hybrid"
- password: <matching password if used>

Response: { "status": "success", "secret_file": "url_to_download" }
```

#### Hide Text Message
```
POST /api/operations/hide/message
Authorization: Bearer <token>
Content-Type: multipart/form-data

Parameters:
- carrier_file: <media file>
- message: <text message>
- encryption_method: "hybrid"

Response: { "status": "success", "stego_file": "url_to_download" }
```

#### Extract Text Message
```
POST /api/operations/extract/message
Authorization: Bearer <token>
Content-Type: multipart/form-data

Parameters:
- stego_file: <media file>
- encryption_method: "hybrid"

Response: { "status": "success", "message": "extracted text" }
```

#### Audio Operations
```
POST /api/operations/hide/audio
POST /api/operations/extract/audio
```

#### Video Operations
```
POST /api/operations/hide/video
POST /api/operations/extract/video
```

#### Document Operations
```
POST /api/operations/hide/document
POST /api/operations/extract/document
```

### Key Management

#### Generate RSA Keys
```
POST /api/operations/generate-keys
Authorization: Bearer <token>

Response: {
  "status": "success",
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "message": "Keys generated and stored securely"
}
```

#### Get User Keys
```
GET /api/operations/keys
Authorization: Bearer <token>

Response: {
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "key_created_at": "2024-01-15T10:30:00Z"
}
```

### Admin Endpoints

#### Get All Users (Admin Only)
```
GET /api/admin/users
Authorization: Bearer <admin_token>

Response: [
  { "id": 1, "username": "user1", "email": "user1@example.com", "status": "active" },
  ...
]
```

#### Delete User (Admin Only)
```
DELETE /api/admin/users/{user_id}
Authorization: Bearer <admin_token>

Response: { "status": "success", "message": "User deleted" }
```

---

## Usage Guide

### Web Interface Workflow

#### 1. Register & Login
- Navigate to http://localhost:5001
- Click "Sign Up" to create account
- Log in with credentials

#### 2. Hide Data
- Upload a carrier file (image, audio, video, or document)
- Select the file or text to hide
- Choose encryption method
- Click "Hide" to generate stego file
- Download the result

#### 3. Extract Data
- Upload the stego file you previously created
- Click "Extract"
- Provide password if needed
- Download the extracted data

### CLI Operations (Programmatic Use)

#### Python Script Example
```python
from backend.core.user_stego import UserSteganography
from backend.crypto.hybrid_crypto import HybridCrypto

# Initialize
crypto = HybridCrypto('keys')
stego = UserSteganography('keys', 'user_keys/user_123')

# Hide file in image
stego.hide_file_in_image(
    carrier_path='photo.jpg',
    secret_path='confidential.pdf',
    output_path='stego_photo.png',
    encryption_method='hybrid',
    password='secure_pass_123'
)

# Extract file from image
stego.extract_file_from_image(
    stego_path='stego_photo.png',
    output_path='extracted.pdf',
    encryption_method='hybrid',
    password='secure_pass_123'
)
```

#### cURL Examples

```bash
# Register
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","email":"test@example.com"}'

# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# Hide file in image
curl -X POST http://localhost:5001/api/operations/hide/image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "carrier_file=@photo.jpg" \
  -F "secret_file=@secret.pdf"

# Extract file
curl -X POST http://localhost:5001/api/operations/extract/image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "stego_file=@stego_photo.png" \
  -o extracted.pdf
```

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                       │
│         (HTML/CSS/JS Web Interface)                     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Server (Uvicorn)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │           API Routers & Endpoints                │  │
│  │  - auth_endpoints.py (Login/Register)           │  │
│  │  - operations_endpoints.py (Stego Ops)          │  │
│  │  - admin_endpoints.py (User Management)         │  │
│  │  - document_operations.py (Doc Processing)      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐   ┌──────────┐   ┌────────────┐
    │  Core  │   │  Crypto  │   │   Media    │
    │ Layer  │   │ Layer    │   │ Handlers   │
    └────────┘   └──────────┘   └────────────┘
         │               │               │
    Algorithms    RSA/AES Encryption   Image/Audio/
    Abstraction   Hybrid System         Video/Doc
                                        Processing
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐   ┌──────────┐   ┌────────────┐
    │Database│   │Redis/RQ  │   │ File      │
    │(SQLite)│   │(Optional)│   │ Storage   │
    └────────┘   └──────────┘   └────────────┘
    User/Auth    Background    Uploads/
    Management    Jobs         Outputs
```

### Data Flow

1. **User Upload** → FastAPI Endpoint
2. **Authentication** → JWT Token Verification
3. **File Validation** → Format & Size Check
4. **Encryption** → Hybrid RSA/AES Processing
5. **Steganography** → Embed in Media
6. **Storage** → Save to File System
7. **Return** → Send Download Link

### Steganography Algorithms

#### Image Steganography
- **LSB (Least Significant Bit)**: Simple, capacity ~8%
- **DCT (Discrete Cosine Transform)**: More robust, capacity ~3%
- **Frequency Domain**: Advanced, resistant to compression

#### Audio Steganography
- **LSB Audio**: Similar to image LSB
- **PQMF (Polyphase Quadrature Mirror Filter)**: Frequency-based

#### Video Steganography
- **Frame-based**: Hide in individual frames
- **GPU Accelerated**: CUDA support for real-time processing

#### Document Steganography
- **PDF Metadata**: Hide in PDF streams
- **DOCX XML**: Embed in document XML structure

---

## Security Considerations

### Encryption Standards

- **RSA**: 2048-bit keys (meets NIST recommendations for ~112-bit security)
- **AES**: 256-bit keys with AES-256 cipher
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **IV/Nonce**: Generated using `secrets.token_bytes(16)`

### Best Practices

1. **Always use strong passwords** for encryption
2. **Backup RSA private keys** securely
3. **Use HTTPS** in production (not just HTTP)
4. **Enable CORS** only for trusted domains
5. **Rotate API tokens** regularly
6. **Audit user access** logs regularly
7. **Keep dependencies** updated

### Threat Mitigation

| Threat | Mitigation |
|--------|-----------|
| Brute Force Attacks | Rate limiting, account lockout |
| Man-in-the-Middle | HTTPS/TLS encryption |
| Unauthorized Access | JWT authentication, role-based access |
| Database Breach | Password hashing with salt |
| Stego Detection | Robust algorithms, noise addition |

### Password Requirements

- Minimum 12 characters
- Must include uppercase, lowercase, numbers, special chars
- Not in common password dictionary

### Key Storage

- **Public Keys**: Can be shared publicly
- **Private Keys**: Stored encrypted in `user_keys/` directory
- **Never**: Commit keys to version control
- **Backup**: Store backups in secure location

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'backend'"

**Solution**:
```bash
# Ensure you're in project root
cd SteganoGraphy

# Install dependencies
pip install -r backend/config/requirements.txt

# Verify imports
python verify_imports.py
```

#### 2. "Permission denied: 'database/stego_system.db'"

**Solution**:
```bash
# Check directory permissions
chmod 755 database/

# Or reset database
rm -rf database/
mkdir database/
# Run app to recreate
python backend/run.py
```

#### 3. "Connection refused" when accessing http://localhost:5001

**Solution**:
```bash
# Check if server is running
netstat -an | grep 5001

# Start server
cd backend
python run.py

# Try different port if 5001 is in use
python -c "from api.app import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=5002)"
```

#### 4. "FFmpeg not found" error

**Solution**:
```bash
# Windows (with Chocolatey)
choco install ffmpeg

# Linux (Debian/Ubuntu)
sudo apt-get install ffmpeg

# Mac (with Homebrew)
brew install ffmpeg
```

#### 5. GPU Processing Not Available

**Solution**:
```bash
# Check CUDA installation
nvidia-smi

# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify
python -c "import torch; print(torch.cuda.is_available())"
```

#### 6. "No such table" SQLite error

**Solution**:
```bash
# Delete corrupted database
rm database/stego_system.db

# Restart app to recreate
python backend/run.py
```

### Debug Mode

Enable detailed logging:

```python
# In backend/api/app.py or backend/run.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Performance Tuning

```bash
# Increase file upload limit
# In backend/api/app.py
MAX_FILE_SIZE = 1000000000  # 1GB

# GPU optimization for video
export CUDA_LAUNCH_BLOCKING=1

# Increase worker threads
gunicorn -w 8 --threads 2 --worker-class=gthread ...
```

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Submit pull request with description

### Code Style

- Python: Follow PEP 8
- Use type hints where possible
- Add docstrings to functions and classes
- Max line length: 100 characters

### Testing

```bash
# Run existing tests
pytest tests/

# Generate coverage report
pytest --cov=backend tests/
```

### Reporting Issues

Include:
- Python version
- OS (Windows/Linux/Mac)
- Error message and traceback
- Steps to reproduce
- Expected vs. actual behavior

---

## License

This project is licensed under the **MIT License** - see LICENSE file for details.

### MIT License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

---

## Deployment Guide

### Comparison of Deployment Platforms

| Platform | Type | Best For | Limitations |
|----------|------|----------|-------------|
| **Render** | Long-running | FastAPI/Docker | Free tier limited RAM |
| **Railway** | Long-running | Full-stack apps | Paid only |
| **Fly.io** | Long-running | Docker apps | Region selection |
| **Vercel** | Serverless | Next.js/Frontend | ❌ NOT for FastAPI |
| **Heroku** | Long-running | Full-stack apps | Paid (pricing increased) |
| **AWS** | Cloud | Enterprise | Complex setup |

### Why Vercel is NOT Ideal

**❌ Vercel Limitations for This Project:**

1. **Execution Timeout**
   - Vercel serverless: Max 60 seconds (free) or 900 seconds (pro)
   - Your steganography operations often exceed this
   - Video processing: 5+ minutes

2. **No Persistent Storage**
   - Vercel's `/tmp` is ephemeral
   - Files deleted after function execution
   - Can't store user keys or uploads

3. **Memory Constraints**
   - Vercel serverless: 512MB-3GB
   - Large media files consume significant memory
   - Video+GPU processing memory needs exceed limits

4. **Cold Start Issues**
   - Initial requests slow (Python runtime cold start)
   - Steganography processing already slow
   - Combined = poor user experience

5. **No Background Jobs**
   - Vercel doesn't support Redis/RQ workers
   - Long processes must complete in one request

### ✅ Recommended Deployment: Render.com

Your project is already configured for Render! Here's the complete setup:

#### Step-by-Step Render Deployment

##### Prerequisites
- GitHub account with your code pushed
- Render.com account (free tier available)

##### Deployment Steps

**1. Prepare Your Repository**

```bash
# Ensure render.yaml is in backend/config/
# Check that all dependencies are in requirements.txt
# Commit everything
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

**2. Create Render Account**

Visit https://dashboard.render.com/ and sign up with GitHub

**3. Connect Repository**

```
Dashboard → New + → Web Service → Connect Repository
```

**4. Configure Service**

Fill in the following details:

| Field | Value |
|-------|-------|
| **Name** | `steganography-api` |
| **Environment** | `Python 3` |
| **Region** | `Oregon` (recommended for US) |
| **Branch** | `main` |
| **Root Directory** | `.` or leave empty |
| **Build Command** | `pip install -r backend/config/requirements.txt` |
| **Start Command** | `cd backend && gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT --timeout 120` |
| **Plan** | `Free` (for testing) or `Starter` ($7/month) |

**5. Add Environment Variables**

Click "Add Environment Variable":

```env
PYTHON_VERSION=3.11
PYTHONUNBUFFERED=1
RENDER=true
SECRET_KEY=your-secret-key-here-change-this
```

**6. Deploy**

Click "Create Web Service" - Render will:
- Clone your repository
- Install dependencies
- Build and deploy
- Start the server

**7. Access Your API**

After deployment:
- API: `https://your-service-name.onrender.com`
- Docs: `https://your-service-name.onrender.com/docs`
- ReDoc: `https://your-service-name.onrender.com/redoc`

#### Render Production Configuration

For production, upgrade to paid tier and add:

```yaml
# backend/config/render.yaml
services:
  - type: web
    name: steganography-api
    runtime: python
    region: oregon
    plan: starter  # or higher
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT --timeout 300
    envVars:
      - key: RENDER
        value: "true"
      - key: DATABASE_URL
        value: "sqlite:////var/data/stego_system.db"
    disk:
      name: stego-data
      mountPath: /var/data
      sizeGB: 10
```

#### Scaling on Render

- **Free Tier**: 0.5 CPU, 512MB RAM, auto-sleeps after 15 mins
- **Starter**: 0.5 CPU, 512MB RAM, $7/month
- **Standard**: 1 CPU, 2GB RAM, $12/month
- **Pro**: 2 CPU, 4GB RAM, $29/month

For heavy video processing, recommend **Standard** or **Pro**.

### Alternative: Railway.sh

If you prefer Railway (similar to Render):

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Create railway account
railway login

# 3. Create new project
railway init

# 4. Add environment variables
railway variables set SECRET_KEY=your-secret
railway variables set PYTHONUNBUFFERED=1

# 5. Deploy
railway up
```

**railway.toml** configuration:

```toml
[build]
builder = "dockerfile"

[start]
cmd = "cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT"

[env]
PORT = "8000"
PYTHONUNBUFFERED = "1"
```

### Alternative: Fly.io (Docker-Based)

For Docker deployment (more complex but more control):

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Create app
fly launch

# 3. Deploy
fly deploy
```

**Dockerfile** for your project:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "backend.api.app:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]
```

### If You Really Want Vercel (Workarounds)

**⚠️ WARNING: Not Recommended - Only for Simple Operations**

If you insist on Vercel, you can deploy only the frontend and use a separate API endpoint:

**1. Split Frontend/Backend**

```
Create separate repository:
frontend/
├── public/
├── pages/
├── api/
│   └── proxy.js (calls external API)
└── vercel.json
```

**2. Vercel API Routes (Proxy)**

```javascript
// pages/api/stego/hide.js
export default async (req, res) => {
  if (req.method === 'POST') {
    // Forward to external API (deployed on Render/Railway)
    const response = await fetch(
      `https://your-api.onrender.com/api/operations/hide/image`,
      {
        method: 'POST',
        body: req.body,
        headers: req.headers
      }
    );
    const data = await response.json();
    res.status(response.status).json(data);
  }
};
```

**3. vercel.json**

```json
{
  "buildCommand": "npm run build",
  "serverlessFunctionRegion": "sjc1",
  "functions": {
    "api/**": {
      "memory": 3008,
      "maxDuration": 60
    }
  },
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url"
  }
}
```

**Result**: Frontend on Vercel, API on Render
- ✅ Fast frontend hosting
- ✅ Independent API scaling
- ✅ Works around Vercel limitations

---

## Support & Contact

### Documentation

- **API Docs**: http://localhost:5001/docs
- **Auto-generated**: Available when server is running
- **Examples**: Check `examples/` directory

### Getting Help

1. Check [Troubleshooting](#troubleshooting) section
2. Review existing issues on GitHub
3. Create detailed issue report
4. Contact maintainers

### Resources

- **Steganography Basics**: https://www.garykessler.net/library/steganography.html
- **Cryptography Standards**: https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **PyCryptodome Docs**: https://pycryptodome.readthedocs.io/

---

## Roadmap

### Planned Features

- [ ] Web-based file sharing between users
- [ ] Cloud storage integration (AWS S3, Google Drive)
- [ ] Mobile app (iOS/Android)
- [ ] Advanced AI-based stego detection resistance
- [ ] Real-time collaboration features
- [ ] Batch processing for multiple files
- [ ] Machine learning-based optimization
- [ ] Blockchain integration for verification

### Known Limitations

- Max concurrent video processing: GPU memory dependent
- Audio files limited to stereo support (currently)
- Document steganography capacity varies by format
- Redis queue not mandatory for development

---

## Acknowledgments

- Built with FastAPI, Pillow, and PyCryptodome
- Steganography research: University of Michigan, Watermarking Lab
- Security standards: NIST, OWASP
- Community: Python and cybersecurity communities

---

## Version History

**v2.0.0** (Current)
- Production-ready FastAPI architecture
- User authentication and authorization
- Hybrid RSA/AES encryption
- Multi-format support (audio, image, video, document)
- GPU acceleration for video processing
- Redis Queue integration
- Admin dashboard

**v1.0.0**
- Initial Flask-based implementation
- Basic image steganography
- RSA encryption only

---

## FAQ

**Q: Is my data safe?**
A: Yes. Your data is encrypted with AES-256 and RSA 2048-bit. Private keys are stored securely. However, security depends on password strength.

**Q: Can I use this commercially?**
A: Yes, it's MIT licensed. You can use it commercially, but include the license notice.

**Q: What's the maximum file size?**
A: Default 500MB, configurable. Depends on carrier media capacity (8-25% of carrier size).

**Q: Does it work on Mac/Linux?**
A: Yes, fully cross-platform. Use `start-dev.sh` on Linux/Mac.

**Q: Can I extract files from stego files I didn't create?**
A: Only if you have the matching encryption password and correct encryption method.

**Q: Is GPU required?**
A: No, but speeds up video processing significantly. Optional feature.

---

## Getting Started Checklist

- [ ] Python 3.8+ installed
- [ ] Project downloaded/cloned
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r backend/config/requirements.txt`)
- [ ] Admin user created (`python setup_admin.py`)
- [ ] Server running (`python backend/run.py`)
- [ ] Web UI accessible (http://localhost:5001)
- [ ] Account registered and logged in
- [ ] First stego file created successfully

---

**Last Updated**: April 2024  
**Maintained By**: [Your Name/Team]  
**Repository**: [GitHub Link]  
**Issues & Support**: [Support Link]

---

*Happy Steganography! 🔒🎵🖼️🎬📄*
