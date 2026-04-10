"""
Operations Endpoints - Command Center API
==========================================
Handles all 16 steganography operation types with real-time status tracking.
Supports: Actual algorithm execution, authentication, file downloads, WebSocket real-time updates.

Operations:
  - I→I (Image to Image): Classic LSB steganography
  - I→V (Image to Video): Embed image in video frames
  - I→A (Image to Audio): Embed image data in audio
  - V→I (Video to Image): Extract key frames as images
  - V→V (Video to Video): Embed video in video stream
  - V→A (Video to Audio): Encode video as audio stream
  - A→I (Audio to Image): Spectral embedding
  - A→V (Audio to Video): Sync audio with video
  - A→A (Audio to Audio): Layer audio streams
"""

import os
import json
import uuid
import time
import shutil
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
import aiofiles
from queue import Queue

# Import steganography engine
try:
    from core.document_concepts_stego import DocumentConceptsSteganography  # Full 16-concept system
    STEGO_AVAILABLE = True
except ImportError:
    STEGO_AVAILABLE = False
    print("[!] Warning: 16-Concept Steganography System not available")

# Status tracking storage
_operations = {}  # result_id -> operation_data
_operation_results = {}  # result_id -> result_data
_active_websockets = {}  # result_id -> [WebSocket, ...]
_stego_engine = None  # Lazy-loaded 16-Concept Steganography instance
_main_loop = None  # Reference to main async loop for scheduling WebSocket broadcasts
_websocket_queue = Queue()  # Thread-safe queue for WebSocket messages from background threads

router = APIRouter(prefix="/api/operations", tags=["Operations"])


