"""
User-based Steganography System
Extends unified_stego.py to track which user encrypted/decrypted files
"""
from steganography.audio_stego import AudioSteganography
from steganography.image_stego import ImageSteganography
from steganography.video_stego import VideoSteganography  # FFmpegFFV1 lossless codec
from crypto.hybrid_crypto import HybridCrypto
import os
import json


class UserSteganography:
    """
    User-aware steganography system
    - Tracks which user created/encrypted files
    - Uses user's private key for encryption
    - Verifies against user's public key for decryption
    """
    
    def __init__(self, user_id, username, private_key_pem, public_key_pem, creator_public_key=None):
        """
        Initialize user steganography system
        
        :param user_id: User ID from database
        :param username: Username
        :param private_key_pem: User's private key (PEM format)
        :param public_key_pem: User's public key (PEM format)
        :param creator_public_key: Creator's public key (optional, for shared file extraction)
        """
        self.user_id = user_id
        self.username = username
        self.private_key_pem = private_key_pem
        self.public_key_pem = public_key_pem
        self.creator_public_key = creator_public_key  # For extracting shared files
        
        self.audio_stego = AudioSteganography()
        self.image_stego = ImageSteganography()
        self.video_stego = VideoSteganography()  # FFmpeg + FFV1 lossless
        self.crypto = HybridCrypto(key_dir='.')
        
        # Override RSA handler with user's key pair
        self._setup_user_crypto()
    
    def _setup_user_crypto(self):
        """Setup crypto system with user's RSA keys"""
        import tempfile
        from Crypto.PublicKey import RSA
        
        # Write user keys to temp location
        self.temp_dir = tempfile.mkdtemp()
        self.user_public_key_path = os.path.join(self.temp_dir, f'user_{self.user_id}_pub.pem')
        self.user_private_key_path = os.path.join(self.temp_dir, f'user_{self.user_id}_priv.pem')
        
        with open(self.user_public_key_path, 'w') as f:
            f.write(self.public_key_pem)
        
        with open(self.user_private_key_path, 'w') as f:
            f.write(self.private_key_pem)
        
        # Load keys into crypto handler
        self.crypto.rsa_handler.load_public_key(self.user_public_key_path)
        self.crypto.rsa_handler.load_private_key(self.user_private_key_path)
        
        print(f"[+] User {self.username} (ID: {self.user_id}) crypto initialized")
        
        # DEBUG: Log key fingerprints to help diagnose key mismatches
        try:
            pub_key = RSA.import_key(self.public_key_pem)
            priv_key = RSA.import_key(self.private_key_pem)
            pub_fingerprint = format(pub_key.n, '064x')[-64:]  # Last 64 chars of modulus in hex
            priv_fingerprint = format(priv_key.n, '064x')[-64:]
            print(f"[DEBUG] Public key fingerprint: {pub_fingerprint}")
            print(f"[DEBUG] Private key fingerprint: {priv_fingerprint}")
            print(f"[DEBUG] Keys paired: {pub_fingerprint == priv_fingerprint}")
        except Exception as e:
            print(f"[DEBUG] Could not compute key fingerprints: {e}")
    
    def hide_file(self, secret_file, cover_file, output_file, password=None, use_encryption=True, encryption_method='hybrid', recipients=None):
        """
        Hide a file inside a cover media
        Supports multi-recipient encryption (Approach 2)
        
        Supports three encryption methods:
        - 'rsa': RSA-only encryption (public key)
        - 'password': Password-only encryption (AES)
        - 'hybrid': RSA + Password (default)
        
        :param secret_file: Path to file to hide
        :param cover_file: Path to cover media
        :param output_file: Path to output file
        :param password: Password for encryption (used with password/hybrid modes)
        :param use_encryption: Whether to encrypt before hiding
        :param encryption_method: 'rsa', 'password', or 'hybrid'
        :param recipients: List of recipient user IDs for multi-recipient encryption
        :return: Dict with output path and metadata
        """
        # Read secret file
        with open(secret_file, 'rb') as f:
            data = f.read()
        
        # Create metadata about the encryption
        metadata = {
            'creator_user_id': self.user_id,
            'creator_username': self.username,
            'creator_public_key': self.public_key_pem,
            'original_secret': os.path.basename(secret_file),
            'encrypted': use_encryption,
            'encryption_method': encryption_method,
            'password_used': password is not None
        }
        
        encrypted_keys = {}
        
        # Multi-recipient encryption (Approach 2)
        if use_encryption and recipients and len(recipients) > 0:
            print(f"[*] Setting up multi-recipient encryption for {len(recipients)} recipients...")
            try:
                from models import Database
                db = Database()
                
                # Get recipients' public keys
                recipients_public_keys = {}
                for rid in recipients:
                    try:
                        user = db.get_user_by_id(int(rid))
                        if user:
                            recipients_public_keys[int(rid)] = user['public_key']
                            print(f"[+] Retrieved public key for recipient {user['username']}")
                    except Exception as e:
                        print(f"[!] Error getting recipient {rid}: {e}")
                
                if recipients_public_keys:
                    # Use multi-recipient encryption
                    data, encrypted_keys, method = self.crypto.encrypt_for_recipients(data, recipients_public_keys)
                    metadata['encryption_method'] = 'MULTI_RECIPIENT'
                    print(f"[+] Data encrypted for {len(encrypted_keys)} recipients")
                else:
                    print("[!] No valid recipients found, falling back to creator-only encryption")
                    # Fallback to normal encryption with user's own key
                    if encryption_method == 'rsa':
                        data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                        metadata['encryption_method'] = method if method else 'RSA'
                    elif encryption_method == 'password':
                        if not password:
                            raise ValueError("Password required for password-only encryption")
                        data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                        metadata['encryption_method'] = 'AES'
                    elif encryption_method == 'hybrid':
                        if not password:
                            raise ValueError("Password required for hybrid encryption")
                        data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                        metadata['encryption_method'] = method if method else 'RSA+AES'
            except Exception as e:
                print(f"[!] Multi-recipient encryption failed: {e}, falling back to normal encryption")
                # Fallback to normal encryption
                if encryption_method == 'rsa':
                    data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                    metadata['encryption_method'] = method if method else 'RSA'
                elif encryption_method == 'password':
                    if not password:
                        raise ValueError("Password required for password-only encryption")
                    data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                    metadata['encryption_method'] = 'AES'
                elif encryption_method == 'hybrid':
                    if not password:
                        raise ValueError("Password required for hybrid encryption")
                    data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                    metadata['encryption_method'] = method if method else 'RSA+AES'
        
        # Normal encryption (single user)
        elif use_encryption:
            if encryption_method == 'rsa':
                # RSA-only encryption
                print(f"[*] Encrypting data with {self.username}'s RSA public key (RSA only)...")
                # Note: encrypt_data will automatically upgrade to hybrid if data is too large
                data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                # Update metadata with actual encryption method used
                metadata['encryption_method'] = method if method else 'RSA'
                print(f"[+] Encryption method: RSA")
                
            elif encryption_method == 'password':
                # Password-only encryption
                if not password:
                    raise ValueError("Password required for password-only encryption")
                print(f"[*] Encrypting data with password (AES only)...")
                data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                metadata['encryption_method'] = 'AES'
                print(f"[+] Encryption method: AES")
                
            elif encryption_method == 'hybrid':
                # Hybrid RSA + Password encryption
                if not password:
                    raise ValueError("Password required for hybrid encryption")
                print(f"[*] Encrypting data with {self.username}'s RSA key + password (Hybrid)...")
                data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                metadata['encryption_method'] = method if method else 'RSA+AES'
                print(f"[+] Encryption method: {metadata['encryption_method']} (Hybrid)")
            else:
                raise ValueError(f"Unknown encryption method: {encryption_method}")
        
        # Determine cover file type
        cover_ext = os.path.splitext(cover_file)[1].lower()[1:]
        
        # Hide data based on cover type
        if cover_ext in ['wav', 'mp3', 'flac', 'aiff']:
            print("[*] Using Audio Steganography...")
            output_path = self.audio_stego.encode(cover_file, output_file, data)
        
        elif cover_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            print("[*] Using Image Steganography...")
            output_path = self.image_stego.encode(cover_file, output_file, data)
        
        elif cover_ext in ['mp4', 'avi', 'mov', 'mkv']:
            print("[*] Using FFmpeg + FFV1 Lossless Video Steganography...")
            output_path = self.video_stego.encode(cover_file, output_file, data)
        
        else:
            raise ValueError(f"Unsupported cover file format: {cover_ext}")
        
        # Save metadata file for extraction reference (legacy support)
        metadata_file = output_path + '.meta'
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"[+] Metadata saved to: {metadata_file}")
        except Exception as e:
            print(f"[!] Warning: Could not save metadata file: {e}")
        
        # Metadata is now stored in the database, not as a separate file
        result = {
            'output_file': output_path,
            'creator': self.username,
            'creator_id': self.user_id,
            'encryption_method': metadata.get('encryption_method', 'RSA-AES'),
            'encrypted': use_encryption
        }
        
        # Include encrypted keys if multi-recipient
        if encrypted_keys:
            result['encrypted_keys'] = encrypted_keys
        
        return result
    
    def extract_file(self, stego_file, output_file, password=None, is_creator=False, encrypted_keys=None, encryption_method=None):
        """
        Extract hidden file from stego media
        Supports multi-recipient decryption (Approach 2)
        Supports multi-user extraction for shared files
        
        :param stego_file: Path to stego media file
        :param output_file: Path to save extracted file
        :param password: Password for decryption
        :param is_creator: Whether current user is the file creator (affects decryption)
        :param encrypted_keys: Dict of encrypted DEKs for multi-recipient decryption
        :param encryption_method: Actual encryption method used when hiding ('RSA', 'RSA+AES', 'password', 'hybrid', etc.)
        :return: Dict with extracted file path and metadata
        """
        # DEBUG: Log what was passed in
        print(f"\n{'='*80}")
        print(f"[EXTRACT-FILE] extract_file() called")
        print(f"[EXTRACT-FILE] stego_file: {stego_file}")
        print(f"[EXTRACT-FILE] output_file: {output_file}")
        print(f"[EXTRACT-FILE] password: {'***' if password else 'None'}")
        print(f"[EXTRACT-FILE] is_creator: {is_creator}")
        print(f"[EXTRACT-FILE] Current user: {self.username} (ID: {self.user_id}, type: {type(self.user_id).__name__})")
        print(f"[EXTRACT-FILE] encryption_method: {encryption_method}")
        print(f"[EXTRACT-FILE] encrypted_keys param: {encrypted_keys}")
        if encrypted_keys:
            print(f"[EXTRACT-FILE]   Type: {type(encrypted_keys).__name__}")
            print(f"[EXTRACT-FILE]   Keys: {list(encrypted_keys.keys())}")
            print(f"[EXTRACT-FILE]   Key types: {[type(k).__name__ for k in encrypted_keys.keys()]}")
        print(f"{'='*80}\n")
        
        # Metadata is now retrieved from database via API
        metadata = {}
        
        # Store the encryption method we'll use for decryption
        actual_encryption_method = encryption_method or 'hybrid'
        
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
            print("[*] Using RobustVideoSteganography (frame-based)...")
            data = self.video_stego.decode(stego_file)
        
        else:
            raise ValueError(f"Unsupported stego file format: {stego_ext}")
        
        # Multi-recipient decryption
        if encrypted_keys and len(encrypted_keys) > 0:
            print(f"\n[MULTI-RECIPIENT] Starting multi-recipient decryption")
            print(f"[MULTI-RECIPIENT] Encrypted keys dict: {encrypted_keys}")
            print(f"[MULTI-RECIPIENT] Dict key types: {[type(k).__name__ for k in encrypted_keys.keys()]}")
            print(f"[MULTI-RECIPIENT] Current user_id: {self.user_id} (type: {type(self.user_id).__name__})")
            print(f"[MULTI-RECIPIENT] Encrypted file detected with {len(encrypted_keys)} encrypted DEKs")
            print(f"[MULTI-RECIPIENT] Attempting decryption using recipient's private key...")
            try:
                # Check if current user has an encrypted DEK
                # NOTE: encrypted_keys dict has INTEGER keys (from database)
                user_id_int = int(self.user_id)
                
                # Debug: check all variations
                print(f"[DEBUG] Checking for user {user_id_int} in encrypted_keys")
                print(f"[DEBUG] user_id_int in encrypted_keys: {user_id_int in encrypted_keys}")
                print(f"[DEBUG] str(user_id_int) in encrypted_keys: {str(user_id_int) in encrypted_keys}")
                print(f"[DEBUG] Available user IDs in encrypted_keys: {list(encrypted_keys.keys())}")
                
                if user_id_int in encrypted_keys:
                    # BUG FIX: Use INTEGER key, not STRING key
                    encrypted_dek = encrypted_keys[user_id_int]  # FIX: was encrypted_keys[str(self.user_id)]
                    print(f"[+] Found encrypted DEK for current user (ID: {user_id_int})")
                    print(f"[DEBUG] Encrypted DEK type: {type(encrypted_dek)}")
                    
                    # Handle both string (hex) and bytes
                    if isinstance(encrypted_dek, str):
                        print(f"[DEBUG] Encrypted DEK is string (hex), length: {len(encrypted_dek)}")
                        print(f"[DEBUG] First 50 chars: {encrypted_dek[:50]}")
                    elif isinstance(encrypted_dek, bytes):
                        print(f"[DEBUG] Encrypted DEK is bytes, length: {len(encrypted_dek)}")
                        print(f"[DEBUG] First 50 bytes (hex): {encrypted_dek[:50].hex()}")
                    
                    # Decrypt using multi-recipient decryption
                    print(f"[MULTI-RECIPIENT] Decrypting data with user's private key...")
                    print(f"[DEBUG] Encrypted data size: {len(data)} bytes")
                    print(f"[DEBUG] Encrypted data (first 32 bytes hex): {data[:32].hex()}")
                    
                    try:
                        data = self.crypto.decrypt_from_recipients(data, encrypted_dek)
                        print(f"[MULTI-RECIPIENT] Decryption successful, {len(data)} bytes recovered")
                    except Exception as decrypt_error:
                        print(f"[!] CRITICAL ERROR during decryption: {decrypt_error}")
                        import traceback
                        print(f"[!] Traceback:\n{traceback.format_exc()}")
                        raise
                    
                    # Save extracted file
                    with open(output_file, 'wb') as f:
                        f.write(data)
                    
                    print(f"[+] Extracted file saved to: {output_file}")
                    print(f"[+] File size: {os.path.getsize(output_file)} bytes")
                    print(f"[+] Extraction completed by: {self.username} (creator={is_creator}) - Multi-recipient decryption")
                    
                    return {
                        'output_file': output_file,
                        'creator': metadata.get('creator_username', 'Unknown'),
                        'creator_id': metadata.get('creator_user_id', 'Unknown'),
                        'decryption_method': 'Multi-Recipient (User Private Key)',
                        'extracted': True,
                        'extracted_by': self.username,
                        'encryption_method': actual_encryption_method
                    }
                else:
                    print(f"[!] ERROR: Current user ({self.username}, ID: {user_id_int}) is NOT a recipient of this encrypted file")
                    print(f"[!] Available recipient IDs: {list(encrypted_keys.keys())}")
                    raise ValueError(f"User {user_id_int} is not a recipient of this file. Available recipients: {list(encrypted_keys.keys())}")
            
            except Exception as e:
                print(f"[!] ERROR: Multi-recipient decryption failed: {e}")
                import traceback
                print(f"[!] Traceback:\n{traceback.format_exc()}")
                print(f"[!] CRITICAL: This causes GARBAGE extracted files if data was saved unencrypted as fallback!")
                # IMPORTANT: Do NOT save unencrypted data - this causes garbage files!
                # Instead, raise the error so user knows decryption failed
                raise ValueError(f"Multi-recipient decryption failed for user {self.user_id}: {e}")
        
        # Decrypt if encrypted (normal single-user decryption)
        # Determine what password to pass for decryption based on encryption method
        actual_method = (actual_encryption_method or 'hybrid').strip().upper()
        
        if actual_method not in ['PLAINTEXT', 'NONE', '']:
            print(f"[*] File was encrypted with: {actual_encryption_method}")
            
            # Determine password requirements
            # RSA+AES requires password (it's hybrid: RSA key + password both needed)
            requires_password = actual_method in ['AES', 'PASSWORD', 'RSA+AES', 'RSA-AES']
            is_rsa_based = actual_method in ['RSA', 'RSA_CHUNKED']
            
            # For RSA-based decryption, verify that keys are paired correctly
            if is_rsa_based:
                print(f"\n[DIAGNOSTIC] Verifying RSA key pair before decryption...")
                keys_valid = self.crypto.rsa_handler.verify_key_pair()
                if not keys_valid:
                    print(f"[!] WARNING: RSA key pair verification FAILED")
                    print(f"[!] This means the file was likely encrypted with a different key")
                    print(f"[!] Possible causes:")
                    print(f"[!]   1. User account keys were regenerated (reset password, account migration)")
                    print(f"[!]   2. File was created by a different user account")
                    print(f"[!]   3. File corrupted or tampered with")
                    print(f"[!] Attempting decryption anyway, but expect failure...")
                print()
            
            if requires_password:
                if password is None or password == '':
                    raise ValueError("Password required for decryption of this file")
                print("[*] Decrypting data with password...")
                decrypt_password = password
            elif is_rsa_based:
                # RSA-only methods don't need password from user
                print(f"[*] Decrypting data with {actual_encryption_method} (RSA-based, no password needed)...")
                decrypt_password = None
            else:
                # Unknown method - try with password if provided
                print(f"[*] Unknown encryption method: {actual_encryption_method}, attempting decryption...")
                decrypt_password = password
            
            try:
                # Normalize method name for decrypt_data
                normalized_method = actual_method.replace('-', '+')  # Convert RSA-AES to RSA+AES
                
                # Convert high-level method names to crypto-specific names
                if normalized_method.upper() == 'HYBRID':
                    normalized_method = 'RSA+AES'
                elif normalized_method.upper() == 'PASSWORD':
                    normalized_method = 'AES'
                
                print(f"[*] Calling decrypt_data with method: {normalized_method}")
                decrypted = self.crypto.decrypt_data(data, decrypt_password, method=normalized_method)
                
                if decrypted is None or len(decrypted) == 0:
                    print("[!] Warning: Decryption returned empty data")
                    raise ValueError("Decryption failed: returned empty data")
                
                data = decrypted
                print(f"[+] Decryption successful, {len(data)} bytes")
                
            except Exception as e:
                print(f"[!] Decryption error: {str(e)}")
                # For RSA-based methods that failed, re-raise the error
                if is_rsa_based and is_creator:
                    raise
                # For password methods, always fail
                elif requires_password:
                    raise
                # Otherwise, try to continue with potentially encrypted data
                print("[*] Continuing with potentially encrypted data...")
        
        # Verify we have data to save
        if data is None or len(data) == 0:
            raise ValueError("No data to extract - result is empty after decryption")
        
        # Save extracted file
        with open(output_file, 'wb') as f:
            bytes_written = f.write(data)
        
        print(f"[+] Extracted file saved to: {output_file}")
        print(f"[+] File size: {bytes_written} bytes")
        print(f"[+] Extraction completed by: {self.username} (creator={is_creator})")
        
        return {
            'output_file': output_file,
            'creator': metadata.get('creator_username', 'Unknown'),
            'creator_id': metadata.get('creator_user_id', 'Unknown'),
            'encryption_method': actual_encryption_method,
            'extracted': True,
            'extracted_by': self.username
        }
    
    def hide_message(self, message, cover_file, output_file, password=None, use_encryption=True, encryption_method='hybrid', recipients=None):
        """
        Hide a text message inside a cover media
        Supports multi-recipient encryption (Approach 2)
        
        :param message: Text message to hide
        :param cover_file: Path to cover media
        :param output_file: Path to output file
        :param password: Password for encryption
        :param use_encryption: Whether to encrypt the message
        :param encryption_method: Encryption method - 'rsa', 'password', or 'hybrid'
        :param recipients: List of recipient user IDs for multi-recipient encryption
        :return: Dict with output path and metadata
        """
        # Validate encryption method
        if encryption_method not in ['rsa', 'password', 'hybrid']:
            raise ValueError(f"Invalid encryption method: {encryption_method}. Must be 'rsa', 'password', or 'hybrid'")
        
        # Handle empty messages
        if message == "":
            message = "\x00"
        
        data = message.encode('utf-8')
        
        # Create metadata
        metadata = {
            'creator_user_id': self.user_id,
            'creator_username': self.username,
            'creator_public_key': self.public_key_pem,
            'encrypted': use_encryption,
            'password_used': password is not None,
            'type': 'message'
        }
        
        encrypted_keys = {}
        
        # Multi-recipient encryption (Approach 2)
        if use_encryption and recipients and len(recipients) > 0:
            print(f"[*] Setting up multi-recipient encryption for {len(recipients)} recipients...")
            try:
                from models import Database
                db = Database()
                
                # Get recipients' public keys
                recipients_public_keys = {}
                for rid in recipients:
                    try:
                        user = db.get_user_by_id(int(rid))
                        if user:
                            recipients_public_keys[int(rid)] = user['public_key']
                            print(f"[+] Retrieved public key for recipient {user['username']}")
                    except Exception as e:
                        print(f"[!] Error getting recipient {rid}: {e}")
                
                if recipients_public_keys:
                    # Use multi-recipient encryption
                    data, encrypted_keys, method = self.crypto.encrypt_for_recipients(data, recipients_public_keys)
                    metadata['encryption_method'] = 'MULTI_RECIPIENT'
                    print(f"[+] Message encrypted for {len(encrypted_keys)} recipients")
                else:
                    print("[!] No valid recipients found, falling back to creator-only encryption")
                    # Fallback to normal encryption with user's own key
                    if encryption_method == 'rsa':
                        data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                        metadata['encryption_method'] = method
                    elif encryption_method == 'password':
                        if password is None or password == '':
                            raise ValueError("Password required for password-only encryption")
                        data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                        metadata['encryption_method'] = method
                    elif encryption_method == 'hybrid':
                        if password is None or password == '':
                            raise ValueError("Password required for hybrid encryption")
                        data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                        metadata['encryption_method'] = method
            except Exception as e:
                print(f"[!] Multi-recipient encryption failed: {e}, falling back to normal encryption")
                # Fallback to normal encryption
                if encryption_method == 'rsa':
                    data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                    metadata['encryption_method'] = method
                elif encryption_method == 'password':
                    if password is None or password == '':
                        raise ValueError("Password required for password-only encryption")
                    data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                    metadata['encryption_method'] = method
                elif encryption_method == 'hybrid':
                    if password is None or password == '':
                        raise ValueError("Password required for hybrid encryption")
                    data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                    metadata['encryption_method'] = method
        
        # Normal encryption (single user)
        elif use_encryption:
            if encryption_method == 'rsa':
                print(f"[*] Encrypting message with {self.username}'s RSA key only...")
                data, method = self.crypto.encrypt_data(data, password=None, use_rsa=True, pure_rsa=True)
                metadata['encryption_method'] = method
                print(f"[+] Encryption method: {method}")
            elif encryption_method == 'password':
                if password is None or password == '':
                    raise ValueError("Password required for password-only encryption")
                print(f"[*] Encrypting message with password only (AES)...")
                data, method = self.crypto.encrypt_data(data, password, use_rsa=False)
                metadata['encryption_method'] = method
                print(f"[+] Encryption method: {method}")
            elif encryption_method == 'hybrid':
                if password is None or password == '':
                    raise ValueError("Password required for hybrid encryption")
                print(f"[*] Encrypting message with {self.username}'s RSA key + password (hybrid)...")
                data, method = self.crypto.encrypt_data(data, password, use_rsa=True)
                metadata['encryption_method'] = method
                print(f"[+] Encryption method: {method}")
        
        # Determine cover file type and hide message
        cover_ext = os.path.splitext(cover_file)[1].lower()[1:]
        
        if cover_ext in ['wav', 'mp3', 'flac', 'aiff']:
            output_path = self.audio_stego.encode(cover_file, output_file, data)
        elif cover_ext in ['png', 'bmp', 'tiff', 'jpg', 'jpeg']:
            output_path = self.image_stego.encode(cover_file, output_file, data)
        elif cover_ext in ['mp4', 'avi', 'mov', 'mkv']:
            print("[*] Using DCT-based Video Steganography (robust to compression)...")
            output_path = self.video_stego.encode(cover_file, output_file, data)
        else:
            raise ValueError(f"Unsupported cover file format: {cover_ext}")
        
        # Metadata is now stored in the database, not as a separate file
        result = {
            'output_file': output_path,
            'creator': self.username,
            'creator_id': self.user_id,
            'encryption_method': encryption_method,
            'encrypted': use_encryption
        }
        
        # Include encrypted keys if multi-recipient
        if encrypted_keys:
            result['encrypted_keys'] = encrypted_keys
        
        return result
    
    def extract_message(self, stego_file, password=None, is_creator=False, encrypted_keys=None, encryption_method=None):
        """
        Extract hidden message from stego media
        Supports multi-recipient decryption (Approach 2)
        Supports multi-user extraction for shared files
        
        :param stego_file: Path to stego media file
        :param password: Password for decryption
        :param is_creator: Whether current user is the file creator
        :param encrypted_keys: Dict of encrypted DEKs for multi-recipient decryption
        :param encryption_method: Actual encryption method used when hiding ('RSA', 'RSA+AES', 'password', 'hybrid', etc.)
        :return: Dict with extracted message and metadata
        """
        # Metadata is now retrieved from database via API
        metadata = {}
        
        # Store the encryption method we'll use for decryption
        actual_encryption_method = encryption_method or 'hybrid'
        
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
            print("[*] Using RobustVideoSteganography (frame-based)...")
            data = self.video_stego.decode(stego_file)
        else:
            raise ValueError(f"Unsupported stego file format: {stego_ext}")
        
        # Multi-recipient decryption
        if encrypted_keys and len(encrypted_keys) > 0:
            print(f"[*] Multi-recipient encrypted message detected with {len(encrypted_keys)} encrypted DEKs")
            print(f"[*] Attempting decryption using recipient's private key...")
            try:
                # Check if current user has an encrypted DEK
                # NOTE: encrypted_keys dict has INTEGER keys (from database)
                user_id_int = int(self.user_id)
                
                if user_id_int in encrypted_keys:
                    # BUG FIX: Use INTEGER key, not STRING key
                    encrypted_dek = encrypted_keys[user_id_int]  # FIX: was encrypted_keys[str(self.user_id)]
                    print(f"[+] Found encrypted DEK for current user")
                    
                    # Decrypt using multi-recipient decryption
                    data = self.crypto.decrypt_from_recipients(data, encrypted_dek)
                    
                    # Decode message
                    try:
                        message = data.decode('utf-8').rstrip('\x00')  # Remove null padding
                    except Exception as e:
                        message = str(data)  # Fallback if decode fails
                        print(f"[!] Warning: Could not decode message as UTF-8: {e}")
                    
                    print(f"[+] Message extraction completed by: {self.username} (creator={is_creator}) - Multi-recipient decryption")
                    
                    return {
                        'message': message,
                        'creator': metadata.get('creator_username', 'Unknown'),
                        'creator_id': metadata.get('creator_user_id', 'Unknown'),
                        'decryption_method': 'Multi-Recipient (User Private Key)',
                        'extracted_by': self.username,
                        'encryption_method': actual_encryption_method
                    }
                else:
                    print(f"[!] Current user ({self.username}, ID: {user_id_int}) is not a recipient of this encrypted message")
                    print(f"[!] Available recipient IDs: {list(encrypted_keys.keys())}")
                    return {
                        'status': 'error',
                        'message': 'Current user is not a recipient',
                        'available_recipients': list(encrypted_keys.keys())
                    }
            
            except Exception as e:
                print(f"[!] Multi-recipient decryption failed: {e}")
                import traceback
                print(f"[!] Traceback:\n{traceback.format_exc()}")
                print(f"[!] CRITICAL: Must not use fallback - will save encrypted data as garbage!")
                # IMPORTANT: Do NOT save encrypted data - this causes garbage files!
                # Instead, raise the error so user knows decryption failed
                raise ValueError(f"Multi-recipient decryption failed for user {self.user_id}: {e}")
        
        # Decrypt if encrypted (normal single-user decryption)
        # Determine what password to pass for decryption based on encryption method
        actual_method = (actual_encryption_method or 'hybrid').strip().upper()
        
        if actual_method not in ['PLAINTEXT', 'NONE', '']:
            print(f"[*] File was encrypted with: {actual_encryption_method}")
            
            # Determine password requirements
            requires_password = actual_method in ['AES', 'PASSWORD']
            is_rsa_based = actual_method in ['RSA', 'RSA_CHUNKED', 'RSA+AES', 'RSA-AES']
            
            if requires_password:
                if password is None or password == '':
                    raise ValueError("Password required for decryption of this file")
                print("[*] Decrypting message with password...")
                decrypt_password = password
            elif is_rsa_based:
                # RSA-based methods don't need password from user
                print(f"[*] Decrypting message with {actual_encryption_method} (RSA-based, no password needed)...")
                decrypt_password = None
            else:
                # Unknown method - try with password if provided
                print(f"[*] Unknown encryption method: {actual_encryption_method}, attempting decryption...")
                decrypt_password = password
            
            try:
                # Normalize method name for decrypt_data
                normalized_method = actual_method.replace('-', '+')  # Convert RSA-AES to RSA+AES
                
                # Convert high-level method names to crypto-specific names
                if normalized_method.upper() == 'HYBRID':
                    normalized_method = 'RSA+AES'
                elif normalized_method.upper() == 'PASSWORD':
                    normalized_method = 'AES'
                
                print(f"[*] Calling decrypt_data with method: {normalized_method}")
                decrypted = self.crypto.decrypt_data(data, decrypt_password, method=normalized_method)
                
                if decrypted is None or len(decrypted) == 0:
                    print("[!] Warning: Decryption returned empty data")
                    raise ValueError("Decryption failed: returned empty data")
                
                data = decrypted
                print(f"[+] Decryption successful, {len(data)} bytes")
                
            except Exception as e:
                print(f"[!] Decryption error: {str(e)}")
                # For RSA-based methods that failed, re-raise the error
                if is_rsa_based and is_creator:
                    raise
                # For password methods, always fail
                elif requires_password:
                    raise
                # Otherwise, try to continue with potentially encrypted data
                print("[*] Continuing with potentially encrypted data...")
        
        # Verify we have data to decode
        if data is None or len(data) == 0:
            raise ValueError("No data to extract - result is empty after decryption")
        
        # Decode message
        try:
            message = data.decode('utf-8').rstrip('\x00')  # Remove null padding
        except Exception as e:
            message = str(data)  # Fallback if decode fails
            print(f"[!] Warning: Could not decode message as UTF-8: {e}")
        
        print(f"[+] Message extraction completed by: {self.username} (creator={is_creator})")
        
        return {
            'message': message,
            'creator': metadata.get('creator_username', 'Unknown'),
            'creator_id': metadata.get('creator_user_id', 'Unknown'),
            'encryption_method': actual_encryption_method,
            'extracted_by': self.username
        }
