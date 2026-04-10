"""
Multimedia Steganography Concepts (9 of 16 total)
Extensions to OptimizedUnifiedSteganography with all 9 cross-media combinations

The 9 Multimedia Concepts (part of 16 total):
  1. Image → Image  (hide image in image)
  2. Image → Video  (hide image in video) 
  3. Image → Audio  (hide image in audio)
  4. Video → Video  (hide video in video)
  5. Video → Image  (hide video in image)
  6. Video → Audio  (hide video in audio)
  7. Audio → Audio  (hide audio in audio)
  8. Audio → Image  (hide audio in image)
  9. Audio → Video  (hide audio in video)

+ 7 Document Concepts (in DocumentConceptsSteganography):
  10. Image → Document
  11. Document → Image
  12. Video → Document
  13. Document → Video
  14. Audio → Document
  15. Document → Audio
  16. Document → Document

TOTAL: 16 steganography concepts supported
"""

from core.optimized_stego import OptimizedUnifiedSteganography
from typing import Optional, Callable
import os


class NineConceptsSteganography(OptimizedUnifiedSteganography):
    """
    Multimedia steganography system with explicit support for 9 cross-media concepts.
    This is the base class; extends to DocumentConceptsSteganography for full 16 concepts.
    
    Provides methods for hiding files/messages in multimedia (Image, Audio, Video).
    Extended by DocumentConceptsSteganography to add document-based concepts 10-16.
    
    Total System: 16 steganography concepts
    """
    
    def __init__(self, key_dir: str = 'keys', **kwargs):
        """Initialize with all optimization features enabled by default"""
        super().__init__(key_dir, **kwargs)
        print("[+] Nine Multimedia Concepts Initialized (part of 16-concept system)")
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 1: IMAGE → IMAGE
    # ═══════════════════════════════════════════════════════════
    
    def hide_image_in_image(
        self,
        secret_image: str,
        cover_image: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 1: Hide an image file inside another image (LSB steganography)
        
        :param secret_image: Image file to hide (.png, .jpg, .bmp, .tiff)
        :param cover_image: Cover image (.png, .jpg, .bmp, .tiff) 
        :param output_file: Output image path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 1: Hiding image in image")
        print(f"    Secret: {os.path.basename(secret_image)}")
        print(f"    Cover:  {os.path.basename(cover_image)}")
        return self.hide_file_optimized(secret_image, cover_image, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 2: IMAGE → VIDEO
    # ═══════════════════════════════════════════════════════════
    
    def hide_image_in_video(
        self,
        secret_image: str,
        cover_video: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 2: Hide an image file inside a video (LSB in video frames)
        
        :param secret_image: Image file to hide (.png, .jpg, .bmp)
        :param cover_video: Cover video (.mp4, .avi, .mov, .mkv)
        :param output_file: Output video path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 2: Hiding image in video")
        print(f"    Secret: {os.path.basename(secret_image)}")
        print(f"    Cover:  {os.path.basename(cover_video)}")
        return self.hide_file_optimized(secret_image, cover_video, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 3: IMAGE → AUDIO
    # ═══════════════════════════════════════════════════════════
    
    def hide_image_in_audio(
        self,
        secret_image: str,
        cover_audio: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 3: Hide an image file inside audio (LSB in audio samples)
        
        :param secret_image: Image file to hide (.png, .jpg, .bmp)
        :param cover_audio: Cover audio (.wav, .mp3, .flac, .aiff)
        :param output_file: Output audio path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 3: Hiding image in audio")
        print(f"    Secret: {os.path.basename(secret_image)}")
        print(f"    Cover:  {os.path.basename(cover_audio)}")
        return self.hide_file_optimized(secret_image, cover_audio, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 4: VIDEO → VIDEO
    # ═══════════════════════════════════════════════════════════
    
    def hide_video_in_video(
        self,
        secret_video: str,
        cover_video: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 4: Hide a video file inside another video (LSB in frames)
        GPU-accelerated for 1GB+ datasets with 30-45s target time
        
        :param secret_video: Video file to hide (.mp4, .avi, .mov, .mkv)
        :param cover_video: Cover video (.mp4, .avi, .mov, .mkv)
        :param output_file: Output video path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 4: Hiding video in video (⚡ GPU-accelerated)")
        print(f"    Secret: {os.path.basename(secret_video)}")
        print(f"    Cover:  {os.path.basename(cover_video)}")
        return self.hide_file_optimized(secret_video, cover_video, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 5: VIDEO → IMAGE
    # ═══════════════════════════════════════════════════════════
    
    def hide_video_in_image(
        self,
        secret_video: str,
        cover_image: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 5: Hide a video file inside an image (LSB in pixels)
        Requires large high-resolution image for video capacity
        
        :param secret_video: Video file to hide (.mp4, .avi, .mov, .mkv)
        :param cover_image: High-resolution cover image (.png, .bmp, .tiff)
        :param output_file: Output image path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 5: Hiding video in image")
        print(f"    Secret: {os.path.basename(secret_video)}")
        print(f"    Cover:  {os.path.basename(cover_image)}")
        return self.hide_file_optimized(secret_video, cover_image, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 6: VIDEO → AUDIO
    # ═══════════════════════════════════════════════════════════
    
    def hide_video_in_audio(
        self,
        secret_video: str,
        cover_audio: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 6: Hide a video file inside audio (LSB in audio samples)
        Requires long audio track for video capacity
        
        :param secret_video: Video file to hide (.mp4, .avi, .mov, .mkv)
        :param cover_audio: Long cover audio (.wav, .mp3, .flac) - recommend 10+ min
        :param output_file: Output audio path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 6: Hiding video in audio")
        print(f"    Secret: {os.path.basename(secret_video)}")
        print(f"    Cover:  {os.path.basename(cover_audio)}")
        return self.hide_file_optimized(secret_video, cover_audio, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 7: AUDIO → AUDIO
    # ═══════════════════════════════════════════════════════════
    
    def hide_audio_in_audio(
        self,
        secret_audio: str,
        cover_audio: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 7: Hide an audio file inside another audio (LSB in samples)
        Perfect for stealth communication
        
        :param secret_audio: Audio file to hide (.wav, .mp3, .flac, .aiff)
        :param cover_audio: Cover audio (.wav, .mp3, .flac, .aiff)
        :param output_file: Output audio path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 7: Hiding audio in audio")
        print(f"    Secret: {os.path.basename(secret_audio)}")
        print(f"    Cover:  {os.path.basename(cover_audio)}")
        return self.hide_file_optimized(secret_audio, cover_audio, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 8: AUDIO → IMAGE
    # ═══════════════════════════════════════════════════════════
    
    def hide_audio_in_image(
        self,
        secret_audio: str,
        cover_image: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 8: Hide an audio file inside an image (LSB in pixels)
        Allows image transmission containing hidden audio
        
        :param secret_audio: Audio file to hide (.wav, .mp3, .flac, .aiff)
        :param cover_image: Cover image (.png, .jpg, .bmp, .tiff)
        :param output_file: Output image path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 8: Hiding audio in image")
        print(f"    Secret: {os.path.basename(secret_audio)}")
        print(f"    Cover:  {os.path.basename(cover_image)}")
        return self.hide_file_optimized(secret_audio, cover_image, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # CONCEPT 9: AUDIO → VIDEO
    # ═══════════════════════════════════════════════════════════
    
    def hide_audio_in_video(
        self,
        secret_audio: str,
        cover_video: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True,
        encryption_method: str = 'rsa'
    ) -> dict:
        """
        Concept 9: Hide an audio file inside a video (LSB in video frames)
        Video already contains audio track, hidden audio goes in frame LSBs
        
        :param secret_audio: Audio file to hide (.wav, .mp3, .flac, .aiff)
        :param cover_video: Cover video (.mp4, .avi, .mov, .mkv)
        :param output_file: Output video path
        :param password: Encryption password
        :param use_encryption: Whether to encrypt before hiding (default True)
        :param encryption_method: Encryption method ('rsa', 'aes', 'rsa+aes')
        :return: Statistics dict with timing information
        """
        print(f"[→] Concept 9: Hiding audio in video")
        print(f"    Secret: {os.path.basename(secret_audio)}")
        print(f"    Cover:  {os.path.basename(cover_video)}")
        return self.hide_file_optimized(secret_audio, cover_video, output_file, password, use_encryption, encryption_method)
    
    # ═══════════════════════════════════════════════════════════
    # EXTRACTION METHODS (works for all 9 multimedia concepts)
    # ═══════════════════════════════════════════════════════════
    
    def extract_from_any_media(
        self,
        stego_file: str,
        output_file: str,
        password: Optional[str] = None,
        use_encryption: bool = True
    ) -> dict:
        """
        Universal extraction method - works with all 9 multimedia concepts
        Automatically detects media type and extracts hidden data
        
        :param stego_file: Media file containing hidden data (any format)
        :param output_file: Output file path
        :param password: Decryption password
        :param use_encryption: Whether data is encrypted (default True)
        :return: Statistics dict with timing information
        """
        print(f"[←] Extracting from media (auto-detect)")
        print(f"    Source: {os.path.basename(stego_file)}")
        return self.extract_file_optimized(stego_file, output_file, password, use_encryption)


# Provide backwards compatibility
__all__ = ['NineConceptsSteganography']