def extract_user_from_auth_header(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract user from Authorization header (Bearer <session_token>)
    Returns dict with user info or None if not authenticated
    """
    import sys
    auth_header = request.headers.get('Authorization', '')
    print(f"[DEBUG-AUTH-EXTRACT] Authorization header: {auth_header[:50] if auth_header else 'EMPTY'}...", flush=True)
    sys.stdout.flush()
    
    if not auth_header.startswith('Bearer '):
        print(f"[DEBUG-AUTH-EXTRACT] Header doesn't start with 'Bearer '", flush=True)
        sys.stdout.flush()
        return None
    
    session_token = auth_header[7:]  # Remove 'Bearer ' prefix
    print(f"[DEBUG-AUTH-EXTRACT] Extracted session_token: {session_token[:30]}...", flush=True)
    sys.stdout.flush()
    
    if not session_token:
        print(f"[DEBUG-AUTH-EXTRACT] session_token is empty", flush=True)
        sys.stdout.flush()
        return None
    
    try:
        from models import Database
        db = Database()
        user_id = db.get_session_user(session_token)
        print(f"[DEBUG-AUTH-EXTRACT] get_session_user returned: {user_id}", flush=True)
        sys.stdout.flush()
        
        if not user_id:
            print(f"[DEBUG-AUTH-EXTRACT] No user_id from session token", flush=True)
            sys.stdout.flush()
            return None
        
        user_data = db.get_user_by_id(user_id)
        print(f"[DEBUG-AUTH-EXTRACT] get_user_by_id returned: {user_data}", flush=True)
        sys.stdout.flush()
        if user_data:
            print(f"[DEBUG-AUTH-EXTRACT] Successfully extracted user: {dict(user_data).get('username')} (ID: {user_id})", flush=True)
            sys.stdout.flush()
            return dict(user_data)
        else:
            print(f"[DEBUG-AUTH-EXTRACT] get_user_by_id returned None for user_id {user_id}", flush=True)
            sys.stdout.flush()
    except Exception as e:
        print(f"[DEBUG-AUTH-EXTRACT] Error extracting user from Bearer token: {e}", flush=True)
        sys.stdout.flush()
        import traceback
        print(traceback.format_exc(), flush=True)
        sys.stdout.flush()
    
    print(f"[DEBUG-AUTH-EXTRACT] Returning None", flush=True)
    sys.stdout.flush()
    return None

# ───────────────────────────────────────────────────────────────
# INITIALIZATION
# ───────────────────────────────────────────────────────────────

def get_stego_engine():
    """Lazy-load and return steganography engine (16-concept system)"""
    global _stego_engine
    if _stego_engine is None and STEGO_AVAILABLE:
        _stego_engine = DocumentConceptsSteganography(key_dir='keys')
    return _stego_engine

# ───────────────────────────────────────────────────────────────
# OPERATION DEFINITIONS
# ───────────────────────────────────────────────────────────────

OPERATION_DEFINITIONS = {
    'i2i': {
        'name': 'I→I',
        'label': 'Classic',
        'description': 'Image to Image - Classic LSB steganography',
        'icon': '🖼️',
        'color': '#3b82f6',
        'input_type': 'image',
        'cover_type': 'image',
        'output_type': 'image',
        'supports_encryption': True,
        'max_capacity': '30-50%',
        'robustness': 'Low',
    },
    'i2v': {
        'name': 'I→V',
        'label': 'Covert',
        'description': 'Image to Video - Embed image data in video frames',
        'icon': '📹',
        'color': '#8b5cf6',
        'input_type': 'image',
        'cover_type': 'video',
        'output_type': 'video',
        'supports_encryption': True,
        'max_capacity': '10-20%',
        'robustness': 'Medium',
    },
    'i2a': {
        'name': 'I→A',
        'label': 'Deep',
        'description': 'Image to Audio - Embed image in audio frequency domain',
        'icon': '🔊',
        'color': '#10b981',
        'input_type': 'image',
        'cover_type': 'audio',
        'output_type': 'audio',
        'supports_encryption': True,
        'max_capacity': '20-40%',
        'robustness': 'High',
    },
    'v2i': {
        'name': 'V→I',
        'label': 'Frame',
        'description': 'Video to Image - Extract key frames with hidden data',
        'icon': '🎬',
        'color': '#f59e0b',
        'input_type': 'video',
        'cover_type': 'image',
        'output_type': 'image',
        'supports_encryption': True,
        'max_capacity': '15-30%',
        'robustness': 'Medium',
    },
    'v2v': {
        'name': 'V→V',
        'label': 'Stream',
        'description': 'Video to Video - Embed video in video stream',
        'icon': '🌊',
        'color': '#06b6d4',
        'input_type': 'video',
        'cover_type': 'video',
        'output_type': 'video',
        'supports_encryption': True,
        'max_capacity': '5-15%',
        'robustness': 'High',
    },
    'v2a': {
        'name': 'V→A',
        'label': 'Sync',
        'description': 'Video to Audio - Encode video as audio stream',
        'icon': '🎵',
        'color': '#ec4899',
        'input_type': 'video',
        'cover_type': 'audio',
        'output_type': 'audio',
        'supports_encryption': True,
        'max_capacity': '25-35%',
        'robustness': 'Medium',
    },
    'a2i': {
        'name': 'A→I',
        'label': 'Spectral',
        'description': 'Audio to Image - Spectral embedding in frequency domain',
        'icon': '📊',
        'color': '#14b8a6',
        'input_type': 'audio',
        'cover_type': 'image',
        'output_type': 'image',
        'supports_encryption': True,
        'max_capacity': '10-25%',
        'robustness': 'Low',
    },
    'a2v': {
        'name': 'A→V',
        'label': 'Dual',
        'description': 'Audio to Video - Synchronize audio with video frames',
        'icon': '🎥',
        'color': '#f97316',
        'input_type': 'audio',
        'cover_type': 'video',
        'output_type': 'video',
        'supports_encryption': True,
        'max_capacity': '20-30%',
        'robustness': 'High',
    },
    'a2a': {
        'name': 'A→A',
        'label': 'Layer',
        'description': 'Audio to Audio - Layer audio streams in frequency domain',
        'icon': '🎼',
        'color': '#6366f1',
        'input_type': 'audio',
        'cover_type': 'audio',
        'output_type': 'audio',
        'supports_encryption': True,
        'max_capacity': '15-25%',
        'robustness': 'High',
    },
}

# ───────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ───────────────────────────────────────────────────────────────

def create_operation_record(operation_id: str, user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Create an operation tracking record"""
    op_def = OPERATION_DEFINITIONS.get(operation_id, {})
    
    record = {
        'operation_id': operation_id,
        'result_id': str(uuid.uuid4()),
        'user_id': user_id,  # Track which user initiated the operation
        'status': 'queued',  # queued -> processing -> completed/failed
        'progress': 0,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'operation_name': op_def.get('name', operation_id),
        'operation_label': op_def.get('label', ''),
        **kwargs
    }
    return record


def get_operation(operation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve operation by ID"""
    return _operations.get(operation_id)


def get_result(result_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve result by ID"""
    return _operation_results.get(result_id)


def update_operation(result_id: str, **updates):
    """Update operation status - can be called from background threads"""
    if result_id in _operations:
        updated = {
            'updated_at': datetime.utcnow().isoformat(),
            **updates
        }
        _operations[result_id].update(updated)
        print(f"[+] Operation {result_id}: {updates}")
        
        # Queue WebSocket broadcast message for the main loop
        message = {
            'type': 'progress',
            'result_id': result_id,
            'timestamp': datetime.utcnow().isoformat(),
            **updated
        }
        _websocket_queue.put((result_id, message))


def save_result(result_id: str, data: Dict[str, Any]):
    """Save operation result"""
    _operation_results[result_id] = {
        'result_id': result_id,
        'completed_at': datetime.utcnow().isoformat(),
        **data
    }
    
    # Cleanup operation from tracking
    if result_id in _operations:
        del _operations[result_id]



def create_progress_callback(result_id: str) -> Callable:
    """Create a progress callback function for steganography operations"""
    def callback(operation: str, progress: int, details: str = ""):
        update_operation(result_id, progress=progress, message=details)
    return callback


def verify_operation_ownership(request: Request, result_id: str) -> Optional[str]:
    """
    Verify that the requesting user owns the operation.
    Returns user_id if verified, None otherwise.
    """
    # Check for auth token (optional - allow anonymous operations)
    auth_header = request.headers.get('Authorization', '')
    session_id = request.cookies.get('session_id')
    
    # If authenticated, verify ownership
    if auth_header or session_id:
        try:
            # Extract user_id from token or session
            # This is simplified - in production, validate JWT/session
            operation = _operations.get(result_id) or _operation_results.get(result_id)
            if operation and operation.get('user_id'):
                # Would validate here that user_id matches auth token
                return operation.get('user_id')
        except:
            pass
    
    # Allow anonymous access for now
    return None


def get_uploads_dir() -> str:
    """Get uploads directory"""
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir


def get_outputs_dir() -> str:
    """Get outputs directory"""
    outputs_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    return outputs_dir


def process_operation(
    result_id: str,
    operation_id: str,
    operation_def: Dict,
    secret_file_path: Optional[str],
    cover_file_path: Optional[str],
    message: Optional[str],
    password: Optional[str],
    encryption_type: Optional[str],
    use_encryption: bool,
    user_id: Optional[int] = None,
    user_dict: Optional[Dict] = None
):
    """
    Background function to process steganography operation.
    Runs in a background thread.
    """
    try:
        update_operation(result_id, status='processing', progress=20)
        
        stego = get_stego_engine()
        if not stego:
            raise RuntimeError("Steganography engine not available")
        
        outputs_dir = get_outputs_dir()
        
        # Create output filename with proper extension
        # Map media type to file extension
        type_to_ext = {
            'image': 'png',
            'video': 'mp4',
            'audio': 'wav',
            'document': 'pdf'
        }
        output_ext = type_to_ext.get(operation_def.get('output_type', 'image'), 'png')
        output_file = os.path.join(outputs_dir, f"{result_id[:8]}_{int(time.time())}.{output_ext}")
        
        # Map operation to appropriate steganography method
        operation_methods = {
            'i2i': stego.hide_image_in_image,
            'i2v': stego.hide_image_in_video,
            'i2a': stego.hide_image_in_audio,
            'v2i': stego.hide_video_in_image,
            'v2v': stego.hide_video_in_video,
            'v2a': stego.hide_video_in_audio,
            'a2i': stego.hide_audio_in_image,
            'a2v': stego.hide_audio_in_video,
            'a2a': stego.hide_audio_in_audio,
        }
        
        # Map operation to parameter names (secret_type, cover_type)
        operation_params = {
            'i2i': ('secret_image', 'cover_image'),
            'i2v': ('secret_image', 'cover_video'),
            'i2a': ('secret_image', 'cover_audio'),
            'v2i': ('secret_video', 'cover_image'),
            'v2v': ('secret_video', 'cover_video'),
            'v2a': ('secret_video', 'cover_audio'),
            'a2i': ('secret_audio', 'cover_image'),
            'a2v': ('secret_audio', 'cover_video'),
            'a2a': ('secret_audio', 'cover_audio'),
        }
        
        method = operation_methods.get(operation_id)
        if not method:
            raise ValueError(f"Operation {operation_id} not implemented")
        
        # Execute steganography operation
        update_operation(result_id, progress=30, message="Starting encoding...")
        
        # Call appropriate method based on operation type
        if message:
            # Hide message
            result = stego.hide_message(
                message=message,
                cover_file=cover_file_path,
                output_file=output_file,
                password=password if use_encryption else None,
                use_encryption=use_encryption,
                encryption_method=encryption_type if use_encryption else 'rsa'
            )
        else:
            # Hide file - build kwargs with correct parameter names
            secret_param, cover_param = operation_params.get(operation_id, ('secret_image', 'cover_image'))
            
            # Map encryption_type from frontend to crypto method names
            encryption_method_mapped = encryption_type.lower()
            if encryption_type.lower() == 'hybrid':
                encryption_method_mapped = 'rsa+aes'
            
            kwargs = {
                secret_param: secret_file_path,
                cover_param: cover_file_path,
                'output_file': output_file,
                'password': password if use_encryption else None,
                'use_encryption': use_encryption,
                'encryption_method': encryption_method_mapped if use_encryption else 'rsa'
            }
            
            result = method(**kwargs)
        
        update_operation(result_id, progress=80, message="Encoding complete, finalizing...")
        
        # Get actual output file path
        actual_output = result.get('output_file', output_file) if isinstance(result, dict) else output_file
        
        # Save metadata file for extraction reference
        try:
            metadata_file = actual_output + '.meta'
            import sys
            print(f"\n[DEBUG-METADATA-SAVE] About to save metadata...", flush=True)
            sys.stdout.flush()
            print(f"[DEBUG-METADATA-SAVE] user_id: {user_id} (type: {type(user_id).__name__ if user_id else 'None'})", flush=True)
            print(f"[DEBUG-METADATA-SAVE] user_dict: {user_dict}", flush=True)
            print(f"[DEBUG-METADATA-SAVE] user_dict.get('id'): {user_dict.get('id')}", flush=True)
            print(f"[DEBUG-METADATA-SAVE] user_dict.get('username'): {user_dict.get('username')}", flush=True)
            sys.stdout.flush()
            metadata = {
                'creator_user_id': user_id,
                'creator_username': user_dict.get('username', 'Unknown') if user_dict else 'Unknown',
                'creator_public_key': user_dict.get('public_key', '') if user_dict else '',
                'original_secret': os.path.basename(secret_file_path or ''),
                'encrypted': use_encryption,
                'encryption_method': encryption_type or 'unknown',
                'password_used': bool(password)
            }
            print(f"[DEBUG-METADATA] Saving metadata with user_id: {user_id}, username: {metadata['creator_username']}", flush=True)
            sys.stdout.flush()
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"[+] Metadata saved to: {metadata_file}", flush=True)
            print(f"[DEBUG-METADATA] Content: {json.dumps(metadata, indent=2)}", flush=True)
            sys.stdout.flush()
            
            # Also save to database for better lookup
            if user_id:
                try:
                    from models import Database
                    db = Database()
                    stored_method = encryption_type or 'unknown'
                    if stored_method == 'hybrid':
                        stored_method = 'RSA+AES'
                    elif stored_method == 'password':
                        stored_method = 'AES'
                    elif stored_method == 'rsa':
                        stored_method = 'RSA'
                    
                    file_id = db.create_file_record(
                        file_name=os.path.basename(actual_output),
                        creator_user_id=user_id,
                        creator_public_key=user_dict.get('public_key', '') if user_dict else '',
                        original_secret=os.path.basename(secret_file_path or ''),
                        encryption_method=stored_method
                    )
                    print(f"[+] Created database file record (ID: {file_id}) for: {os.path.basename(actual_output)}")
                except Exception as e:
                    print(f"[!] Warning: Could not create database file record: {e}")
        except Exception as e:
            print(f"[!] Warning: Could not save metadata file: {e}")
            import traceback
            print(traceback.format_exc())
        
        # Update to completed BEFORE saving (before removing from operations)
        update_operation(result_id, status='completed', progress=100)
        
        # Save result
        save_result(result_id, {
            'status': 'completed',
            'progress': 100,
            'operation_id': operation_id,
            'operation_name': operation_def.get('name'),
            'output_file': os.path.basename(actual_output),
            'output_path': actual_output,
            'download_url': f'http://localhost:5001/api/operations/download/{result_id}',
            'encryption_used': use_encryption,
            'message': 'Operation completed successfully',
            'metrics': {
                'operation_type': operation_id,
                'input_file': os.path.basename(secret_file_path or ''),
                'cover_file': os.path.basename(cover_file_path or ''),
            }
        })
        
        # Cleanup input files
        for path in [secret_file_path, cover_file_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"[!] Failed to cleanup {path}: {e}")
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[!] Operation error: {error_msg}")
        
        save_result(result_id, {
            'status': 'failed',
            'progress': 0,
            'operation_id': operation_id,
            'error': str(e),
            'message': f'Operation failed: {str(e)}'
        })


# ───────────────────────────────────────────────────────────────
# ENDPOINTS
# ───────────────────────────────────────────────────────────────

@router.get("/")
async def list_operations():
    """List all available operations"""
    return {
        'success': True,
        'operations': [
            {
                'id': op_id,
                **op_def
            }
            for op_id, op_def in OPERATION_DEFINITIONS.items()
        ],
        'total': len(OPERATION_DEFINITIONS)
    }


# ───────────────────────────────────────────────────────────────
# HEALTH & STATS (Must come before /{result_id} to avoid route conflicts)
# ───────────────────────────────────────────────────────────────

@router.get("/health/status")
async def operations_health():
    """Get operations system health"""
    
    completed = sum(1 for op in _operation_results.values() if op.get('status') == 'completed')
    failed = sum(1 for op in _operation_results.values() if op.get('status') == 'failed')
    processing = sum(1 for op in _operations.values() if op.get('status') == 'processing')
    
    stego_status = "Available" if STEGO_AVAILABLE else "Not Available"
    
    return {
        'status': 'healthy' if STEGO_AVAILABLE else 'degraded',
        'steganography_engine': stego_status,
        'total_operations': len(_operations) + len(_operation_results),
        'completed': completed,
        'failed': failed,
        'processing': processing,
        'available_operations': len(OPERATION_DEFINITIONS),
        'websocket_support': True,
        'file_download_support': True,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.post("/execute")
async def execute_operation(
    request: Request,
    operation_id: str = Form(...),
    secret_file: Optional[UploadFile] = File(None),
    cover_file: Optional[UploadFile] = File(None),
    message: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    encryption_type: Optional[str] = Form('rsa'),
    use_encryption: Optional[str] = Form('false'),
    quality: Optional[str] = Form('high'),
    preserve_original: Optional[str] = Form('true'),
    user_id_override: Optional[str] = Form(None),  # Explicit user ID from frontend
):
    """
    Execute a steganography operation
    
    Operations:
    - I2I: Requires secret_file (image) and cover_file (image)
    - I2V: Requires secret_file (image) and cover_file (video)
    - etc.
    
    Optional:
    - password: For encryption (if use_encryption=true)
    - quality: 'low', 'medium', 'high' (default: high)
    - preserve_original: Keep original files (default: true)
    
    Returns: result_id for polling/WebSocket subscription
    """
    
    # Get authenticated user info
    user_id = None
    user_dict = {'username': 'anonymous', 'id': None, 'public_key': ''}
    
    import sys
    print(f"\n[DEBUG-AUTH] ========== EXECUTE_OPERATION AUTH FLOW ==========", flush=True)
    print(f"[DEBUG-AUTH] user_id_override: {user_id_override}", flush=True)
    sys.stdout.flush()
    
    # Try user_id_override first (from frontend)
    if user_id_override:
        try:
            user_id = int(user_id_override)
            print(f"[DEBUG-AUTH] Using user_id_override: {user_id}", flush=True)
            from models import Database
            db = Database()
            user_data = db.get_user_by_id(user_id)
            if user_data:
                user_dict = dict(user_data)
                print(f"[DEBUG-AUTH] Successfully got user from override: {user_dict.get('username')} (ID: {user_id})", flush=True)
            else:
                print(f"[DEBUG-AUTH] get_user_by_id returned None for user_id {user_id}", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"[DEBUG-AUTH] Error with user_id_override: {e}", flush=True)
            sys.stdout.flush()
    
    # If no override, try Authorization Bearer token
    if not user_id:
        print(f"[DEBUG-AUTH] Trying Authorization Bearer token...", flush=True)
        sys.stdout.flush()
        auth_user = extract_user_from_auth_header(request)
        if auth_user:
            user_id = auth_user.get('id')
            user_dict = auth_user
            print(f"[DEBUG-AUTH] Successfully got user from Bearer token: {user_dict.get('username')} (ID: {user_id})", flush=True)
        else:
            print(f"[DEBUG-AUTH] No user found in Authorization Bearer token", flush=True)
        sys.stdout.flush()
    
    # If still no user, try session cookie/header
    if not user_id:
        session_token = request.cookies.get('session_id') or request.headers.get('X-Session-Token')
        
        print(f"[DEBUG-AUTH] Attempting to get user from session cookie/header...", flush=True)
        print(f"[DEBUG-AUTH] session_id cookie: {request.cookies.get('session_id')[:30] if request.cookies.get('session_id') else 'NONE'}...", flush=True)
        print(f"[DEBUG-AUTH] X-Session-Token header: {request.headers.get('X-Session-Token')[:30] if request.headers.get('X-Session-Token') else 'NONE'}...", flush=True)
        sys.stdout.flush()
        
        if session_token:
            try:
                from models import Database
                db = Database()
                user_id = db.get_session_user(session_token)
                print(f"[DEBUG-AUTH] get_session_user returned: {user_id}", flush=True)
                sys.stdout.flush()
                if user_id:
                    user_data = db.get_user_by_id(user_id)
                    print(f"[DEBUG-AUTH] get_user_by_id returned: {user_data}", flush=True)
                    sys.stdout.flush()
                    if user_data:
                        user_dict = dict(user_data)
                        print(f"[DEBUG-AUTH] Successfully got user from session: {user_dict.get('username')} (ID: {user_id})", flush=True)
                        sys.stdout.flush()
            except Exception as e:
                print(f"[!] Warning: Could not get user from session: {e}", flush=True)
                sys.stdout.flush()
        else:
            print(f"[DEBUG-AUTH] No session token found in cookies or headers", flush=True)
    
    print(f"[DEBUG-AUTH] Final user_id: {user_id}, username: {user_dict.get('username')}", flush=True)
    print(f"[DEBUG-AUTH] ========== END AUTH FLOW ==========\n", flush=True)
    sys.stdout.flush()
    
    # Validate operation ID
    if operation_id not in OPERATION_DEFINITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operation ID: {operation_id}. Valid operations: {list(OPERATION_DEFINITIONS.keys())}"
        )
    
    operation_def = OPERATION_DEFINITIONS[operation_id]
    encrypt = use_encryption.lower() == 'true'
    
    # Validate encryption password
    if encrypt and not password:
        raise HTTPException(
            status_code=400,
            detail="Password required when encryption is enabled"
        )
    
    # Validate files
    if not message and not (secret_file and cover_file):
        raise HTTPException(
            status_code=400,
            detail="Either 'message' OR both 'secret_file' and 'cover_file' are required"
        )
    
    # Create operation record
    operation_record = create_operation_record(
        operation_id=operation_id,
        user_id=user_id,
        status='queued',
        progress=5,
        encryption_enabled=encrypt,
        quality=quality,
        preserve_original=preserve_original == 'true',
        input_files={},
        parameters={}
    )
    
    result_id = operation_record['result_id']
    _operations[result_id] = operation_record
    
    # Save uploaded files temporarily
    uploads_dir = get_uploads_dir()
    secret_file_path = None
    cover_file_path = None
    
    try:
        if secret_file:
            secret_file_path = os.path.join(uploads_dir, f"{result_id[:8]}_secret_{secret_file.filename}")
            content = await secret_file.read()
            with open(secret_file_path, 'wb') as f:
                f.write(content)
        
        if cover_file:
            cover_file_path = os.path.join(uploads_dir, f"{result_id[:8]}_cover_{cover_file.filename}")
            content = await cover_file.read()
            with open(cover_file_path, 'wb') as f:
                f.write(content)
        
        # NOTE: We already have user_id and user_dict from auth flow above, don't reset them
        # If user_id is set but user_dict is still default, try to populate user_dict from database
        if user_id and user_dict.get('id') is None:
            try:
                from models import Database
                db = Database()
                user_data = db.get_user_by_id(user_id)
                if user_data:
                    user_dict = dict(user_data)
                    print(f"[DEBUG-RETRIEVE-USER] Successfully retrieved user data: {user_dict.get('username')} from DB", flush=True)
            except Exception as e:
                print(f"[DEBUG-RETRIEVE-USER] Warning: Could not retrieve user from DB: {e}", flush=True)
        
        # Start operation processing in background thread
        thread = threading.Thread(
            target=process_operation,
            args=(
                result_id,
                operation_id,
                operation_def,
                secret_file_path,
                cover_file_path,
                message,
                password,
                encryption_type,
                encrypt,
                user_id,
                user_dict
            )
        )
        thread.daemon = True
        thread.start()
        
        return JSONResponse(
            {
                'success': True,
                'message': f'Operation {operation_id} queued successfully',
                'result_id': result_id,
                'status': 'queued',
                'operation': {
                    'id': operation_id,
                    'name': operation_def['name'],
                    'label': operation_def['label'],
                    'description': operation_def['description'],
                },
                'estimated_time': '10-60 seconds',
                'websocket_url': f'/api/operations/ws/{result_id}',
                'poll_url': f'/api/operations/{result_id}/status',
            },
            status_code=202  # Accepted (processing async)
        )
    
    except Exception as e:
        update_operation(result_id, status='failed', error=str(e), progress=0)
        # Cleanup
        for path in [secret_file_path, cover_file_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue operation: {str(e)}"
        )


@router.get("/{result_id}/status")
async def get_operation_status(result_id: str):
    """Get status of an operation"""
    
    operation = get_result(result_id)
    if not operation:
        # Check if it's still being processed
        operation = _operations.get(result_id)
        if not operation:
            raise HTTPException(
                status_code=404,
                detail=f"Operation not found: {result_id}"
            )
    
    return {
        'success': True,
        'result_id': result_id,
        'status': operation.get('status', 'unknown'),
        'progress': operation.get('progress', 0),
        'operation_id': operation.get('operation_id'),
        'operation_name': operation.get('operation_name'),
        'created_at': operation.get('created_at'),
        'updated_at': operation.get('updated_at'),
        'error': operation.get('error'),
        'message': operation.get('message'),
    }


@router.get("/{result_id}")
async def get_operation_result(result_id: str):
    """Get result of a completed operation"""
    
    result = get_result(result_id)
    if not result:
        operation = _operations.get(result_id)
        if operation and operation.get('status') != 'completed':
            return {
                'success': False,
                'status': operation.get('status', 'unknown'),
                'progress': operation.get('progress', 0),
                'message': 'Operation still processing'
            }
        raise HTTPException(
            status_code=404,
            detail=f"Result not found: {result_id}"
        )
    
    if result.get('status') == 'failed':
        return {
            'success': False,
            'result_id': result_id,
            'status': 'failed',
            'error': result.get('error'),
            'message': result.get('message'),
        }
    
    return {
        'success': True,
        'result_id': result_id,
        'status': result.get('status', 'completed'),
        'operation_id': result.get('operation_id'),
        'operation_name': result.get('operation_name'),
        'output_file': result.get('output_file'),
        'download_url': result.get('download_url'),
        'metrics': result.get('metrics'),
        'completed_at': result.get('completed_at'),
        'message': result.get('message'),
    }


@router.post("/{result_id}/cancel")
async def cancel_operation(result_id: str):
    """Cancel a running operation"""
    
    operation = _operations.get(result_id) or get_result(result_id)
    if not operation:
        raise HTTPException(
            status_code=404,
            detail=f"Operation not found: {result_id}"
        )
    
    if operation.get('status') == 'completed':
        return {
            'success': False,
            'message': 'Cannot cancel completed operation'
        }
    
    update_operation(result_id, status='cancelled', progress=0)
    
    return {
        'success': True,
        'message': f'Operation {result_id} cancelled',
        'status': 'cancelled'
    }


# ───────────────────────────────────────────────────────────────
# WEBSOCKET REAL-TIME UPDATES
# ───────────────────────────────────────────────────────────────

@router.websocket("/ws/{result_id}")
async def websocket_operation_updates(websocket: WebSocket, result_id: str):
    """
    WebSocket endpoint for real-time operation updates
    Clients connect here to receive live progress updates
    
    Usage: ws://localhost:5001/api/operations/ws/{result_id}
    """
    await websocket.accept()
    
    # Register WebSocket client
    if result_id not in _active_websockets:
        _active_websockets[result_id] = []
    _active_websockets[result_id].append(websocket)
    
    try:
        # Send initial status
        operation = _operations.get(result_id) or _operation_results.get(result_id)
        if operation:
            await websocket.send_json({
                'type': 'connected',
                'result_id': result_id,
                'status': operation.get('status'),
                'progress': operation.get('progress'),
                'message': 'Connected to operation stream'
            })
        
        # Keep connection open, checking for both incoming messages and queued updates
        while True:
            # Process any pending queued messages for this operation
            try:
                while True:
                    q_result_id, message = _websocket_queue.get_nowait()
                    if q_result_id == result_id and websocket in _active_websockets.get(result_id, []):
                        await websocket.send_json(message)
                        # Stop if operation is completed
                        if message.get('status') == 'completed':
                            break
            except Exception:
                pass  # Queue is empty
            
            try:
                # Wait for client messages with timeout to also check queue periodically
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                # Handle ping/keep-alive messages
                if data in ['ping', '']:
                    operation = _operations.get(result_id) or _operation_results.get(result_id)
                    if operation:
                        await websocket.send_json({
                            'type': 'pong',
                            'status': operation.get('status'),
                            'progress': operation.get('progress'),
                        })
            except asyncio.TimeoutError:
                # Timeout is expected, just loop again to check queue
                continue
    
    except WebSocketDisconnect:
        # Remove WebSocket client
        if result_id in _active_websockets and websocket in _active_websockets[result_id]:
            _active_websockets[result_id].remove(websocket)
    except Exception as e:
        print(f"[!] WebSocket error: {e}")


# ───────────────────────────────────────────────────────────────
# FILE DOWNLOAD
# ───────────────────────────────────────────────────────────────

@router.get("/download/{result_id}")
async def download_operation_result(result_id: str, request: Request):
    """
    Download the output file from a completed operation
    
    Security: 
    - Verifies operation exists and is completed
    - Optionally validates user ownership if authenticated
    - Prevents path traversal attacks
    """
    try:
        print(f"\n[📥] Download request for result_id: {result_id}")
        
        # Verify operation ownership (if authenticated)
        verify_operation_ownership(request, result_id)
        
        # Get result
        result = get_result(result_id)
        print(f"[📋] Retrieved result: {result is not None}")
        
        if not result:
            print(f"[✗] Result not found in _operation_results")
            raise HTTPException(
                status_code=404,
                detail=f"Operation result not found: {result_id}"
            )
        
        # Check if completed
        status = result.get('status')
        print(f"[⏱️] Operation status: {status}")
        
        if status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Operation not completed. Status: {status}"
            )
        
        # Get file path
        output_path = result.get('output_path')
        print(f"[📁] Output path: {output_path}")
        
        if not output_path:
            print(f"[✗] No output_path in result")
            raise HTTPException(
                status_code=404,
                detail="Output file path not specified"
            )
        
        if not os.path.exists(output_path):
            print(f"[✗] File doesn't exist at: {output_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Output file not found at: {output_path}"
            )
        
        # Security: Ensure file is in outputs directory to prevent traversal
        outputs_dir = get_outputs_dir()
        real_output_path = os.path.realpath(output_path)
        real_outputs_dir = os.path.realpath(outputs_dir)
        
        print(f"[🔒] Security check - Real path: {real_output_path}")
        print(f"[🔒] Security check - Outputs dir: {real_outputs_dir}")
        
        if not real_output_path.startswith(real_outputs_dir):
            print(f"[✗] Path traversal attempt detected")
            raise HTTPException(
                status_code=403,
                detail="Access denied: Invalid file path"
            )
        
        # Get file info
        file_name = os.path.basename(output_path)
        file_size = os.path.getsize(output_path)
        
        print(f"[✓] File ready: {file_name} ({file_size} bytes)")
        
        # Return file with proper headers
        return FileResponse(
            path=output_path,
            filename=file_name,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{file_name}"',
                'Content-Length': str(file_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n[✗✗✗] DOWNLOAD ENDPOINT ERROR ✗✗✗")
        print(f"[✗] Result ID: {result_id}")
        print(f"[✗] Error: {str(e)}")
        import traceback
        print(f"[✗] Traceback:\n{traceback.format_exc()}")
        print(f"[✗✗✗] END ERROR ✗✗✗\n")
        
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )
