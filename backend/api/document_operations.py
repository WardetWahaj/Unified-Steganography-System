"""
Document Operations Endpoints - Command Center API
===================================================
Handles all 7 document steganography operations with real-time status tracking.

Document Concepts (10-16):
  - I→D (Image to Document): Concept 10
  - D→I (Document to Image): Concept 11  
  - V→D (Video to Document): Concept 12
  - D→V (Document to Video): Concept 13
  - A→D (Audio to Document): Concept 14
  - D→A (Document to Audio): Concept 15
  - D↔D (Document to Document): Concept 16
"""

import os
import uuid
import time
import shutil
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket
from fastapi.responses import FileResponse, JSONResponse
import aiofiles

# Import steganography engine
try:
    from core.document_concepts_stego import DocumentConceptsSteganography
    DOC_STEGO_AVAILABLE = True
except ImportError:
    DOC_STEGO_AVAILABLE = False
    print("[!] Warning: DocumentConceptsSteganography not available")

# Status tracking storage
_doc_operations = {}  # result_id -> operation_data
_doc_results = {}  # result_id -> result_data
_doc_stego_engine = None  # Lazy-loaded DocumentConceptsSteganography instance

router = APIRouter(prefix="/api/document-ops", tags=["Document Operations"])

# ───────────────────────────────────────────────────────────────
# INITIALIZATION
# ───────────────────────────────────────────────────────────────

def get_doc_stego_engine():
    """Lazy-load and return document steganography engine"""
    global _doc_stego_engine
    if _doc_stego_engine is None and DOC_STEGO_AVAILABLE:
        _doc_stego_engine = DocumentConceptsSteganography(key_dir='keys')
    return _doc_stego_engine

# ───────────────────────────────────────────────────────────────
# OPERATION DEFINITIONS
# ───────────────────────────────────────────────────────────────

DOCUMENT_OPERATION_DEFINITIONS = {
    'i2d': {
        'name': 'I→D',
        'label': 'Image→Doc',
        'description': 'Image to Document - Hide image in text document',
        'icon': '📄',
        'color': '#6b7280',
        'input_type': 'image',
        'cover_type': 'document',
        'output_type': 'document',
        'supports_encryption': True,
        'max_capacity': '5-15%',
        'robustness': 'Very High',
    },
    'd2i': {
        'name': 'D→I',
        'label': 'Doc→Image',
        'description': 'Document to Image - Hide document in image pixels',
        'icon': '🖼️',
        'color': '#8b5cf6',
        'input_type': 'document',
        'cover_type': 'image',
        'output_type': 'image',
        'supports_encryption': True,
        'max_capacity': '30-50%',
        'robustness': 'Medium',
    },
    'v2d': {
        'name': 'V→D',
        'label': 'Video→Doc',
        'description': 'Video to Document - Encode video in document',
        'icon': '🎬',
        'color': '#f59e0b',
        'input_type': 'video',
        'cover_type': 'document',
        'output_type': 'document',
        'supports_encryption': True,
        'max_capacity': '1-5%',
        'robustness': 'Very High',
    },
    'd2v': {
        'name': 'D→V',
        'label': 'Doc→Video',
        'description': 'Document to Video - Hide in video frames',
        'icon': '📹',
        'color': '#06b6d4',
        'input_type': 'document',
        'cover_type': 'video',
        'output_type': 'video',
        'supports_encryption': True,
        'max_capacity': '10-20%',
        'robustness': 'High',
    },
    'a2d': {
        'name': 'A→D',
        'label': 'Audio→Doc',
        'description': 'Audio to Document - Encode audio in doc',
        'icon': '🔊',
        'color': '#10b981',
        'input_type': 'audio',
        'cover_type': 'document',
        'output_type': 'document',
        'supports_encryption': True,
        'max_capacity': '2-8%',
        'robustness': 'Very High',
    },
    'd2a': {
        'name': 'D→A',
        'label': 'Doc→Audio',
        'description': 'Document to Audio - Hide in audio samples',
        'icon': '🎵',
        'color': '#ec4899',
        'input_type': 'document',
        'cover_type': 'audio',
        'output_type': 'audio',
        'supports_encryption': True,
        'max_capacity': '20-40%',
        'robustness': 'High',
    },
    'd2d': {
        'name': 'D↔D',
        'label': 'Doc↔Doc',
        'description': 'Document to Document - Hide in text/metadata',
        'icon': '📋',
        'color': '#64748b',
        'input_type': 'document',
        'cover_type': 'document',
        'output_type': 'document',
        'supports_encryption': True,
        'max_capacity': '10-25%',
        'robustness': 'Very High',
    },
}

