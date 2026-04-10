"""
Unified Steganography System
Combines steganography with encryption for secure data hiding
"""
from steganography.audio_stego import AudioSteganography
from steganography.image_stego import ImageSteganography
from steganography.video_stego import VideoSteganography
from crypto.hybrid_crypto import HybridCrypto
import os


class UnifiedSteganography:
    """
    Unified system for steganography with encryption
    Supports: Audio, Image, and Video steganography with RSA/AES encryption
    """
    
    def __init__(self, key_dir='keys'):
        """
        Initialize Unified Steganography System
        
        :param key_dir: Directory for RSA keys
        """
        self.audio_stego = AudioSteganography()
        self.image_stego = ImageSteganography()
        self.video_stego = VideoSteganography()
        self.crypto = HybridCrypto(key_dir)
    
    def hide_file(self, secret_file, cover_file, output_file, password=None, use_encryption=True):
        """
        Hide a file inside a cover media file
        
        :param secret_file: Path to file to hide
        :param cover_file: Path to cover media (audio/image/video)
        :param output_file: Path to output file
        :param password: Password for encryption (required if use_encryption=True)
        :param use_encryption: Whether to encrypt the file before hiding
        :return: Path to output file
        """
        # Read secret file
        with open(secret_file, 'rb') as f:
            data = f.read()
        
        # Encrypt if requested
        if use_encryption:
            if password is None:
                raise ValueError("Password required for encryption (use password for both RSA and AES security)")
            
            print("[*] Encrypting data...")
            data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
            print(f"[+] Encryption method: {method}")
        
        # Determine cover file type
        cover_ext = os.path.splitext(cover_file)[1].lower()[1:]
        
        # Hide data based on cover type
        if cover_ext in ['wav', 'mp3', 'flac', 'aiff']:
            print("[*] Using Audio Steganography...")
            # Convert to WAV if needed
            if cover_ext != 'wav':
                print(f"[!] Note: {cover_ext} files should be converted to WAV first")
            return self.audio_stego.encode(cover_file, output_file, data)
        
        elif cover_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            print("[*] Using Image Steganography...")
            return self.image_stego.encode(cover_file, output_file, data)
        
        elif cover_ext in ['mp4', 'avi', 'mov', 'mkv']:
            print("[*] Using Video Steganography...")
            return self.video_stego.encode(cover_file, output_file, data)
        
        else:
            raise ValueError(f"Unsupported cover file format: {cover_ext}")
    
    def extract_file(self, stego_file, output_file, password=None, use_encryption=True):
        """
        Extract hidden file from stego media
        
        :param stego_file: Path to stego media file
        :param output_file: Path to save extracted file
        :param password: Password for decryption (required if use_encryption=True)
        :param use_encryption: Whether the hidden data is encrypted
        :return: Path to extracted file
        """
        # Determine stego file type
        stego_ext = os.path.splitext(stego_file)[1].lower()[1:]
        
        # Extract data based on stego type
        if stego_ext in ['wav', 'mp3', 'flac', 'aiff']:
            print("[*] Using Audio Steganography...")
            data = self.audio_stego.decode(stego_file)
        
        elif stego_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            print("[*] Using Image Steganography...")
            data = self.image_stego.decode(stego_file)
        
        elif stego_ext in ['mp4', 'avi', 'mov', 'mkv']:
            print("[*] Using Video Steganography...")
            data = self.video_stego.decode(stego_file)
        
        else:
            raise ValueError(f"Unsupported stego file format: {stego_ext}")
        
        # Decrypt if requested
        if use_encryption:
            if password is None:
                raise ValueError("Password required for decryption")
            
            print("[*] Decrypting data...")
            data = self.crypto.decrypt_data(data, password, method='AUTO')
        
        # Save extracted file
        with open(output_file, 'wb') as f:
            f.write(data)
        
        print(f"[+] Extracted file saved to: {output_file}")
        return output_file
    
    def hide_message(self, message, cover_file, output_file, password=None, use_encryption=True):
        """
        Hide a text message inside a cover media file
        
        :param message: Text message to hide
        :param cover_file: Path to cover media
        :param output_file: Path to output file
        :param password: Password for encryption
        :param use_encryption: Whether to encrypt the message
        :return: Path to output file
        """
        # Handle empty messages
        if message == "":
            message = "\x00"  # Use null character for truly empty messages
        
        data = message.encode('utf-8')
        
        # Encrypt if requested
        if use_encryption:
            if password is None:
                raise ValueError("Password required for encryption (use password for both RSA and AES security)")
            
            print("[*] Encrypting message...")
            data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
            print(f"[+] Encryption method: {method}")
        
        # Determine cover file type and hide message
        cover_ext = os.path.splitext(cover_file)[1].lower()[1:]
        
        if cover_ext in ['wav', 'mp3', 'flac', 'aiff']:
            return self.audio_stego.encode(cover_file, output_file, data)
        elif cover_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            return self.image_stego.encode(cover_file, output_file, data)
        elif cover_ext in ['mp4', 'avi', 'mov', 'mkv']:
            return self.video_stego.encode(cover_file, output_file, data)
        else:
            raise ValueError(f"Unsupported cover file format: {cover_ext}")
    
    def extract_message(self, stego_file, password=None, use_encryption=True):
        """
        Extract hidden text message from stego media
        
        :param stego_file: Path to stego media file
        :param password: Password for decryption
        :param use_encryption: Whether the message is encrypted
        :return: Extracted message
        """
        # Determine stego file type and extract data
        stego_ext = os.path.splitext(stego_file)[1].lower()[1:]
        
        if stego_ext in ['wav', 'mp3', 'flac', 'aiff']:
            data = self.audio_stego.decode(stego_file)
        elif stego_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            data = self.image_stego.decode(stego_file)
        elif stego_ext in ['mp4', 'avi', 'mov', 'mkv']:
            data = self.video_stego.decode(stego_file)
        else:
            raise ValueError(f"Unsupported stego file format: {stego_ext}")
        
        # Decrypt if requested
        if use_encryption:
            if password is None:
                raise ValueError("Password required for decryption")
            
            print("[*] Decrypting message...")
            data = self.crypto.decrypt_data(data, password, method='AUTO')
        
        # Convert to string
        message = data.decode('utf-8', errors='ignore')
        
        # Handle empty message placeholder
        if message == "\x00":
            return ""
        
        return message
    
    def generate_keys(self):
        """Generate RSA key pair"""
        return self.crypto.rsa_handler.generate_keys()
    
    def keys_exist(self):
        """Check if RSA keys exist"""
        return self.crypto.rsa_handler.keys_exist()
