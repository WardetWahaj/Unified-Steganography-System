"""
Unified Steganography System - FastAPI + Redis Queue
=====================================================
Production-ready API server with async support and task queuing.

Architecture:
  FastAPI (Uvicorn) -> Redis Queue -> Workers
  Supports: Audio, Image, Video steganography with RSA/AES encryption

Running:
  Development:  python app.py
  Production:   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:5000
  Worker:       rq worker steganography --url redis://localhost:6379/0
"""
import os
import sys
import secrets
import shutil
import threading
import time
from typing import Optional

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.document_concepts_stego import DocumentConceptsSteganography  # Full 16-concept system

# User-based steganography and authentication
try:
    from api.auth_endpoints import auth_router, user_router, public_router, get_current_user
    from api.admin_endpoints import admin_router
    from api.operations_endpoints import router as operations_router
    from api.document_operations import router as document_operations_router
    from models import Database, UserManager
    AUTH_ENABLED = True
    print("[+] User authentication system loaded successfully")
    print("[+] Admin endpoints loaded successfully")
    print("[+] Operations endpoints loaded successfully")
    print("[+] Document operations endpoints loaded successfully")
except Exception as e:
    AUTH_ENABLED = False
    print(f"[!] Warning: Could not load auth system: {e}")

# Redis/Queue imports (graceful fallback)
try:
    import redis
    from rq import Queue
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

