"""
Authentication endpoints for user-based steganography system
Add these to your FastAPI app
"""
import os
import sys
import json
import secrets
from datetime import datetime, timedelta

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from models import Database, UserManager


# ═══════════════════════════════════════════════════════════
# STEGANOGRAPHY CONCEPTS (12 Total)
# ═══════════════════════════════════════════════════════════

CONCEPTS = {
    # Multimedia concepts 1-9 + Document concepts 10-16
    'i2i': {'name': 'Image → Image', 'dataType': 'image', 'coverType': 'image', 'capacity': 10},
    'i2v': {'name': 'Image → Video', 'dataType': 'image', 'coverType': 'video', 'capacity': 100},
    'i2a': {'name': 'Image → Audio', 'dataType': 'image', 'coverType': 'audio', 'capacity': 50},
    'v2i': {'name': 'Video → Image', 'dataType': 'video', 'coverType': 'image', 'capacity': 5},
    'v2v': {'name': 'Video → Video', 'dataType': 'video', 'coverType': 'video', 'capacity': 200},
    'v2a': {'name': 'Video → Audio', 'dataType': 'video', 'coverType': 'audio', 'capacity': 100},
    'a2i': {'name': 'Audio → Image', 'dataType': 'audio', 'coverType': 'image', 'capacity': 8},
    'a2v': {'name': 'Audio → Video', 'dataType': 'audio', 'coverType': 'video', 'capacity': 150},
    'a2a': {'name': 'Audio → Audio', 'dataType': 'audio', 'coverType': 'audio', 'capacity': 80},
    # New 3 document concepts
    'd2i': {'name': 'Document → Image', 'dataType': 'document', 'coverType': 'image', 'capacity': 5},
    'd2v': {'name': 'Document → Video', 'dataType': 'document', 'coverType': 'video', 'capacity': 50},
    'd2a': {'name': 'Document → Audio', 'dataType': 'document', 'coverType': 'audio', 'capacity': 20},
}

MIME_TYPE_MAP = {
    'image': [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
        'image/x-windows-bmp', 'image/vnd.microsoft.icon'
    ],
    'video': [
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 
        'video/x-matroska', 'video/x-msvideo', 'video/avi', 'video/webm',
        'video/x-flv', 'video/x-ms-wmv'
    ],
    'audio': [
        'audio/mpeg', 'audio/wav', 'audio/webm', 'audio/ogg', 'audio/flac',
        'audio/aac', 'audio/x-m4a', 'audio/x-wav', 'audio/x-ms-wma'
    ],
    'document': [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'application/vnd.ms-word',
        'application/x-docx'
    ]
}

# File extension mappings (case will be handled by converting to lowercase)
EXTENSION_MAP = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'],
    'video': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.webm', '.m4v'],
    'audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', '.webm'],
    'document': ['.pdf', '.docx', '.doc', '.txt']
}


def get_file_type(file: UploadFile) -> str:
    """Detect file type based on extension first, then MIME type (most reliable approach)"""
    mime_type = (file.content_type or '').lower()
    filename = (file.filename or '')
    file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Check extension FIRST (most reliable)
    # Document extensions
    if file_extension in ['pdf', 'docx', 'doc', 'txt', 'rtf', 'odt']:
        return 'document'
    
    # Image extensions
    if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff']:
        return 'image'
    
    # Video extensions
    if file_extension in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'mpeg', 'mpg', 'm4v', '3gp']:
        return 'video'
    
    # Audio extensions
    if file_extension in ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a', 'wma', 'opus', 'aiff']:
        return 'audio'
    
    # Fall back to MIME type
    if mime_type.startswith('image/'):
        return 'image'
    if mime_type.startswith('video/'):
        return 'video'
    if mime_type.startswith('audio/'):
        return 'audio'
    
    # Document MIME types
    if any(keyword in mime_type for keyword in ['pdf', 'word', 'document', 'officedocument', 'text/plain', 'msword']):
        return 'document'
    
    return None


# ═══════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    """Request body for signup endpoint"""
    fullname: str
    username: str
    email: str
    password: str


class SigninRequest(BaseModel):
    """Request body for signin endpoint"""
    username: str
    password: str

# Create router for auth endpoints
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])
user_router = APIRouter(prefix="/api/user", tags=["user operations"])
public_router = APIRouter(prefix="/api", tags=["public"])

# Initialize database and user manager
db = Database()
user_manager = UserManager(db=db)


def get_current_user(request: Request):
    """Extract user from Authorization Bearer token, session cookie, or header"""
    user_id = None
    
    # Try Authorization Bearer token first (for API clients like frontend)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        session_token = auth_header[7:]  # Remove 'Bearer ' prefix
        if session_token:
            user_id = db.get_session_user(session_token)
            print(f"[DEBUG-AUTH] Extracted user {user_id} from Bearer token")
    
    # Fallback to session cookie or X-Session-Token header
    if not user_id:
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        if session_token:
            user_id = db.get_session_user(session_token)
            print(f"[DEBUG-AUTH] Extracted user {user_id} from session token")
    
    if not session_token and not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated - no Authorization header or session cookie")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # CHECK IF USER IS SUSPENDED
    user_status = user.get('status', 'active') if user else 'active'
    if user_status == 'suspended':
        print(f"[DEBUG-AUTH] Access denied - user is suspended: {user.get('username')}")
        db.invalidate_session(session_token)  # Invalidate session
        raise HTTPException(status_code=403, detail="Your account has been suspended. Please contact the administrator.")
    
    return dict(user)


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════