# ───────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ───────────────────────────────────────────────────────────────

def create_upload_directory(dir_path: str):
    """Create upload directory if it doesn't exist"""
    os.makedirs(dir_path, exist_ok=True)

@router.get("/api/document-ops/info")
async def get_document_operations_info():
    """Get information about all document operations"""
    return {
        'total_operations': len(DOCUMENT_OPERATION_DEFINITIONS),
        'operations': DOCUMENT_OPERATION_DEFINITIONS
    }

# ───────────────────────────────────────────────────────────────
# DOCUMENT OPERATION ENDPOINTS
# ───────────────────────────────────────────────────────────────

def _execute_document_operation(
    operation_id: str,
    secret_file: str,
    cover_file: str,
    output_file: str,
    password: str,
    use_encryption: bool = True
) -> Dict[str, Any]:
    """Execute a document operation using the stego engine"""
    
    engine = get_doc_stego_engine()
    if not engine:
        raise RuntimeError("Document steganography engine not available")
    
    try:
        # Map operation_id to engine method
        if operation_id == 'i2d':
            return engine.hide_image_in_document(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'd2i':
            return engine.hide_document_in_image(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'v2d':
            return engine.hide_video_in_document(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'd2v':
            return engine.hide_document_in_video(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'a2d':
            return engine.hide_audio_in_document(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'd2a':
            return engine.hide_document_in_audio(secret_file, cover_file, output_file, password, use_encryption)
        
        elif operation_id == 'd2d':
            return engine.hide_document_in_document(secret_file, cover_file, output_file, password, use_encryption)
        
        else:
            raise ValueError(f"Unknown document operation: {operation_id}")
    
    except Exception as e:
        raise RuntimeError(f"Document operation failed: {str(e)}")


@router.post("/api/document-ops/hide-image-in-document")
async def hide_image_in_document(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 10: Hide image in document (I→D)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        # Create upload directories
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        # Save uploaded files
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.txt")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        # Execute operation in thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'i2d', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'i2d',
            'concept': 'Image to Document (Concept 10)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-document-in-image")
async def hide_document_in_image(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 11: Hide document in image (D→I)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.png")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'd2i', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'd2i',
            'concept': 'Document to Image (Concept 11)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-video-in-document")
async def hide_video_in_document(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 12: Hide video in document (V→D)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.pdf")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'v2d', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'v2d',
            'concept': 'Video to Document (Concept 12)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-document-in-video")
async def hide_document_in_video(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 13: Hide document in video (D→V)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.mp4")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'd2v', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'd2v',
            'concept': 'Document to Video (Concept 13)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-audio-in-document")
async def hide_audio_in_document(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 14: Hide audio in document (A→D)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.pdf")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'a2d', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'a2d',
            'concept': 'Audio to Document (Concept 14)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-document-in-audio")
async def hide_document_in_audio(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 15: Hide document in audio (D→A)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.wav")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'd2a', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'd2a',
            'concept': 'Document to Audio (Concept 15)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@router.post("/api/document-ops/hide-document-in-document")
async def hide_document_in_document(
    secret: UploadFile = File(...),
    cover: UploadFile = File(...),
    password: str = Form(...)
):
    """Concept 16: Hide document in document (D↔D)"""
    
    result_id = str(uuid.uuid4())
    
    try:
        uploads_dir = 'api/static/uploads/documents'
        create_upload_directory(uploads_dir)
        
        secret_path = os.path.join(uploads_dir, f"{result_id}_secret_{secret.filename}")
        cover_path = os.path.join(uploads_dir, f"{result_id}_cover_{cover.filename}")
        output_path = os.path.join(uploads_dir, f"{result_id}_output_stego.pdf")
        
        async with aiofiles.open(secret_path, 'wb') as f:
            await f.write(await secret.read())
        
        async with aiofiles.open(cover_path, 'wb') as f:
            await f.write(await cover.read())
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _execute_document_operation,
            'd2d', secret_path, cover_path, output_path, password
        )
        
        return {
            'status': 'success',
            'result_id': result_id,
            'operation': 'd2d',
            'concept': 'Document to Document (Concept 16)',
            'output_file': output_path,
            'stats': result
        }
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


__all__ = ['router', 'DOCUMENT_OPERATION_DEFINITIONS']