# Configure FastAPI app
app = FastAPI(
    title="Unified Steganography System",
    description="Image, Audio steganography with RSA/AES encryption",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routers if enabled
if AUTH_ENABLED:
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(public_router)
    app.include_router(admin_router)
    app.include_router(operations_router)
    app.include_router(document_operations_router)
    print("[+] Authentication routers registered")
    print("[+] Admin router registered")
    print("[+] Operations router registered")
    print("[+] Document operations router registered")


# Early rejection of oversized uploads to protect Render's 512 MB RAM.
# Checks Content-Length header before the body is read into memory.
@app.middleware("http")
async def reject_oversized_uploads(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_CONTENT_SIZE:
            return JSONResponse(
                {"success": False, "error": f"Upload too large ({int(cl)} bytes). Max is {MAX_CONTENT_SIZE} bytes."},
                status_code=413,
            )
    return await call_next(request)

# Setup directories — use /tmp on Render (ephemeral filesystem)
# BASE_DIR should point to project root, not api/ subdirectory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IS_RENDER = bool(os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL'))
if IS_RENDER:
    UPLOAD_FOLDER = '/tmp/stego_uploads'
    OUTPUT_FOLDER = '/tmp/stego_outputs'
    KEY_FOLDER = '/tmp/stego_keys'
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'outputs')
    KEY_FOLDER = os.path.join(BASE_DIR, 'keys')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(KEY_FOLDER, exist_ok=True)

# Templates and static files
templates_dir = os.path.join(BASE_DIR, 'templates')
static_dir = os.path.join(BASE_DIR, 'static')
if os.path.isdir(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize steganography system with all 16 concepts and optimizations enabled
stego = DocumentConceptsSteganography(
    key_dir=KEY_FOLDER,
    use_gpu=True,           # GPU acceleration enabled (CUDA if available)
    use_streaming=True,      # Streaming encryption for large files
    use_compression=True,    # Enable compression for reduced file size
    max_workers=4            # 4 parallel workers for i7-9750H
)

# Auto-generate RSA keys on startup if they don't exist (critical for Render)
if not stego.keys_exist():
    print("[*] No RSA keys found — generating new key pair on startup...")
    stego.generate_keys()
    print("[+] RSA keys generated and ready.")
else:
    print("[*] RSA keys already exist.")

# ── Keep-alive self-ping (prevents Render free tier from sleeping) ──
def _keep_alive_ping():
    """Ping own /health endpoint every 13 minutes to prevent Render sleep."""
    import urllib.request
    ext_url = os.environ.get('RENDER_EXTERNAL_URL', '')
    if not ext_url:
        print("[!] RENDER_EXTERNAL_URL not set — keep-alive disabled")
        return
    health_url = f"{ext_url}/health"
    print(f"[*] Keep-alive started — pinging {health_url} every 13 min")
    while True:
        time.sleep(13 * 60)  # 13 minutes
        try:
            urllib.request.urlopen(health_url, timeout=10)
            print(f"[+] Keep-alive ping OK at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[!] Keep-alive ping failed: {e}")

_keep_alive_thread = threading.Thread(target=_keep_alive_ping, daemon=True)
_keep_alive_thread.start()

# Session store (in-memory for local dev; use Redis-backed sessions in production)
_sessions = {}

# Redis queue setup
redis_conn = None
task_queue = None
if REDIS_AVAILABLE:
    try:
        redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        redis_conn.ping()
        task_queue = Queue('steganography', connection=redis_conn, default_timeout=600)
        print("[+] Redis connected - task queue enabled")
    except Exception:
        redis_conn = None
        task_queue = None
        print("[!] Redis not available - running in sync mode")

# Allowed file extensions
# Note: Video steganography re-enabled with DCT (robust to compression)
ALLOWED_EXTENSIONS = {
    'audio': {'wav', 'mp3', 'flac', 'aiff'},
    'image': {'png', 'bmp', 'tiff', 'jpg', 'jpeg'},
    'video': {'mp4', 'avi', 'mov', 'mkv'}
}
MAX_CONTENT_SIZE = 50 * 1024 * 1024 if IS_RENDER else 1000 * 1024 * 1024  # 50MB on Render, 1GB local


def allowed_file(filename: str, file_type: str = 'all') -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'all':
        all_exts = set()
        for exts in ALLOWED_EXTENSIONS.values():
            all_exts.update(exts)
        return ext in all_exts
    else:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())


def _secure_filename(filename: str) -> str:
    import re
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    filename = filename.strip()
    return filename or 'upload'


def get_session_id(request: Request) -> str:
    """Get or create a session ID from cookie or header"""
    sid = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
    if not sid:
        sid = secrets.token_hex(16)
    return sid


def cleanup_session_files(session_id: str):
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            if filename.startswith(session_id):
                try:
                    os.remove(os.path.join(folder, filename))
                except Exception:
                    pass


async def save_upload_file(file: UploadFile, session_id: str, prefix: str) -> str:
    """Save an uploaded file and return its path"""
    filename = _secure_filename(file.filename or 'upload')
    filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{prefix}_{filename}")
    content = await file.read()
    if len(content) > MAX_CONTENT_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    with open(filepath, 'wb') as f:
        f.write(content)
    return filepath


def dispatch_task(func, *args) -> dict:
    if task_queue is not None:
        job = task_queue.enqueue(func, *args, result_ttl=3600)
        return {'queued': True, 'job_id': job.id, 'status': 'processing'}
    else:
        return func(*args)


# ═══════════════════════════════════════════════════════════
# WORKER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def process_hide_file(secret_path, cover_path, output_path, password, use_encryption):
    try:
        actual_output = stego.hide_file(secret_path, cover_path, output_path,
                        password if use_encryption else None, use_encryption)
        actual_filename = os.path.basename(actual_output)
        # Cleanup input files
        for p in [secret_path, cover_path]:
            if os.path.exists(p):
                os.remove(p)
        return {
            'success': True,
            'message': 'File hidden successfully',
            'output_file': actual_filename
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_extract_file(stego_path, output_path, password, use_encryption):
    try:
        stego.extract_file(stego_path, output_path,
                           password if use_encryption else None, use_encryption)
        if os.path.exists(stego_path):
            os.remove(stego_path)
        return {
            'success': True,
            'message': 'File extracted successfully',
            'output_file': os.path.basename(output_path)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_hide_message(message, cover_path, output_path, password, use_encryption):
    try:
        actual_output = stego.hide_message(message, cover_path, output_path,
                                           password if use_encryption else None, use_encryption)
        actual_filename = os.path.basename(actual_output)
        if os.path.exists(cover_path):
            os.remove(cover_path)
        return {
            'success': True,
            'message': 'Message hidden successfully',
            'output_file': actual_filename,
            'download_url': f'/api/download/{actual_filename}',
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_hide_message_whatsapp(data, cover_path, stego_path, use_encryption, password):
    try:
        from steganography.transmission_robust_stego import WhatsAppRobustSteganography
        whatsapp_stego = WhatsAppRobustSteganography()

        if use_encryption and password:
            data, method = stego.crypto.encrypt_data(data, password, use_rsa=True)

        whatsapp_stego.encode_for_whatsapp(cover_path, stego_path, data)

        if os.path.exists(cover_path):
            os.remove(cover_path)

        stego_filename = os.path.basename(stego_path)
        return {
            'success': True,
            'message': 'Message hidden successfully with WhatsApp optimization',
            'stego_file': stego_filename,
            'download_url': f'/api/download/{stego_filename}',
            'method': 'WhatsApp-optimized transmission-robust steganography',
            'note': 'This image is optimized to survive WhatsApp compression'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_extract_message(stego_path, password, use_encryption):
    try:
        extracted_message = None
        extraction_method = None

        try:
            extracted_message = stego.extract_message(
                stego_path,
                password if use_encryption else None,
                use_encryption
            )
            extraction_method = "Standard extraction"
        except Exception as standard_error:
            stego_filename = os.path.basename(stego_path).lower()
            if stego_filename.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                from steganography.transmission_robust_stego import TransmissionRobustSteganography, WhatsAppRobustSteganography

                try:
                    whatsapp_stego = WhatsAppRobustSteganography()
                    raw_data = whatsapp_stego.decode_from_whatsapp(stego_path)
                    if use_encryption and password:
                        raw_data = stego.crypto.decrypt_data(raw_data, password, method='AUTO')
                    extracted_message = raw_data.decode('utf-8', errors='ignore')
                    extraction_method = "WhatsApp-robust extraction"
                except Exception:
                    try:
                        ultra_stego = TransmissionRobustSteganography()
                        raw_data = ultra_stego.decode(stego_path)
                        if use_encryption and password:
                            raw_data = stego.crypto.decrypt_data(raw_data, password, method='AUTO')
                        extracted_message = raw_data.decode('utf-8', errors='ignore')
                        extraction_method = "Ultra-robust extraction"
                    except Exception:
                        raise standard_error
            else:
                raise standard_error

        if os.path.exists(stego_path):
            os.remove(stego_path)

        if extracted_message is not None:
            return {
                'success': True,
                'message': f'Message extracted successfully using {extraction_method}',
                'extracted_message': extracted_message,
                'extraction_method': extraction_method
            }
        else:
            return {
                'success': False,
                'error': 'Could not extract message - file may be corrupted or not contain hidden data'
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ═══════════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Redirect to signin or dashboard based on auth status"""
    # Check if user is authenticated
    token = request.cookies.get('access_token')
    if token:
        return FileResponse(os.path.join(BASE_DIR, 'templates', 'index.html'))  # Dashboard
    else:
        return FileResponse(os.path.join(BASE_DIR, 'templates', 'signin.html'))  # Sign in page


@app.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """Sign in page"""
    return FileResponse(os.path.join(BASE_DIR, 'templates', 'signin.html'))


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Sign up page"""
    return FileResponse(os.path.join(BASE_DIR, 'templates', 'signup.html'))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page (requires authentication)"""
    token = request.cookies.get('access_token')
    if not token:
        return FileResponse(os.path.join(BASE_DIR, 'templates', 'signin.html'))  # Redirect to signin if not authenticated
    return FileResponse(os.path.join(BASE_DIR, 'templates', 'index.html'))


# API ROUTES
# ═══════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    return {
        'status': 'healthy',
        'server': 'FastAPI + Uvicorn',
        'queue': 'Redis RQ' if task_queue else 'sync (local)',
        'service': 'Steganography Analysis',
        'version': '2.0'
    }


@app.post("/api/generate-keys")
async def generate_keys():
    try:
        pub_key, priv_key = stego.generate_keys()
        return {
            'success': True,
            'message': 'RSA keys generated successfully',
            'public_key': pub_key,
            'private_key': priv_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/hide-message-whatsapp")
async def hide_message_whatsapp(
    request: Request,
    cover_file: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(''),
    use_encryption: str = Form('true')
):
    session_id = get_session_id(request)
    encrypt = use_encryption.lower() == 'true'

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if encrypt and not password:
        raise HTTPException(status_code=400, detail="Password required for encryption")
    if not allowed_file(cover_file.filename or '', 'image'):
        raise HTTPException(status_code=400, detail="WhatsApp optimization requires image files")

    cover_path = await save_upload_file(cover_file, session_id, "cover")

    cover_filename = _secure_filename(cover_file.filename or 'cover')
    stego_filename = f"{session_id}_whatsapp_stego_{cover_filename.rsplit('.', 1)[0]}.jpg"
    stego_path = os.path.join(OUTPUT_FOLDER, stego_filename)

    data = message.encode('utf-8')

    result = dispatch_task(process_hide_message_whatsapp, data, cover_path, stego_path, encrypt, password)

    if isinstance(result, dict) and result.get('queued'):
        return JSONResponse(result, status_code=202)

    response = JSONResponse(result)
    response.set_cookie('session_id', session_id)
    return response


    response.set_cookie('session_id', session_id)
    return response


@app.get("/api/download/{filename}")
async def download_file(filename: str, request: Request):
    """Download a stego file - authenticated users can download their files"""
    print(f"\n[DOWNLOAD] Request for file: {filename}")
    
    # Try to get authenticated user
    user = None
    try:
        system_session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        if system_session_token and AUTH_ENABLED:
            # Try to validate with auth system
            user_id = db.get_session_user(system_session_token)
            if user_id:
                user = db.get_user_by_id(user_id)
                print(f"[DOWNLOAD] Authenticated user: {user['username'] if user else 'Unknown'}")
    except Exception as e:
        print(f"[DOWNLOAD] Auth check failed: {e}")
    
    # Allow download if file exists
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    print(f"[DOWNLOAD] Looking for file at: {file_path}")
    print(f"[DOWNLOAD] File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"[DOWNLOAD] ERROR: File not found - listing available files in {OUTPUT_FOLDER}:")
        try:
            files = os.listdir(OUTPUT_FOLDER)
            for f in files[:10]:  # Show first 10 files
                print(f"  - {f}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
        except Exception as e:
            print(f"[DOWNLOAD] Could not list directory: {e}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Extract original filename (remove any prefix like user_id_)
    # Handle both formats: "filename.ext" and "userid_randomid_filename.ext"
    download_name = filename
    if '_stego' in filename:
        # Extract just the stego part
        parts = filename.rsplit('_stego', 1)
        if len(parts) > 0:
            # Try to get original extension
            remaining = parts[0]
            # Skip leading user_id and random token
            tokens = remaining.split('_')
            if len(tokens) > 2:
                download_name = '_'.join(tokens[2:]) + '_stego' + (parts[1] if len(parts) > 1 else '')
    elif '_msg' in filename:
        # Handle message files
        parts = filename.rsplit('_msg', 1)
        if len(parts) > 0:
            remaining = parts[0]
            tokens = remaining.split('_')
            if len(tokens) > 2:
                download_name = '_'.join(tokens[2:]) + '_msg' + (parts[1] if len(parts) > 1 else '')
    
    print(f"[DOWNLOAD] Returning file as: {download_name}")
    return FileResponse(file_path, filename=download_name)


@app.post("/api/cleanup")
async def cleanup(request: Request):
    session_id = get_session_id(request)
    cleanup_session_files(session_id)
    return {'success': True, 'message': 'Files cleaned up'}


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    if not REDIS_AVAILABLE or redis_conn is None:
        raise HTTPException(status_code=404, detail="Queue not active")

    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.is_finished:
        return {'status': 'completed', 'result': job.result}
    elif job.is_failed:
        return {'status': 'failed', 'error': str(job.exc_info)}
    else:
        return {'status': job.get_status()}


# ═══════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    import socket
    import uvicorn

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "localhost"
    local_ip = get_local_ip()
    port = int(os.environ.get('PORT', 5000))

    print("=" * 70)
    print(" " * 15 + "UNIFIED STEGANOGRAPHY SYSTEM")
    print(" " * 10 + "Audio • Image • Video with RSA Encryption")
    print(" " * 10 + "FastAPI + Uvicorn + Redis Queue")
    print("=" * 70)
    print(f"\n[*] Local Access:    http://localhost:{port}")
    print(f"[*] Network Access:  http://{local_ip}:{port}")
    print(f"[*] API Docs:        http://localhost:{port}/docs")
    print(f"\n[!] For mobile devices on same WiFi:")
    print(f"    Update Flutter app baseUrl to: http://{local_ip}:{port}")
    print(f"\n[*] Press Ctrl+C to stop\n")

    uvicorn.run(app, host='0.0.0.0', port=port, log_level='info')
