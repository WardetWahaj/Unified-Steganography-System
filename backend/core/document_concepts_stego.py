"""
Document Steganography Concepts - Explicit Implementation
===========================================================
Extensions to NineConceptsSteganography with 7 document-based combinations

The 16 Total Concepts:
  Original 9 (Multimedia):
  1. Image → Image
  2. Image → Video
  3. Image → Audio
  4. Video → Video
  5. Video → Image
  6. Video → Audio
  7. Audio → Audio
  8. Audio → Image
  9. Audio → Video
  
  New 7 (Document-based):
  10. Image → Document
  11. Document → Image
  12. Video → Document
  13. Document → Video
  14. Audio → Document
  15. Document → Audio
  16. Document → Document
"""

import os
import io
from typing import Optional, Dict, Any
from core.nine_concepts_stego import NineConceptsSteganography
from steganography.document_stego import DocumentSteganography


class DocumentConceptsSteganography(NineConceptsSteganography):
    """
    Extended steganography system with full 16-concept support.
    Inherits all 9 multimedia concepts from NineConceptsSteganography.
    Adds 7 document-based concepts (10-16).
    TOTAL: 16 steganography concepts supported
    """
    
    def __init__(self, key_dir: str = 'keys', **kwargs):
        """Initialize with all optimization features enabled by default"""
        super().__init__(key_dir, **kwargs)
        print("[+] Document Concepts Steganography System Initialized (16-Concept Total)")
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 10: IMAGE → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_image_in_document(
        self,
        secret_image: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 10: Hide an image file inside a document (TXT/PDF/DOCX)
        Encodes image binary data in document metadata or text
        
        :param secret_image: Image file to hide (.jpg, .png, .bmp)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 10: Hiding image in document")
        print(f"    Secret: {os.path.basename(secret_image)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        stats = self.hide_file_optimized(secret_image, cover_document, output_file, password, use_encryption, encryption_method)
        stats['output_file'] = output_file
        return stats
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 11: DOCUMENT → IMAGE
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_image(
        self,
        secret_document: str,
        cover_image: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 11: Hide a document inside an image (LSB in pixels)
        Documents can be hidden in high-resolution images
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_image: Cover image (.png, .jpg, .bmp, .tiff)
        :param output_file: Output image path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 11: Hiding document in image")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_image)}")
        
        return self.hide_file_optimized(secret_document, cover_image, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 12: VIDEO → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_video_in_document(
        self,
        secret_video: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 12: Hide a video file inside a document
        Extremely low capacity but very robust hiding
        Requires very large document (PDF/DOCX)
        
        :param secret_video: Video file to hide (.mp4, .avi, .mov, .mkv)
        :param cover_document: Large cover document (.pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 12: Hiding video in document (⚠️ Low capacity)")
        print(f"    Secret: {os.path.basename(secret_video)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        return self.hide_file_optimized(secret_video, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 13: DOCUMENT → VIDEO
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_video(
        self,
        secret_document: str,
        cover_video: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 13: Hide a document inside a video
        Document encoded in video frame LSBs
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_video: Cover video (.mp4, .avi, .mov, .mkv)
        :param output_file: Output video path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 13: Hiding document in video")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_video)}")
        
        return self.hide_file_optimized(secret_document, cover_video, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 14: AUDIO → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_audio_in_document(
        self,
        secret_audio: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 14: Hide an audio file inside a document
        Very robust - minimal detectable changes to document
        
        :param secret_audio: Audio file to hide (.wav, .mp3, .flac, .aiff)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 14: Hiding audio in document")
        print(f"    Secret: {os.path.basename(secret_audio)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        stats = self.hide_file_optimized(secret_video, cover_document, output_file, password, use_encryption, encryption_method)
        stats['output_file'] = output_file
        return stats
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 15: DOCUMENT → AUDIO
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_audio(
        self,
        secret_document: str,
        cover_audio: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 15: Hide a document inside audio (LSB in samples)
        Good capacity and robustness
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_audio: Cover audio (.wav, .mp3, .flac, .aiff)
        :param output_file: Output audio path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 15: Hiding document in audio")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_audio)}")
        
        return self.hide_file_optimized(secret_document, cover_audio, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 16: DOCUMENT → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_document(
        self,
        secret_document: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 16: Hide a document inside another document
        Ultimate robustness - minimal perceptual changes
        
        Document-Document combinations:
        - TXT in TXT: Zero-width character encoding
        - TXT in PDF: Metadata injection
        - TXT in DOCX: Property modification
        - PDF in TXT: Base64 encoding
        - PDF in PDF: Stream modification
        - PDF in DOCX: Custom XML parts
        - DOCX in TXT: Base64 encoding
        - DOCX in PDF: Metadata
        - DOCX in DOCX: Comment insertion
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 16: Hiding document in document (⭐ Highest Robustness)")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        return self.hide_file_optimized(secret_document, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # UNIVERSAL EXTRACTION (All 16 concepts)
    # ═══════════════════════════════════════════════════════════
    
    def extract_from_any_media_or_document(
        self,
        stego_file: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Universal extraction method - works with all 16 concepts
        Automatically detects media/document type and extracts hidden data
        
        :param stego_file: Media/document file containing hidden data (any format)
        :param output_file: Output file path
        :param password: Decryption password
        :param use_encryption: Whether data is encrypted (default True)
        :return: Statistics dict with timing information
        """
        file_ext = os.path.splitext(stego_file)[1].lower()
        
        is_document = file_ext in ['.txt', '.pdf', '.docx']
        
        if is_document:
            print(f"[←] Extracting from document (auto-detect)")
        else:
            print(f"[←] Extracting from media (auto-detect)")
        
        print(f"    Source: {os.path.basename(stego_file)}")
        
        return self.extract_file_optimized(stego_file, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════
    
    def get_concept_info(self, concept_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific concept"""
        concepts = {
            '10': {
                'name': 'I→D',
                'label': 'Image→Doc',
                'description': 'Image to Document',
                'robustness': 'Very High',
                'capacity': '5-15%',
                'reversible': True
            },
            '11': {
                'name': 'D→I',
                'label': 'Doc→Image',
                'description': 'Document to Image',
                'robustness': 'Medium',
                'capacity': '30-50%',
                'reversible': True
            },
            '12': {
                'name': 'V→D',
                'label': 'Video→Doc',
                'description': 'Video to Document',
                'robustness': 'Very High',
                'capacity': '1-5%',
                'reversible': True
            },
            '13': {
                'name': 'D→V',
                'label': 'Doc→Video',
                'description': 'Document to Video',
                'robustness': 'High',
                'capacity': '10-20%',
                'reversible': True
            },
            '14': {
                'name': 'A→D',
                'label': 'Audio→Doc',
                'description': 'Audio to Document',
                'robustness': 'Very High',
                'capacity': '2-8%',
                'reversible': True
            },
            '15': {
                'name': 'D→A',
                'label': 'Doc→Audio',
                'description': 'Document to Audio',
                'robustness': 'High',
                'capacity': '20-40%',
                'reversible': True
            },
            '16': {
                'name': 'D↔D',
                'label': 'Doc↔Doc',
                'description': 'Document to Document',
                'robustness': 'Extremely High',
                'capacity': '10-25%',
                'reversible': True
            }
        }
        
        return concepts.get(concept_id, {})
    
    def list_all_concepts(self) -> Dict[str, Dict[str, str]]:
        """List all 16 concepts with metadata"""
        all_concepts = {
            # Original 9 (from parent class)
            '1': {'name': 'I→I', 'type': 'Multimedia', 'category': 'Classic'},
            '2': {'name': 'I→V', 'type': 'Multimedia', 'category': 'Covert'},
            '3': {'name': 'I→A', 'type': 'Multimedia', 'category': 'Deep'},
            '4': {'name': 'V→V', 'type': 'Multimedia', 'category': 'Stream'},
            '5': {'name': 'V→I', 'type': 'Multimedia', 'category': 'Frame'},
            '6': {'name': 'V→A', 'type': 'Multimedia', 'category': 'Sync'},
            '7': {'name': 'A→A', 'type': 'Multimedia', 'category': 'Layer'},
            '8': {'name': 'A→I', 'type': 'Multimedia', 'category': 'Spectral'},
            '9': {'name': 'A→V', 'type': 'Multimedia', 'category': 'Dual'},
            # Document concepts
            '10': {'name': 'I→D', 'type': 'Document', 'category': 'Image→Doc'},
            '11': {'name': 'D→I', 'type': 'Document', 'category': 'Doc→Image'},
            '12': {'name': 'V→D', 'type': 'Document', 'category': 'Video→Doc'},
            '13': {'name': 'D→V', 'type': 'Document', 'category': 'Doc→Video'},
            '14': {'name': 'A→D', 'type': 'Document', 'category': 'Audio→Doc'},
            '15': {'name': 'D→A', 'type': 'Document', 'category': 'Doc→Audio'},
            '16': {'name': 'D↔D', 'type': 'Document', 'category': 'Doc↔Doc'},
        }
        
        return all_concepts


# Provide backwards compatibility and explicit exports
__all__ = ['DocumentConceptsSteganography']
"""
Document Steganography Concepts - 7 New Bidirectional Concepts
===============================================================

New Concepts (10-16):
  10. I→D (Image to Document) - Hide image in document
  11. D→I (Document to Image) - Hide document in image
  12. V→D (Video to Document) - Hide video in document
  13. D→V (Document to Video) - Hide document in video
  14. A→D (Audio to Document) - Hide audio in document
  15. D→A (Document to Audio) - Hide document in audio
  16. D→D (Document to Document) - Hide document in document
"""

import os
import sys
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nine_concepts_stego import NineConceptsSteganography
from steganography.document_stego import DocumentSteganography


class DocumentConceptsSteganography(NineConceptsSteganography):
    """
    Extended steganography system with full 16-concept support.
    Inherits all 9 multimedia concepts from NineConceptsSteganography.
    Adds 7 document-based concepts (10-16).
    TOTAL: 16 steganography concepts supported
    """
    
    def __init__(self, key_dir: str = 'keys', **kwargs):
        """Initialize with all optimization features + document support"""
        super().__init__(key_dir, **kwargs)
        self.doc_stego = DocumentSteganography()
        print("[+] Document Steganography Concepts Initialized")
        print("[+] Extended Concepts: 9 multimedia + 7 document = 16 total")
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 10: IMAGE → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_image_in_document(
        self,
        secret_image: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 10: Hide an image file inside a document
        
        Supported document formats: .txt, .pdf, .docx
        
        :param secret_image: Image file to hide (.jpg, .png, .bmp, .tiff)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 10: Hiding image in document")
        print(f"    Secret: {os.path.basename(secret_image)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        # Use base hide_file_optimized which handles encryption
        return self.hide_file_optimized(secret_image, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 11: DOCUMENT → IMAGE
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_image(
        self,
        secret_document: str,
        cover_image: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 11: Hide a document file inside an image
        Requires high-resolution cover image for document capacity
        
        :param secret_document: Document to hide (.txt, .pdf, .docx)
        :param cover_image: High-resolution cover image (.png, .bmp, .tiff)
        :param output_file: Output image path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 11: Hiding document in image")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_image)}")
        
        return self.hide_file_optimized(secret_document, cover_image, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 12: VIDEO → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_video_in_document(
        self,
        secret_video: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 12: Hide a video file inside a document
        Very low capacity but extremely robust
        
        :param secret_video: Video file to hide (.mp4, .avi, .mov, .mkv)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 12: Hiding video in document (low capacity, high robustness)")
        print(f"    Secret: {os.path.basename(secret_video)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        return self.hide_file_optimized(secret_video, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 13: DOCUMENT → VIDEO
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_video(
        self,
        secret_document: str,
        cover_video: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 13: Hide a document file inside a video
        Good capacity and high robustness
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_video: Cover video (.mp4, .avi, .mov, .mkv)
        :param output_file: Output video path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 13: Hiding document in video")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_video)}")
        
        return self.hide_file_optimized(secret_document, cover_video, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 14: AUDIO → DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_audio_in_document(
        self,
        secret_audio: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 14: Hide an audio file inside a document
        Very high robustness - documents are perceptually stable
        
        :param secret_audio: Audio file to hide (.wav, .mp3, .flac, .aiff)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 14: Hiding audio in document (very high robustness)")
        print(f"    Secret: {os.path.basename(secret_audio)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        return self.hide_file_optimized(secret_audio, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 15: DOCUMENT → AUDIO
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_audio(
        self,
        secret_document: str,
        cover_audio: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 15: Hide a document file inside audio
        Good capacity with high robustness
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_audio: Cover audio (.wav, .mp3, .flac, .aiff)
        :param output_file: Output audio path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 15: Hiding document in audio")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_audio)}")
        
        return self.hide_file_optimized(secret_document, cover_audio, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 16: DOCUMENT ↔ DOCUMENT
    # ═══════════════════════════════════════════════════════════
    
    def hide_document_in_document(
        self,
        secret_document: str,
        cover_document: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Concept 16: Hide a document file inside another document
        Highest robustness - documents are stable and perceptually unchanging
        
        Supports combinations:
        - TXT ↔ TXT, PDF, DOCX
        - PDF ↔ TXT, PDF, DOCX
        - DOCX ↔ TXT, PDF, DOCX
        
        :param secret_document: Document file to hide (.txt, .pdf, .docx)
        :param cover_document: Cover document (.txt, .pdf, .docx)
        :param output_file: Output document path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 16: Hiding document in document (HIGHEST robustness)")
        print(f"    Secret: {os.path.basename(secret_document)}")
        print(f"    Cover:  {os.path.basename(cover_document)}")
        
        return self.hide_file_optimized(secret_document, cover_document, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # UNIVERSAL EXTRACTION (works for all 16 concepts)
    # ═══════════════════════════════════════════════════════════
    
    def extract_from_any_media_with_docs(
        self,
        stego_file: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Universal extraction - works with all 16 concepts
        Automatically detects media/document type and extracts hidden data
        
        Supports extraction from:
        - Multimedia: Images, Videos, Audio files
        - Documents: TXT, PDF, DOCX
        
        :param stego_file: Media/document file containing hidden data
        :param output_file: Output file path for extracted secret
        :param password: Decryption password
        :param use_encryption: Whether data is encrypted
        :return: Statistics dict with timing information
        """
        print(f"[←] Universal extraction from any media/document (auto-detect)")
        print(f"    Source: {os.path.basename(stego_file)}")
        
        return self.extract_file_optimized(stego_file, output_file, password, use_encryption)
    
    # ═══════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    def get_all_concepts(self) -> dict:
        """Return all 16 concepts with metadata"""
        return {
            # Multimedia (9)
            'i2i': {'name': 'Image→Image', 'category': 'multimedia', 'robustness': 'Low'},
            'i2v': {'name': 'Image→Video', 'category': 'multimedia', 'robustness': 'Medium'},
            'i2a': {'name': 'Image→Audio', 'category': 'multimedia', 'robustness': 'High'},
            'v2i': {'name': 'Video→Image', 'category': 'multimedia', 'robustness': 'Medium'},
            'v2v': {'name': 'Video→Video', 'category': 'multimedia', 'robustness': 'High'},
            'v2a': {'name': 'Video→Audio', 'category': 'multimedia', 'robustness': 'Medium'},
            'a2i': {'name': 'Audio→Image', 'category': 'multimedia', 'robustness': 'Low'},
            'a2v': {'name': 'Audio→Video', 'category': 'multimedia', 'robustness': 'High'},
            'a2a': {'name': 'Audio→Audio', 'category': 'multimedia', 'robustness': 'High'},
            
            # Document (7)
            'i2d': {'name': 'Image→Document', 'category': 'document', 'robustness': 'Very High'},
            'd2i': {'name': 'Document→Image', 'category': 'document', 'robustness': 'Medium'},
            'v2d': {'name': 'Video→Document', 'category': 'document', 'robustness': 'Very High'},
            'd2v': {'name': 'Document→Video', 'category': 'document', 'robustness': 'High'},
            'a2d': {'name': 'Audio→Document', 'category': 'document', 'robustness': 'Very High'},
            'd2a': {'name': 'Document→Audio', 'category': 'document', 'robustness': 'High'},
            'd2d': {'name': 'Document↔Document', 'category': 'document', 'robustness': 'Extreme'},
        }


# Provide backwards compatibility
__all__ = ['DocumentConceptsSteganography']