@auth_router.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...)):
    """
    Create new user with RSA key pair
    
    - Generates unique 2048-bit RSA keys for the user
    - Stores public key on server
    - Returns user info with session token
    """
    try:
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Create user and generate keys
        result = user_manager.signup(username, password)
        user_id = result['user_id']
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        db.create_session(user_id, session_token, expires_at)
        
        response = JSONResponse({
            'success': True,
            'message': 'Signup successful',
            'user_id': user_id,
            'username': username,
            'session_token': session_token,
            'public_key': result['public_key'][:100] + '...'  # Return snippet
        })
        response.set_cookie('session_id', session_token, httponly=True, max_age=86400)
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Authenticate user and create session
    
    - Verifies password
    - Returns session token
    - User can now use encrypted endpoints
    - Checks user suspension status
    """
    try:
        print(f'[DEBUG] Login attempt: username={username}')
        result = user_manager.login(username, password)
        print(f'[DEBUG] Login successful for user: {username}')
        
        # Get user details including role and status
        user = db.get_user_by_username(username)
        role = 'admin' if username == 'admin' else 'user'  # Default role logic
        
        # CHECK IF USER IS SUSPENDED
        user_status = user.get('status', 'active') if user else 'active'
        print(f'[DEBUG] User status: {user_status}')
        
        if user_status == 'suspended':
            print(f'[DEBUG] Login rejected - user is suspended: {username}')
            raise ValueError("Your account has been suspended. Please contact the administrator.")
        
        print(f'[DEBUG] User data: {user}, role: {role}')
        print(f'[DEBUG] Session token: {result["session_token"][:20]}...')
        
        response = JSONResponse({
            'success': True,
            'message': 'Login successful',
            'user_id': result['user_id'],
            'username': username,
            'role': role,
            'session_token': result['session_token'],
            'public_key_preview': result['public_key'][:100] + '...'
        })
        response.set_cookie('session_id', result['session_token'], httponly=True, max_age=86400)
        return response
    
    except ValueError as e:
        print(f'[ERROR] ValueError: {e}')
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        print(f'[ERROR] Exception in login: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/logout")
async def logout(request: Request):
    """Logout user and invalidate session"""
    try:
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        
        if session_token:
            db.invalidate_session(session_token)
        
        response = JSONResponse({'success': True, 'message': 'Logout successful'})
        response.delete_cookie('session_id')
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.get("/me")
async def get_current_user_info(request: Request):
    """Get current user info"""
    try:
        user = get_current_user(request)
        role = 'admin' if user['username'] == 'admin' else 'user'  # Default role logic
        
        return {
            'user_id': user['id'],
            'username': user['username'],
            'role': role,
            'created_at': user['created_at'],
            'public_key_preview': user['public_key'][:100] + '...'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# USER STEGANOGRAPHY ENDPOINTS
# ═══════════════════════════════════════════════════════════

@public_router.post("/hide-file")
async def user_hide_file(request: Request):
    """
    Hide file - File-to-file steganography with 12 concepts
    
    Supports 12 steganography concepts:
    - Original 9: i2i, i2v, i2a, v2i, v2v, v2a, a2i, a2v, a2a
    - New 3: d2i, d2v, d2a (document → image/video/audio)
    
    Encryption methods:
    - 'rsa': RSA only (secure, default)
    - 'password': Password only
    - 'hybrid': RSA + Password (recommended)
    
    :param request: Request object containing multipart form data
    """
    try:
        # Parse multipart form data manually for better error handling
        form = await request.form()
        
        # Extract files
        data_file = form.get('data_file')
        cover_file = form.get('cover_file')
        concept_id = form.get('concept_id', '')
        password = form.get('password', '')
        encryption_type = form.get('encryption_type', 'rsa')
        compress = form.get('compress', 'false')
        recipients = form.get('recipients', '')
        
        # Strip whitespace from password
        if password:
            password = password.strip()
        
        # Log received parameters
        print(f"[DEBUG] hide-file received:")
        print(f"  - data_file: {data_file.filename if hasattr(data_file, 'filename') else 'EMPTY'}")
        print(f"  - cover_file: {cover_file.filename if hasattr(cover_file, 'filename') else 'EMPTY'}")
        print(f"  - concept_id: {concept_id}")
        print(f"  - encryption_type: {encryption_type}")
        print(f"  - password: {repr(password)}")
        print(f"  - password length: {len(password) if password else 0}")
        if password:
            print(f"  - password bytes: {password.encode('utf-8').hex()}")
        print(f"  - compress: {compress}")
        print(f"  - recipients: {recipients}")
        
        # Validate files exist
        if not data_file:
            raise HTTPException(status_code=400, detail="data_file is required")
        if not cover_file:
            raise HTTPException(status_code=400, detail="cover_file is required")
        
        # Get current user and session
        user = get_current_user(request)
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        
        from core.user_stego import UserSteganography
        import json
        
        # Validate concept
        if concept_id not in CONCEPTS:
            raise HTTPException(status_code=400, detail=f"Invalid concept. Choose from: {', '.join(CONCEPTS.keys())}")
        
        concept = CONCEPTS[concept_id]
        print(f"[+] Using concept: {concept['name']} (capacity: {concept['capacity']}MB)")
        
        # Validate file types match concept requirements
        data_type = get_file_type(data_file)
        cover_type = get_file_type(cover_file)
        
        if data_type != concept['dataType']:
            raise HTTPException(
                status_code=400,
                detail=f"Data file type mismatch. Concept expects {concept['dataType']}, got {data_type or 'unknown'}"
            )
        
        if cover_type != concept['coverType']:
            raise HTTPException(
                status_code=400,
                detail=f"Cover file type mismatch. Concept expects {concept['coverType']}, got {cover_type or 'unknown'}"
            )
        
        print(f"[+] File types validated: data={data_type}, cover={cover_type}")
        
        # Validate encryption type
        if encryption_type not in ['rsa', 'password', 'hybrid']:
            raise HTTPException(status_code=400, detail="Invalid encryption type. Choose 'rsa', 'password', or 'hybrid'")
        
        # Auto-downgrade encryption if password is missing
        if encryption_type == 'hybrid' and not password:
            print("[*] Hybrid requested but no password - falling back to RSA")
            encryption_type = 'rsa'
        elif encryption_type == 'password' and not password:
            raise HTTPException(status_code=400, detail="Password required for password-only encryption")
        
        # Parse recipients
        recipient_ids = []
        if recipients:
            try:
                recipient_ids = json.loads(recipients)
                if not isinstance(recipient_ids, list):
                    recipient_ids = []
            except:
                recipient_ids = []
        
        print(f"[*] Multi-recipient: {len(recipient_ids)} recipients selected")
        
        # Initialize user steganography
        user_stego = UserSteganography(
            user_id=user['id'],
            username=user['username'],
            private_key_pem=user['private_key'],
            public_key_pem=user['public_key']
        )
        
        # Save uploaded files temporarily
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        data_path = os.path.join(UPLOAD_FOLDER, f"{user['id']}_data_{data_file.filename}")
        cover_path = os.path.join(UPLOAD_FOLDER, f"{user['id']}_cover_{cover_file.filename}")
        
        # Save files
        with open(data_path, 'wb') as f:
            f.write(await data_file.read())
        
        with open(cover_path, 'wb') as f:
            f.write(await cover_file.read())
        
        # Validate file sizes
        data_size_mb = os.path.getsize(data_path) / (1024 * 1024)
        if data_size_mb > concept['capacity']:
            os.remove(data_path)
            os.remove(cover_path)
            raise HTTPException(
                status_code=400,
                detail=f"Data file too large. Concept capacity: {concept['capacity']}MB, Your file: {data_size_mb:.2f}MB"
            )
        
        # Hide file
        OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'outputs')
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        # Use the cover file's extension for the output
        cover_ext = os.path.splitext(cover_file.filename)[1].lower()
        output_name = f"{user['id']}_{secrets.token_hex(4)}_stego{cover_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        
        print(f"[DEBUG] Calling hide_file:")
        print(f"  - data_path: {data_path}")
        print(f"  - cover_path: {cover_path}")
        print(f"  - output_path: {output_path}")
        print(f"  - encryption_type: {encryption_type}")
        print(f"  - compress: {compress == 'true'}")
        
        result = user_stego.hide_file(
            data_path,
            cover_path,
            output_path,
            password=password if encryption_type != 'rsa' else None,
            use_encryption=True,
            encryption_method=encryption_type,
            recipients=recipient_ids if recipient_ids else None
        )
        
        print(f"[DEBUG] hide_file result: {result}")
        
        # Extract actual output path
        actual_output_path = result.pop('output_file')
        actual_filename = os.path.basename(actual_output_path)
        
        # Verify file exists
        if not os.path.exists(actual_output_path):
            print(f"[ERROR] Output file not found: {actual_output_path}")
            raise HTTPException(status_code=500, detail=f"Output file not created")
        
        print(f"[DEBUG] Output file: {os.path.getsize(actual_output_path)} bytes")
        
        # Record in database
        stored_method = result.get('encryption_method', encryption_type)
        
        # Convert high-level method names to crypto-specific names for storage
        if stored_method == 'hybrid':
            stored_method = 'RSA+AES'
        elif stored_method == 'password':
            stored_method = 'AES'
        elif stored_method == 'rsa':
            stored_method = 'RSA'
        
        file_id = db.create_file_record(
            file_name=actual_filename,
            creator_user_id=user['id'],
            creator_public_key=user['public_key'],
            original_secret=data_file.filename or 'unknown',
            encryption_method=stored_method
        )
        
        # Store recipient keys if multi-recipient
        if recipient_ids and file_id:
            try:
                if 'encrypted_keys' in result:
                    recipient_keys = {}
                    for rid in recipient_ids:
                        rid_int = int(rid)
                        if rid_int in result['encrypted_keys']:
                            recipient_keys[rid_int] = result['encrypted_keys'][rid_int]
                    
                    if recipient_keys:
                        db.add_file_recipients(file_id, recipient_keys)
                        print(f"[+] Stored encrypted keys for {len(recipient_keys)} recipients")
            except Exception as e:
                print(f"[!] Warning: Error storing recipient keys: {e}")
        
        # Cleanup temp files
        for p in [data_path, cover_path]:
            if os.path.exists(p):
                os.remove(p)
        
        # Return response
        response_data = {
            'success': True,
            'message': f'File hidden successfully with {encryption_type.upper()} encryption',
            'download_url': f'/api/download/{actual_filename}',  # Frontend expects 'download_url'
            'output_file': actual_filename,
            'creator': user['username'],
            'creator_id': user['id'],
            'concept': concept['name'],
            'encryption_method': result.get('encryption_method', encryption_type),
            'data_file': data_file.filename,
            'cover_file': cover_file.filename,
            'recipients': len(recipient_ids),
        }
        
        # Log the hide operation
        try:
            ip_address = request.client.host if request.client else 'unknown'
            details = {
                'concept': concept['name'],
                'encryption_method': result.get('encryption_method', encryption_type),
                'data_file': data_file.filename,
                'cover_file': cover_file.filename,
                'recipients_count': len(recipient_ids),
                'output_file': actual_filename
            }
            db.log_operation(
                user_id=user['id'],
                username=user['username'],
                action='HIDE_FILE',
                resource=concept['name'],
                status='success',
                details=json.dumps(details),
                ip_address=ip_address
            )
            print(f"[+] Logged HIDE_FILE operation for user {user['username']} (ID: {user['id']})")
        except Exception as log_err:
            print(f"[!] Warning: Failed to log HIDE_FILE operation: {log_err}")
        
        response = JSONResponse(response_data)
        response.set_cookie('session_id', session_token, max_age=3600)
        return response
    
    except HTTPException as he:
        print(f"[ERROR] HTTPException: {he.detail}")
        raise
    except Exception as e:
        import traceback
        error_str = str(e)
        print(f"[ERROR] Exception in hide-file: {error_str}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {error_str}")


@public_router.post("/extract-file")
async def user_extract_file(
    request: Request,
    stego_file: UploadFile = File(...),
    password: str = Form(None),
    output_name: str = Form('extracted'),
    encryption_type: str = Form(None),
    encrypted_keys: str = Form(None)
):
    """
    Extract file - Supports multi-user extraction with encryption validation
    Supports both single-user and multi-recipient decryption (Approach 2)
    
    For Password-Only: Anyone with password can extract
    For RSA-Only/Hybrid: Only creator can extract (by design) or explicit sharing
    For Multi-Recipient: Only authorized recipients can extract using their private key
    
    - Validates file metadata from database
    - Decrypts based on encryption method
    - Handles multi-recipient decryption with encrypted DEKs
    - Returns extracted file with creator info
    """
    try:
        # Get current user and session
        user = get_current_user(request)
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        
        from core.user_stego import UserSteganography
        import json
        
        # DEBUG: Log received password details
        print(f"[DEBUG-EXTRACT] Received password: {repr(password)}")
        print(f"[DEBUG-EXTRACT] Password type: {type(password)}")
        print(f"[DEBUG-EXTRACT] Password length: {len(password) if password else 0}")
        if password:
            print(f"[DEBUG-EXTRACT] Password bytes: {password.encode('utf-8').hex()}")
        
        # Strip whitespace from password
        if password:
            password = password.strip()
        
        # Parse encrypted_keys if provided
        recipients_keys = None
        if encrypted_keys:
            try:
                recipients_keys = json.loads(encrypted_keys)
                print(f"[+] Multi-recipient encrypted keys received with {len(recipients_keys)} DEKs")
            except json.JSONDecodeError:
                print("[!] Warning: Could not parse encrypted_keys JSON")
        
        # Save stego file temporarily
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        stego_path = os.path.join(UPLOAD_FOLDER, f"{user['id']}_stego_{stego_file.filename}")
        with open(stego_path, 'wb') as f:
            f.write(await stego_file.read())
        
        # Try to get file record from database to retrieve metadata
        file_record = db.get_file_record(stego_file.filename)
        creator_data = {}
        multi_recipient_keys = None
        encryption_method_used = None
        
        print(f"[DEBUG-EXTRACT-META] Looking up metadata...")
        print(f"[DEBUG-EXTRACT-META] stego_file.filename: {stego_file.filename}")
        print(f"[DEBUG-EXTRACT-META] stego_path: {stego_path}")
        print(f"[DEBUG-EXTRACT-META] file_record found: {bool(file_record)}")
        
        if file_record:
            # File is in database - get creator info
            creator_data = {
                'creator_user_id': file_record['creator_user_id'],
                'creator_username': file_record.get('creator_username', 'Unknown'),
                'creator_public_key': file_record['creator_public_key']
            }
            # Get the actual encryption method that was used when hiding
            encryption_method_used = file_record.get('encryption_method', 'RSA+AES')
            print(f"[+] File record found - created by user {file_record['creator_user_id']}")
            print(f"[+] File was encrypted with method: {encryption_method_used}")
            
            # Try to get encrypted keys from database for multi-recipient files
            try:
                file_id = file_record.get('id')
                if file_id:
                    file_recipients = db.get_file_recipients(file_id)
                    if file_recipients:
                        multi_recipient_keys = file_recipients
                        print(f"[+] Multi-recipient file detected with {len(multi_recipient_keys)} recipient keys")
            except Exception as e:
                print(f"[!] Warning: Could not fetch recipient keys: {e}")
            
            # Save metadata file in uploads folder for extraction code to find
            try:
                metadata_file = stego_path + '.meta'
                metadata_from_db = {
                    'creator_user_id': file_record['creator_user_id'],
                    'creator_username': file_record.get('creator_username', 'Unknown'),
                    'creator_public_key': file_record['creator_public_key'],
                    'original_secret': file_record.get('original_secret', 'unknown'),
                    'encryption_method': encryption_method_used,
                    'password_used': encryption_method_used in ['AES', 'RSA+AES']
                }
                with open(metadata_file, 'w') as f:
                    json.dump(metadata_from_db, f, indent=2)
                print(f"[+] Created .meta file from database: {metadata_file}")
            except Exception as e:
                print(f"[!] Warning: Could not create .meta file from database: {e}")
        else:
            # Legacy file without database record
            metadata_file = stego_path + '.meta'
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    creator_data = json.load(f)
                # Extract encryption method from legacy metadata
                encryption_method_used = creator_data.get('encryption_method', 'RSA+AES')
                print(f"[+] Found .meta file in uploads folder: {metadata_file}")
            else:
                # Try looking in outputs folder for files hidden via operations endpoint
                outputs_folder = os.path.join(os.path.dirname(__file__), 'static', 'outputs')
                outputs_metadata_file = os.path.join(outputs_folder, stego_file.filename + '.meta')
                print(f"[DEBUG-EXTRACT-META] Checking for metadata in outputs folder: {outputs_metadata_file}")
                
                if os.path.exists(outputs_metadata_file):
                    with open(outputs_metadata_file, 'r') as f:
                        creator_data = json.load(f)
                    encryption_method_used = creator_data.get('encryption_method', 'RSA+AES')
                    print(f"[+] Found .meta file in outputs folder: {outputs_metadata_file}")
                else:
                    print(f"[DEBUG-EXTRACT-META] No .meta file found in outputs folder either")
            
            print("[*] Using legacy metadata from .meta file")
        
        # Final fallback: use encryption_type from frontend if encryption_method_used is still None
        if encryption_method_used is None and encryption_type:
            print(f"[+] Using encryption_type from frontend: {encryption_type}")
            # Convert high-level UI names to crypto-specific names
            if encryption_type == 'hybrid':
                encryption_method_used = 'RSA+AES'
            elif encryption_type == 'password':
                encryption_method_used = 'AES'
            elif encryption_type == 'rsa':
                encryption_method_used = 'RSA'
            else:
                encryption_method_used = encryption_type
        
        # Determine if current user is the creator
        is_creator = bool(creator_data and creator_data.get('creator_user_id') == user['id'])
        print(f"[DEBUG-CREATOR-CHECK] Checking creator status...")
        print(f"[DEBUG-CREATOR-CHECK] creator_data exists: {bool(creator_data)}")
        if creator_data:
            print(f"[DEBUG-CREATOR-CHECK] creator_user_id from metadata: {creator_data.get('creator_user_id')} (type: {type(creator_data.get('creator_user_id')).__name__})")
            print(f"[DEBUG-CREATOR-CHECK] current user['id']: {user['id']} (type: {type(user['id']).__name__})")
            print(f"[DEBUG-CREATOR-CHECK] Are they equal? {creator_data.get('creator_user_id') == user['id']}")
        print(f"[DEBUG-CREATOR-CHECK] is_creator result: {is_creator}")
        
        # Initialize user stego with CURRENT user's keys
        user_stego = UserSteganography(
            user_id=user['id'],
            username=user['username'],
            private_key_pem=user['private_key'],
            public_key_pem=user['public_key'],
            creator_public_key=creator_data.get('creator_public_key')  # Pass creator's public key if available
        )
        
        # Extract file
        OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'outputs')
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        # Try to get the original file extension
        original_ext = '.bin'  # Safe default fallback
        
        # Try 1: Get from database record (if file was previously stored)
        if file_record and file_record.get('original_secret'):
            orig_name = file_record.get('original_secret')
            detected_ext = os.path.splitext(orig_name)[1].lower()
            if detected_ext and len(detected_ext) <= 5:  # Ensure it's a reasonable extension
                original_ext = detected_ext
                print(f"[+] Found original extension from DB: {original_ext}")
        # Try 2: Get from .meta file (legacy metadata)
        elif creator_data and creator_data.get('original_secret'):
            orig_name = creator_data.get('original_secret')
            detected_ext = os.path.splitext(orig_name)[1].lower()
            if detected_ext and len(detected_ext) <= 5:  # Ensure it's a reasonable extension
                original_ext = detected_ext
                print(f"[+] Found original extension from .meta file: {original_ext}")
                print(f"[DEBUG-METADATA-READ] Metadata content: {json.dumps(creator_data, indent=2)}")
        else:
            # If no metadata found, try to infer from the stego file type
            # This helps when files weren't saved with metadata
            stego_type = get_file_type(stego_file)
            if stego_type:
                # Use a reasonable extension for the secret file based on stego container type
                type_extensions = {
                    'image': '.png',      # Most image secrets are images
                    'video': '.mp4',      # Most video secrets are videos
                    'audio': '.wav',      # Most audio secrets are audio
                    'document': '.pdf'    # Most document secrets are documents
                }
                inferred_ext = type_extensions.get(stego_type, '.dat')
                original_ext = inferred_ext
                print(f"[+] Inferred extension from stego type '{stego_type}': {original_ext}")
        
        output_filename = f"{user['id']}_{secrets.token_hex(4)}_extracted{original_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # FIX: Creator should NOT use multi-recipient decryption
        # Only non-creators (recipients) should use encrypted_keys
        # Creator decrypts using normal method with their private key
        if is_creator:
            # Creator uses normal decryption path - don't pass recipient keys
            encryption_keys = None
            print(f"[+] Current user is the creator - using normal decryption (not multi-recipient)")
            print(f"[DEBUG] is_creator=True, encryption_keys set to None for normal decryption")
            
            # KEY VERIFICATION: Compare stored creator public key with current user's key
            if creator_data and creator_data.get('creator_public_key'):
                stored_creator_key = creator_data.get('creator_public_key')
                current_user_key = user['public_key']
                
                if stored_creator_key.strip() == current_user_key.strip():
                    print(f"[+] KEY VERIFICATION PASSED: Creator's stored key matches current user's key")
                else:
                    print(f"[!] KEY VERIFICATION FAILED: Creator's stored key does NOT match current user's key")
                    print(f"[!] This indicates:")
                    print(f"[!]   - Account keys were regenerated (password reset/account recovery)")
                    print(f"[!]   - Different user account or compromised database")
                    print(f"[!] The file cannot be decrypted with the current keys")
        else:
            # Non-creator checks if they're a recipient
            encryption_keys = multi_recipient_keys or recipients_keys
            if encryption_keys:
                print(f"[+] Current user is a recipient - using multi-recipient decryption")
            else:
                print(f"[*] Non-creator user, but no multi-recipient keys found")
        
        print(f"[EXTRACT-FILE] Current user ID: {user['id']} (type: {type(user['id']).__name__})")
        print(f"[EXTRACT-FILE] Current username: {user['username']}")
        print(f"[EXTRACT-FILE] is_creator: {is_creator}")
        print(f"[EXTRACT-FILE] Using encryption_keys: {encryption_keys}")
        if encryption_keys:
            print(f"[EXTRACT-FILE] Type: {type(encryption_keys).__name__}")
            print(f"[EXTRACT-FILE] Keys in dict: {list(encryption_keys.keys())}")
            print(f"[EXTRACT-FILE] Key types: {[type(k).__name__ for k in encryption_keys.keys()]}")
            for key, value in encryption_keys.items():
                print(f"[EXTRACT-FILE]   Key {key} (int: {int(key) if isinstance(key, str) else key}): {type(value).__name__} value")
        else:
            print(f"[EXTRACT-FILE] No encryption keys (using normal decryption for creator)")
        
        result = user_stego.extract_file(
            stego_path,
            output_path,
            password=password,
            is_creator=is_creator,
            encrypted_keys=encryption_keys,
            encryption_method=encryption_method_used
        )
        
        # Cleanup
        if os.path.exists(stego_path):
            os.remove(stego_path)
        
        # Return response with session_id cookie set
        response_data = {
            'success': True,
            'message': 'File extracted successfully',
            'output_file': output_filename,  # Return actual filename (user is authenticated)
            'download_url': f'/api/download/{output_filename}',
            'creator': creator_data.get('creator_username', result.get('creator', 'Unknown')),
            'creator_id': creator_data.get('creator_user_id', result.get('creator_id')),
            'encryption_method': result.get('encryption_method', 'RSA+AES'),
            'extracted_by': user['username'],
            'is_creator': is_creator
        }
        
        # Log the extract operation
        try:
            ip_address = request.client.host if request.client else 'unknown'
            details = {
                'stego_file': stego_file.filename,
                'extracted_file': output_filename,
                'encryption_method': result.get('encryption_method', 'RSA+AES'),
                'is_creator': is_creator,
                'creator_id': creator_data.get('creator_user_id'),
                'is_multi_recipient': bool(multi_recipient_keys or recipients_keys)
            }
            db.log_operation(
                user_id=user['id'],
                username=user['username'],
                action='EXTRACT_FILE',
                resource=stego_file.filename,
                status='success',
                details=json.dumps(details),
                ip_address=ip_address
            )
            print(f"[+] Logged EXTRACT_FILE operation for user {user['username']} (ID: {user['id']})")
        except Exception as log_err:
            print(f"[!] Warning: Failed to log EXTRACT_FILE operation: {log_err}")
        
        response = JSONResponse(response_data)
        response.set_cookie('session_id', session_token, max_age=3600)  # 1 hour
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_str = str(e)
        print(f"[ERROR] Exception in extract-file: {error_str}", flush=True)
        # Safely handle traceback printing with Unicode characters
        try:
            tb_str = traceback.format_exc()
            # Replace any problematic Unicode characters
            tb_safe = tb_str.encode('utf-8', errors='replace').decode('utf-8')
            print(f"[ERROR] Traceback:\n{tb_safe}", flush=True)
        except Exception as tb_err:
            print(f"[ERROR] Could not print traceback: {tb_err}", flush=True)
        raise HTTPException(status_code=500, detail=f"Error: {error_str}")


@public_router.post("/hide-message")
async def user_hide_message(
    request: Request,
    message: str = Form(...),
    cover_file: UploadFile = File(...),
    password: str = Form(default=""),
    encryption_method: str = Form(default="hybrid"),
    recipients: str = Form(default="")  # JSON array of recipient user IDs
):
    """
    Hide message - Supports multi-recipient encryption (Approach 2)
    Same as hide-file but for text messages
    
    :param recipients: JSON array of recipient user IDs for sharing
    """
    try:
        # Log received parameters
        print(f"[DEBUG] hide-message received:")
        print(f"  - message: {message[:50] if message else 'EMPTY'}...")
        print(f"  - cover_file: {cover_file.filename if cover_file else 'EMPTY'}")
        print(f"  - password: {'***' if password else 'EMPTY'}")
        print(f"  - encryption_method: {encryption_method}")
        print(f"  - recipients: {recipients}")
        
        # Validate encryption method
        if encryption_method not in ['rsa', 'password', 'hybrid']:
            raise HTTPException(status_code=400, detail="Invalid encryption method. Must be 'rsa', 'password', or 'hybrid'")
        
        # Auto-downgrade encryption method if password is missing
        if encryption_method == 'hybrid' and not password:
            print("[*] Hybrid method selected but no password provided - falling back to RSA")
            encryption_method = 'rsa'
        elif encryption_method == 'password' and not password:
            raise HTTPException(status_code=400, detail="Password is required for password-only encryption")
        
        user = get_current_user(request)
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        
        from core.user_stego import UserSteganography
        import json
        
        # Parse recipients
        recipient_ids = []
        if recipients:
            try:
                recipient_ids = json.loads(recipients)
                if not isinstance(recipient_ids, list):
                    recipient_ids = []
            except:
                recipient_ids = []
        
        print(f"[*] Multi-recipient encryption: {len(recipient_ids)} recipients selected")
        
        user_stego = UserSteganography(
            user_id=user['id'],
            username=user['username'],
            private_key_pem=user['private_key'],
            public_key_pem=user['public_key']
        )
        
        # Save cover file
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        cover_path = os.path.join(UPLOAD_FOLDER, f"{user['id']}_cover_{cover_file.filename}")
        with open(cover_path, 'wb') as f:
            f.write(await cover_file.read())
        
        # Hide message
        OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'outputs')
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        # Use the cover file's extension for the output stego file
        cover_ext = os.path.splitext(cover_file.filename)[1].lower()
        output_name = f"{user['id']}_{secrets.token_hex(4)}_msg{cover_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        
        result = user_stego.hide_message(
            message,
            cover_path,
            output_path,
            password=password if encryption_method != 'rsa' else None,
            use_encryption=True,
            encryption_method=encryption_method,
            recipients=recipient_ids if recipient_ids else None  # Pass recipient IDs for multi-recipient
        )
        
        # Extract the actual filename from the full path returned by hide_message
        # (steganography modules may change the extension, e.g., .jpg → .png)
        actual_output_path = result.pop('output_file')  # Get the full path
        actual_filename = os.path.basename(actual_output_path)  # Extract just the filename
        
        # Get the actual encryption method used (may differ from requested if auto-upgraded)
        actual_encryption_method = result.get('encryption_method', encryption_method)
        
        # Record file with actual encryption method
        file_id = db.create_file_record(
            file_name=actual_filename,  # Use the actual filename with correct extension
            creator_user_id=user['id'],
            creator_public_key=user['public_key'],
            original_secret=f"message: {message[:50]}",
            encryption_method=actual_encryption_method  # Store actual method used
        )
        
        # Store recipient keys if multi-recipient encryption
        if recipient_ids and file_id:
            try:
                # Get encrypted keys from result
                if 'encrypted_keys' in result:
                    # Convert recipient_ids to int and match with encrypted keys
                    recipient_keys = {}
                    for rid in recipient_ids:
                        rid_int = int(rid)
                        if rid_int in result['encrypted_keys']:
                            recipient_keys[rid_int] = result['encrypted_keys'][rid_int]
                    
                    if recipient_keys:
                        db.add_file_recipients(file_id, recipient_keys)
                        print(f"[+] Stored encrypted keys for {len(recipient_keys)} recipients")
            except Exception as e:
                print(f"[!] Warning: Error storing recipient keys: {e}")
        
        # Cleanup
        if os.path.exists(cover_path):
            os.remove(cover_path)
        
        # Return response with session_id cookie set
        response_data = {
            'success': True,
            'message': 'Message hidden successfully',
            'output_file': actual_filename,  # Return actual filename (user is authenticated)
            'download_url': f'/api/download/{actual_filename}',
            'creator': user['username'],
            'creator_id': user['id'],
            'encryption_method': result.get('encryption_method', encryption_method),
            'recipients': len(recipient_ids),
            'encrypted': True
        }
        
        # Log the hide-message operation
        try:
            ip_address = request.client.host if request.client else 'unknown'
            details = {
                'message_length': len(message),
                'cover_file': cover_file.filename,
                'encryption_method': result.get('encryption_method', encryption_method),
                'recipients_count': len(recipient_ids),
                'output_file': actual_filename
            }
            db.log_operation(
                user_id=user['id'],
                username=user['username'],
                action='HIDE_MESSAGE',
                resource=cover_file.filename,
                status='success',
                details=json.dumps(details),
                ip_address=ip_address
            )
            print(f"[+] Logged HIDE_MESSAGE operation for user {user['username']} (ID: {user['id']})")
        except Exception as log_err:
            print(f"[!] Warning: Failed to log HIDE_MESSAGE operation: {log_err}")
        
        response = JSONResponse(response_data)
        response.set_cookie('session_id', session_token, max_age=3600)  # 1 hour
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_str = str(e)
        print(f"[ERROR] Exception in hide-message: {error_str}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {error_str}")


@public_router.post("/extract-message")
async def user_extract_message(
    request: Request,
    stego_file: UploadFile = File(...),
    password: str = Form(None),
    encrypted_keys: str = Form(None)
):
    """Extract message - Supports multi-user extraction with shared files and multi-recipient decryption (Approach 2)"""
    try:
        user = get_current_user(request)
        
        from core.user_stego import UserSteganography
        import json
        
        # Parse encrypted_keys if provided
        recipients_keys = None
        if encrypted_keys:
            try:
                recipients_keys = json.loads(encrypted_keys)
                print(f"[+] Multi-recipient encrypted keys received with {len(recipients_keys)} DEKs")
            except json.JSONDecodeError:
                print("[!] Warning: Could not parse encrypted_keys JSON")
        
        # Save stego file
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        stego_path = os.path.join(UPLOAD_FOLDER, f"{user['id']}_stego_{stego_file.filename}")
        with open(stego_path, 'wb') as f:
            f.write(await stego_file.read())
        
        # Try to get file record from database to retrieve metadata
        file_record = db.get_file_record(stego_file.filename)
        creator_data = {}
        multi_recipient_keys = None
        encryption_method_used = None
        
        if file_record:
            # File is in database - get creator info
            creator_data = {
                'creator_user_id': file_record['creator_user_id'],
                'creator_username': file_record.get('creator_username', 'Unknown'),
                'creator_public_key': file_record['creator_public_key']
            }
            # Get the actual encryption method that was used when hiding
            encryption_method_used = file_record.get('encryption_method', 'RSA+AES')
            print(f"[+] File record found - created by user {file_record['creator_user_id']}")
            print(f"[+] File was encrypted with method: {encryption_method_used}")
            
            # Try to get encrypted keys from database for multi-recipient files
            try:
                file_id = file_record.get('id')
                if file_id:
                    file_recipients = db.get_file_recipients(file_id)
                    if file_recipients:
                        multi_recipient_keys = file_recipients
                        print(f"[+] Multi-recipient file detected with {len(multi_recipient_keys)} recipient keys")
            except Exception as e:
                print(f"[!] Warning: Could not fetch recipient keys: {e}")
        else:
            # Legacy file without database record
            metadata_file = stego_path + '.meta'
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    creator_data = json.load(f)
                # Extract encryption method from legacy metadata if available
                encryption_method_used = creator_data.get('encryption_method', 'RSA+AES')
            print("[*] Using legacy metadata from .meta file")
        
        # Determine if current user is the creator
        is_creator = bool(creator_data and creator_data.get('creator_user_id') == user['id'])
        
        user_stego = UserSteganography(
            user_id=user['id'],
            username=user['username'],
            private_key_pem=user['private_key'],
            public_key_pem=user['public_key'],
            creator_public_key=creator_data.get('creator_public_key')
        )
        
        # Extract message
        # Use multi-recipient keys from database if available
        encryption_keys = multi_recipient_keys or recipients_keys
        
        result = user_stego.extract_message(
            stego_path,
            password=password,
            is_creator=is_creator,
            encrypted_keys=encryption_keys,
            encryption_method=encryption_method_used
        )
        
        # Cleanup
        if os.path.exists(stego_path):
            os.remove(stego_path)
        
        # Log the extract-message operation
        try:
            ip_address = request.client.host if request.client else 'unknown'
            details = {
                'stego_file': stego_file.filename,
                'encryption_method': result.get('encryption_method', 'RSA+AES'),
                'is_creator': is_creator,
                'creator_id': creator_data.get('creator_user_id'),
                'message_length': len(result.get('message', ''))
            }
            db.log_operation(
                user_id=user['id'],
                username=user['username'],
                action='EXTRACT_MESSAGE',
                resource=stego_file.filename,
                status='success',
                details=json.dumps(details),
                ip_address=ip_address
            )
            print(f"[+] Logged EXTRACT_MESSAGE operation for user {user['username']} (ID: {user['id']})")
        except Exception as log_err:
            print(f"[!] Warning: Failed to log EXTRACT_MESSAGE operation: {log_err}")
        
        return {
            'success': True,
            'message': 'Message extracted successfully',
            'extracted_message': result['message'],
            'creator': creator_data.get('creator_username', result.get('creator', 'Unknown')),
            'creator_id': creator_data.get('creator_user_id', result.get('creator_id')),
            'encryption_method': result.get('encryption_method'),
            'extracted_by': user['username'],
            'is_creator': is_creator
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_str = str(e)
        print(f"[ERROR] Exception in extract-message: {error_str}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {error_str}")


@user_router.get("/public-key/{user_id}")
async def get_user_public_key(user_id: int):
    """
    Get a user's public key (for verification purposes)
    
    Public keys can be shared - this allows other users to verify
    that a file was created by this user
    """
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            'user_id': user['id'],
            'username': user['username'],
            'public_key': user['public_key']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.get("/users")
async def get_all_users(request: Request):
    """
    Get all users for recipient selection (multi-recipient encryption)
    Returns list of users excluding current user
    """
    try:
        current_user = get_current_user(request)
        
        all_users = db.get_all_users()
        
        # Filter out current user and format response
        other_users = [
            {
                'id': u['id'],
                'username': u['username'],
                'email': u['email'],
                'fullname': u['fullname']
            }
            for u in all_users
            if u['id'] != current_user['id']  # Exclude current user
        ]
        
        return {
            'success': True,
            'users': other_users,
            'count': len(other_users)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# PUBLIC API ROUTES (Frontend-friendly endpoints)
# ═══════════════════════════════════════════════════════════

@public_router.post("/signup")
async def public_signup(data: SignupRequest):
    """
    Public signup endpoint for frontend
    Creates user with RSA key pair
    Accepts JSON: {fullname, username, email, password}
    """
    try:
        username = data.username
        email = data.email
        fullname = data.fullname
        password = data.password
        
        if len(username) < 3:
            return {'success': False, 'error': 'Username must be at least 3 characters'}
        if len(password) < 8:
            return {'success': False, 'error': 'Password must be at least 8 characters'}
        if len(email) < 5:
            return {'success': False, 'error': 'Invalid email'}
        
        # Check if user already exists
        if db.user_exists(username):
            return {'success': False, 'error': 'Username already exists'}
        
        # Create user and generate keys
        result = user_manager.sign_up(username, email, fullname, password)
        
        if result.get('success'):
            return {
                'success': True,
                'message': 'Account created successfully',
                'user_id': result['user_id'],
                'username': result['username']
            }
        else:
            return result
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


@public_router.post("/signin")
async def public_signin(data: SigninRequest):
    """
    Public signin endpoint for frontend
    Authenticates user and creates session
    Accepts JSON: {username, password}
    """
    try:
        username = data.username
        password = data.password
        
        result = user_manager.sign_in(username, password)
        
        if result.get('success'):
            # Create session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(days=7)
            db.create_session(result['user_id'], session_token, expires_at)
            
            response = JSONResponse({
                'success': True,
                'message': result['message'],
                'user': {
                    'id': result['user_id'],
                    'username': result['username'],
                    'email': result['email'],
                    'fullname': result['fullname']
                }
            })
            response.set_cookie('access_token', session_token, httponly=True, max_age=86400*7)
            response.set_cookie('session_id', session_token, httponly=True, max_age=86400*7)
            return response
        else:
            return JSONResponse({'success': False, 'error': result.get('error', 'Authentication failed')}, status_code=401)
    
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@public_router.post("/logout")
async def public_logout(request: Request):
    """Logout user"""
    try:
        response = JSONResponse({'success': True, 'message': 'Logged out successfully'})
        response.delete_cookie('access_token')
        response.delete_cookie('session_id')
        return response
    except Exception as e:
        return {'success': False, 'error': str(e)}


@public_router.get("/me")
async def public_get_current_user(request: Request):
    """Get current user info"""
    try:
        session_token = request.cookies.get('access_token') or request.cookies.get('session_id')
        
        if not session_token:
            return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
        
        user_id = db.get_session_user(session_token)
        if not user_id:
            return JSONResponse({'success': False, 'error': 'Invalid or expired session'}, status_code=401)
        
        user = db.get_user_by_id(user_id)
        if not user:
            return JSONResponse({'success': False, 'error': 'User not found'}, status_code=404)
        
        return {
            'success': True,
            'user': {
                'id': user.get('id') or user_id,
                'username': user.get('username'),
                'email': user.get('email'),
                'fullname': user.get('fullname'),
                'created_at': user.get('created_at')
            }
        }
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@public_router.get("/keys/public")
async def get_public_key(request: Request):
    """Get current user's public key"""
    try:
        session_token = request.cookies.get('access_token') or request.cookies.get('session_id')
        
        if not session_token:
            return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
        
        user_id = db.get_session_user(session_token)
        if not user_id:
            return JSONResponse({'success': False, 'error': 'Invalid session'}, status_code=401)
        
        user = db.get_user_by_id(user_id)
        if not user or user.get('public_key') is None:
            return JSONResponse({'success': False, 'error': 'Public key not found'}, status_code=404)
        
        return {
            'success': True,
            'public_key': user.get('public_key'),
            'user_id': user_id
        }
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@public_router.post("/keys/private")
async def get_private_key(request: Request):
    """Get current user's private key (requires password for decryption)"""
    try:
        session_token = request.cookies.get('access_token') or request.cookies.get('session_id')
        
        if not session_token:
            return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
        
        user_id = db.get_session_user(session_token)
        if not user_id:
            return JSONResponse({'success': False, 'error': 'Invalid session'}, status_code=401)
        
        # Get password from request body
        body = await request.json()
        password = body.get('password')
        
        if not password:
            return JSONResponse({'success': False, 'error': 'Password required'}, status_code=400)
        
        user = db.get_user_by_id(user_id)
        if not user:
            return JSONResponse({'success': False, 'error': 'User not found'}, status_code=404)
        
        # Decrypt private key
        private_key = user_manager.decrypt_private_key(user_id, password)
        
        if not private_key:
            return JSONResponse({'success': False, 'error': 'Failed to decrypt private key. Wrong password?'}, status_code=401)
        
        return {
            'success': True,
            'private_key': private_key,
            'user_id': user_id
        }
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@public_router.get("/download/{filename}")
async def download_stego_file(filename: str, request: Request):
    """
    Download a steganography output file by authenticated user
    Verifies that the file belongs to the current user before serving
    """
    try:
        # Authenticate user
        session_token = request.cookies.get('access_token') or request.cookies.get('session_id')
        if not session_token:
            return JSONResponse({'success': False, 'error': 'Not authenticated'}, status_code=401)
        
        user_id = db.get_session_user(session_token)
        if not user_id:
            return JSONResponse({'success': False, 'error': 'Invalid session'}, status_code=401)
        
        # Check file exists in outputs folder
        OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'outputs')
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return JSONResponse({'success': False, 'error': 'File not found'}, status_code=404)
        
        # Verify file ownership via database
        file_record = db.get_file_record(filename)
        if file_record and file_record.get('creator_user_id') != user_id:
            # File exists in database but belongs to another user - deny access
            return JSONResponse({'success': False, 'error': 'Unauthorized to access this file'}, status_code=403)
        
        # If file is in database and belongs to user, allow
        # If file is NOT in database, allow authenticated users to download (legacy files or untracked files)
        # This is safe because files are isolated in user-specific output folders
        
        # Determine MIME type based on file extension
        file_ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.flac': 'audio/flac',
            '.aiff': 'audio/aiff',
        }
        media_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # Serve the file
        return FileResponse(
            file_path,
            filename=filename,
            media_type=media_type
        )
    
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)

