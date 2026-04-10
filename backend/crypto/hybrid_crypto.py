"""
Hybrid Encryption Module
Combines RSA and AES encryption for secure and efficient file encryption
"""
from crypto.rsa_handler import RSAHandler
from crypto.aes_handler import AESHandler
import os


class HybridCrypto:
    """
    Hybrid encryption combining RSA and AES:
    - Small files: Direct RSA encryption
    - Large files: AES encryption with password
    - Optional: RSA + AES for maximum security
    """
    
    def __init__(self, key_dir='keys'):
        """
        Initialize Hybrid Crypto handler
        
        :param key_dir: Directory for RSA keys
        """
        self.rsa_handler = RSAHandler(key_dir)
        self.aes_handler = AESHandler()
        self.rsa_threshold = 200  # Maximum safe bytes for direct RSA encryption (leaves room for padding)
    
    def encrypt_data(self, data, password=None, use_rsa=True, pure_rsa=False):
        """
        Encrypt data using hybrid approach
        
        :param data: Data to encrypt (bytes)
        :param password: Password for encryption (optional for RSA, required for AES)
        :param use_rsa: Whether to use RSA (if applicable)
        :param pure_rsa: Force RSA-only encryption using chunks for large data
        :return: Tuple (encrypted_data, encryption_method)
        """
        data_size = len(data)
        print(f"\n{'='*80}")
        print(f"[ENCRYPT-DATA] encrypt_data() called")
        print(f"[ENCRYPT-DATA] data_size: {data_size} bytes")
        print(f"[ENCRYPT-DATA] use_rsa: {use_rsa}")
        print(f"[ENCRYPT-DATA] pure_rsa: {pure_rsa}")
        print(f"[ENCRYPT-DATA] password provided: {password is not None}")
        print(f"[ENCRYPT-DATA] RSA keys available: {self.rsa_handler.keys_exist()}")
        print(f"{'='*80}\n")
        
        # Smart RSA fallback: if pure_rsa is requested but data is large, use RSA chunking instead of hybrid
        if pure_rsa and data_size > self.rsa_threshold and self.rsa_handler.keys_exist():
            print(f"[*] Data too large for single RSA block ({data_size} bytes > {self.rsa_threshold} bytes)")
            print("[*] Using RSA chunking for large data (no password needed)")
            # Use RSA chunking instead of auto-upgrading to hybrid
            # This way, user-selected RSA-only stays RSA-only without auto-password
            try:
                encrypted = self._encrypt_rsa_chunks(data)
                if encrypted:
                    return encrypted, 'RSA_CHUNKED'
                else:
                    print("[!] Pure RSA encryption failed")
                    raise Exception("Pure RSA encryption failed")
            except Exception as e:
                print(f"[!] RSA chunking failed: {e}, falling back to hybrid encryption")
                # Fallback to hybrid only if chunking fails
                # Generate a random password and use hybrid encryption
                import secrets
                auto_password = secrets.token_hex(16)  # 32-char random password
                password = auto_password
                # Continue to hybrid encryption below
        
        # Force pure RSA mode (chunk large files)
        if pure_rsa and self.rsa_handler.keys_exist():
            print(f"[*] Using pure RSA encryption with chunking for data ({data_size} bytes)")
            try:
                encrypted = self._encrypt_rsa_chunks(data)
                if encrypted:
                    return encrypted, 'RSA_CHUNKED'
                else:
                    print("[!] Pure RSA encryption failed")
                    raise Exception("Pure RSA encryption failed")
            except Exception as e:
                print(f"[!] Pure RSA encryption failed: {e}")
                raise
        
        # If password provided and RSA requested, use password-protected RSA
        # For small data: single RSA, for large data: RSA chunked
        if password is not None and use_rsa and self.rsa_handler.keys_exist():
            print(f"[*] Using password-protected RSA encryption for data ({data_size} bytes)")
            try:
                if data_size <= self.rsa_threshold:
                    # Small data: single RSA encryption
                    print(f"[*] Using single RSA block for small data")
                    rsa_encrypted = self.rsa_handler.encrypt(data)
                else:
                    # Large data: RSA chunking
                    print(f"[*] Using RSA chunking for large data")
                    rsa_encrypted = self._encrypt_rsa_chunks(data)
                
                if rsa_encrypted:
                    # Second layer: encrypt with AES using password
                    aes_encrypted = self.aes_handler.encrypt(rsa_encrypted, password)
                    if aes_encrypted:
                        print(f"[ENCRYPT] RSA+AES successful: {len(rsa_encrypted)} bytes RSA → {len(aes_encrypted)} bytes AES")
                        return aes_encrypted, 'RSA+AES'
                    else:
                        print("[!] AES encryption of RSA data failed")
                else:
                    print("[!] RSA encryption failed")
            except Exception as e:
                print(f"[!] Password-protected RSA encryption failed: {e}")
        
        # Priority 1: RSA for small data (no password)
        if password is None and use_rsa and data_size <= self.rsa_threshold and self.rsa_handler.keys_exist():
            print(f"[*] Using RSA encryption for small data ({data_size} bytes)")
            try:
                encrypted = self.rsa_handler.encrypt(data)
                if encrypted:
                    return encrypted, 'RSA'
                else:
                    print("[!] RSA encryption failed, falling back to AES")
            except Exception as e:
                print(f"[!] RSA encryption failed: {e}, falling back to AES")
        elif use_rsa and data_size <= self.rsa_threshold:
            print("[!] RSA keys not found, using AES encryption")
        
        # Priority 2: AES with password
        if password is not None:
            print(f"[*] Using AES encryption for data ({data_size} bytes)")
            encrypted = self.aes_handler.encrypt(data, password)
            if encrypted:
                return encrypted, 'AES'
            else:
                raise Exception("AES encryption failed")
        
        # Fallback: require password for AES
        raise ValueError("Password required for encryption (RSA not available or data too large)")
    
    def decrypt_data(self, encrypted_data, password=None, method='AUTO'):
        """
        Decrypt data
        
        :param encrypted_data: Encrypted data
        :param password: Password for AES decryption
        :param method: Decryption method ('RSA', 'AES', or 'AUTO')
        :return: Decrypted data
        """
        # Auto-detect method based on size and characteristics
        if method == 'AUTO':
            # Check for RSA chunked data first
            if encrypted_data.startswith(b'RSA_CHUNKED_V1:'):
                method = 'RSA_CHUNKED'
                print(f"[*] Auto-detected RSA chunked encryption ({len(encrypted_data)} bytes)")
            # RSA encrypted data is typically 256 bytes for 2048-bit key
            # AES encrypted data has salt(16) + IV(16) + HMAC(32) + ciphertext, so minimum 80 bytes
            elif len(encrypted_data) == 256:
                method = 'RSA'
                print(f"[*] Auto-detected RSA encryption (exact 256 bytes)")
            elif len(encrypted_data) in [128, 384, 512]:  # Other common RSA sizes
                method = 'RSA' 
                print(f"[*] Auto-detected RSA encryption ({len(encrypted_data)} bytes)")
            elif len(encrypted_data) < 80:
                # Too short for AES (needs at least 80 bytes), must be RSA or error
                method = 'RSA'
                print(f"[*] Auto-detected RSA encryption (short data: {len(encrypted_data)} bytes)")
            else:
                # For larger data with password, could be AES or RSA+AES
                if password is not None:
                    # Try RSA+AES first if password provided and RSA keys exist
                    if self.rsa_handler.keys_exist():
                        method = 'RSA+AES'
                        print(f"[*] Auto-detected password-protected RSA encryption ({len(encrypted_data)} bytes)")
                    else:
                        method = 'AES'
                        print(f"[*] Auto-detected AES encryption (large data with password: {len(encrypted_data)} bytes)")
                else:
                    # No password - try RSA if keys exist
                    if self.rsa_handler.keys_exist():
                        method = 'RSA'
                        print(f"[*] Auto-detected RSA encryption (no password, keys exist: {len(encrypted_data)} bytes)")
                    else:
                        raise ValueError("Cannot decrypt: no password provided and no RSA keys found")
        
        print(f"[*] Using {method} decryption method")
        
        if method == 'RSA+AES':
            if password is None:
                raise ValueError("Password required for RSA+AES decryption")
            
            print("[*] Attempting RSA+AES decryption...")
            if not self.rsa_handler.keys_exist():
                raise ValueError("RSA keys not found for RSA+AES decryption")
            
            try:
                # First decrypt with AES to get RSA-encrypted data
                rsa_encrypted_data = self.aes_handler.decrypt(encrypted_data, password)
                print(f"[+] AES layer decrypted successfully, got {len(rsa_encrypted_data)} bytes of RSA-encrypted data")
                
                # Then decrypt with RSA - check if chunked or single block
                key_size = self.rsa_handler.public_key.size_in_bits() // 8
                print(f"[*] RSA key size: {key_size} bytes, Data size: {len(rsa_encrypted_data)} bytes")
                
                # Check for RSA_CHUNKED format first
                if len(rsa_encrypted_data) > 15 and rsa_encrypted_data.startswith(b'RSA_CHUNKED_V1:'):
                    print(f"[*] Detected RSA_CHUNKED_V1 format in decrypted data")
                    decrypted = self._decrypt_rsa_chunks(rsa_encrypted_data)
                elif len(rsa_encrypted_data) > key_size + 100:
                    # Large data: likely chunked
                    print(f"[*] Large RSA-encrypted data ({len(rsa_encrypted_data)} bytes) - attempting dechunk...")
                    
                    # If data doesn't have RSA_CHUNKED_V1 header but is large, assume it's chunked data
                    if not rsa_encrypted_data.startswith(b'RSA_CHUNKED_V1:'):
                        print(f"[!] Large data without RSA_CHUNKED_V1 header - prepending header...")
                        # Assume data is chunked format (size_header + chunk)* and prepend the marker
                        rsa_encrypted_data = b'RSA_CHUNKED_V1:' + rsa_encrypted_data
                    
                    try:
                        print(f"[*] Using RSA dechunking for large RSA-encrypted data")
                        decrypted = self._decrypt_rsa_chunks(rsa_encrypted_data)
                    except ValueError as chunk_error:
                        # Chunk decryption failed - might be recovery case
                        if "chunk" in str(chunk_error).lower():
                            print(f"[!] RSA chunk decryption failed: {chunk_error}")
                            raise ValueError(f"RSA+AES decryption failed: {chunk_error}")
                        else:
                            raise
                else:
                    # Small data: single RSA block
                    print(f"[*] Using single RSA block for small RSA-encrypted data")
                    decrypted = self.rsa_handler.decrypt(rsa_encrypted_data)
                
                if decrypted:
                    print("[+] RSA layer decrypted successfully")
                    return decrypted
                else:
                    raise ValueError("RSA decryption returned empty result - file may be corrupted or wrong password used")
            except ValueError as e:
                # AES HMAC verification failed = wrong password
                if "HMAC verification failed" in str(e):
                    raise ValueError(f"Incorrect password - RSA+AES decryption failed: {e}")
                # RSA decryption failed - could be key mismatch or corruption
                else:
                    error_msg = str(e)
                    if "key mismatch" in error_msg.lower() or "chunk" in error_msg.lower():
                        raise ValueError(f"RSA+AES decryption failed: {e}\n[DEBUG] Possible causes:\n"
                                       f"  1. Account keys were regenerated after file creation\n"
                                       f"  2. File was encrypted with different user's key\n"
                                       f"  3. File corrupted during extraction from stego media")
                    else:
                        raise ValueError(f"RSA+AES decryption failed: {e}. Wrong password or corrupted file.")
            except Exception as e:
                raise ValueError(f"RSA+AES decryption failed: {e}. File may not be encrypted with RSA+AES or wrong password.")
        
        if method == 'RSA_CHUNKED':
            print("[*] Using RSA chunked decryption...")
            if not self.rsa_handler.keys_exist():
                raise ValueError("RSA keys not found for chunked decryption")
            try:
                decrypted = self._decrypt_rsa_chunks(encrypted_data)
                return decrypted
            except Exception as e:
                raise ValueError(f"RSA chunked decryption failed: {e}")
        
        if method == 'RSA':
            print("[*] Attempting RSA decryption...")
            if not self.rsa_handler.keys_exist():
                print("[!] RSA keys not found")
                if password is not None:
                    print("[!] Falling back to AES decryption...")
                    method = 'AES'
                else:
                    raise ValueError("RSA keys not found and no password provided for AES")
            else:
                try:
                    # Check if this is chunked or single block
                    key_size = self.rsa_handler.public_key.size_in_bits() // 8
                    print(f"[*] RSA key size: {key_size} bytes, Data size: {len(encrypted_data)} bytes")
                    
                    if len(encrypted_data) > key_size + 100:
                        # Large data: use RSA dechunking
                        print(f"[*] Using RSA dechunking for large encrypted data")
                        decrypted = self._decrypt_rsa_chunks(encrypted_data)
                    else:
                        # Small data: single RSA block
                        print(f"[*] Using single RSA block for small encrypted data")
                        decrypted = self.rsa_handler.decrypt(encrypted_data)
                    
                    if decrypted:
                        return decrypted
                    else:
                        print("[!] RSA decryption returned empty result")
                        if password is not None:
                            print("[!] Trying AES decryption...")
                            method = 'AES'
                        else:
                            raise ValueError("RSA decryption failed and no password provided for AES")
                except Exception as e:
                    print(f"[!] RSA decryption failed: {e}")
                    if password is not None:
                        print("[!] Trying AES decryption...")
                        method = 'AES'
                    else:
                        raise ValueError(f"RSA decryption failed: {e}")
        
        if method == 'AES':
            if password is None:
                raise ValueError("Password required for AES decryption")
            
            print("[*] Using AES decryption...")
            try:
                decrypted = self.aes_handler.decrypt(encrypted_data, password)
                return decrypted
            except ValueError as e:
                # AES errors are usually password-related, don't try RSA fallback
                raise ValueError(f"AES decryption failed: {e}")
            except Exception as e:
                raise Exception(f"Decryption failed: {e}")
        
        raise ValueError(f"Unknown decryption method: {method}")
    
    def encrypt_file(self, input_file, output_file=None, password=None, use_rsa=True):
        """
        Encrypt a file
        
        :param input_file: Path to input file
        :param output_file: Path to output file (optional)
        :param password: Password for encryption
        :param use_rsa: Whether to use RSA for small files
        :return: Path to encrypted file
        """
        # Read input file
        try:
            with open(input_file, 'rb') as f:
                data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Encrypt data
        encrypted_data, method = self.encrypt_data(data, password, use_rsa)
        
        # Determine output file path
        if output_file is None:
            output_file = input_file + '.enc'
        
        # Write encrypted data
        with open(output_file, 'wb') as f:
            # Write encryption method marker (1 byte)
            method_marker = b'R' if method == 'RSA' else b'A'
            f.write(method_marker)
            f.write(encrypted_data)
        
        print(f"[+] File encrypted successfully: {output_file}")
        print(f"[+] Encryption method: {method}")
        return output_file
    
    def decrypt_file(self, input_file, output_file=None, password=None):
        """
        Decrypt a file
        
        :param input_file: Path to encrypted file
        :param output_file: Path to output file (optional)
        :param password: Password for decryption
        :return: Path to decrypted file
        """
        # Read encrypted file
        try:
            with open(input_file, 'rb') as f:
                method_marker = f.read(1)
                encrypted_data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Determine decryption method
        if method_marker == b'R':
            method = 'RSA'
        elif method_marker == b'A':
            method = 'AES'
        else:
            # Legacy file without marker
            method = 'AUTO'
            # Re-read entire file
            with open(input_file, 'rb') as f:
                encrypted_data = f.read()
        
        # Decrypt data
        decrypted_data = self.decrypt_data(encrypted_data, password, method)
        
        # Determine output file path
        if output_file is None:
            if input_file.endswith('.enc'):
                output_file = input_file[:-4]
            else:
                output_file = input_file + '.dec'
        
        # Write decrypted data
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        
        print(f"[+] File decrypted successfully: {output_file}")
        return output_file
    
    def encrypt_for_recipients(self, data, recipients_public_keys):
        """
        Encrypt data for multiple recipients (Approach 2: Multi-Recipient Encryption)
        
        - Generate random master AES key
        - Encrypt data with master key
        - Encrypt master key with each recipient's public key
        
        :param data: Data to encrypt (bytes)
        :param recipients_public_keys: Dict of {recipient_id: public_key_pem}
        :return: Tuple (encrypted_data, encrypted_master_keys_dict, method)
        
        Example:
            recipients = {
                1: "-----BEGIN PUBLIC KEY-----\n...",
                2: "-----BEGIN PUBLIC KEY-----\n..."
            }
            enc_data, enc_keys, method = crypto.encrypt_for_recipients(data, recipients)
        """
        print(f"[*] Setting up multi-recipient encryption for {len(recipients_public_keys)} recipients...")
        
        try:
            # Step 1: Generate a random master AES key
            import secrets
            master_key = secrets.token_bytes(32)  # 256-bit AES key
            print(f"[+] Generated 256-bit master key")
            
            # Step 2: Encrypt data with master key
            print(f"[*] Encrypting data with master AES key ({len(data)} bytes)...")
            encrypted_data = self.aes_handler.encrypt(data, None)  # Will use random key from data, we'll override
            
            # Actually encrypt with our specific master key
            from Crypto.Cipher import AES
            from Crypto.Random import get_random_bytes
            cipher = AES.new(master_key, AES.MODE_GCM)
            encrypted_data, tag = cipher.encrypt_and_digest(data)
            # Prepend IV and tag
            encrypted_data_with_iv = cipher.nonce + tag + encrypted_data
            print(f"[+] Encrypted data with master key ({len(encrypted_data_with_iv)} bytes)")
            
            # Step 3: Encrypt master key for each recipient
            encrypted_keys = {}
            for recipient_id, public_key_pem in recipients_public_keys.items():
                try:
                    encrypted_key = self.rsa_handler.encrypt_with_public_key(master_key, public_key_pem)
                    if encrypted_key:
                        encrypted_keys[recipient_id] = encrypted_key.hex()  # Store as hex string
                        print(f"[+] Encrypted master key for recipient {recipient_id}")
                    else:
                        print(f"[!] Failed to encrypt key for recipient {recipient_id}")
                except Exception as e:
                    print(f"[!] Error encrypting for recipient {recipient_id}: {e}")
            
            if not encrypted_keys:
                raise Exception("Failed to encrypt master key for any recipient")
            
            print(f"[+] Multi-recipient encryption complete: {len(encrypted_keys)} recipients")
            return encrypted_data_with_iv, encrypted_keys, 'MULTI_RECIPIENT'
        
        except Exception as e:
            print(f"[!] Multi-recipient encryption failed: {e}")
            raise
    
    def decrypt_from_recipients(self, encrypted_data, encrypted_master_key_hex):
        """
        Decrypt multi-recipient encrypted data
        
        - Decrypt the master key using recipient's private key
        - Decrypt data using the master key
        
        :param encrypted_data: Data encrypted with AES master key (format: nonce(16) + tag(16) + ciphertext)
        :param encrypted_master_key_hex: Master key encrypted with recipient's RSA public key (hex string)
        :return: Decrypted data (bytes)
        
        Example:
            # After User 2 retrieves their encrypted DEK from database
            encrypted_dek_hex = "a1b2c3d4e5f6..."  # From database
            plaintext = crypto.decrypt_from_recipients(encrypted_data, encrypted_dek_hex)
        """
        try:
            print(f"[*] Starting multi-recipient decryption")
            print(f"[DEBUG] encrypted_master_key_hex type: {type(encrypted_master_key_hex)}")
            print(f"[DEBUG] encrypted_master_key_hex (first 50 chars): {str(encrypted_master_key_hex)[:50]}")
            
            # Step 1: Convert hex string back to bytes if needed
            if isinstance(encrypted_master_key_hex, str):
                try:
                    encrypted_master_key_bytes = bytes.fromhex(encrypted_master_key_hex)
                    print(f"[+] Converted hex string to bytes ({len(encrypted_master_key_bytes)} bytes)")
                except ValueError as e:
                    print(f"[!] ERROR: Invalid hex string for encrypted master key: {e}")
                    raise ValueError(f"Encrypted master key is not valid hex: {e}")
            else:
                encrypted_master_key_bytes = encrypted_master_key_hex
                print(f"[+] Using encrypted master key as bytes ({len(encrypted_master_key_bytes)} bytes)")
            
            # Step 2: Decrypt master key using recipient's private key
            if self.rsa_handler.private_key is None:
                raise ValueError("Private key not loaded - cannot decrypt master key")
            
            print(f"[*] Decrypting master key with recipient's private key...")
            master_key = self.rsa_handler.decrypt(encrypted_master_key_bytes)
            
            if master_key is None or len(master_key) == 0:
                raise ValueError("Failed to decrypt master key - returned None or empty")
            
            print(f"[+] Master key decrypted successfully ({len(master_key)} bytes)")
            
            # Step 3: Decrypt data with master key
            print(f"[*] Decrypting data with master key...")
            
            # encrypted_data format: nonce(16) + tag(16) + ciphertext
            if len(encrypted_data) < 32:
                raise ValueError(f"Encrypted data too short ({len(encrypted_data)} bytes, need >= 32)")
            
            nonce = encrypted_data[:16]
            tag = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]
            
            from Crypto.Cipher import AES
            try:
                cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
                plaintext = cipher.decrypt_and_verify(ciphertext, tag)
                print(f"[+] Data decrypted successfully ({len(plaintext)} bytes)")
                return plaintext
            except ValueError as e:
                print(f"[!] ERROR: Authentication tag verification failed - data may be corrupted or wrong key")
                raise ValueError(f"GCM tag verification failed: {e}")
            
        except Exception as e:
            print(f"[!] ERROR in decrypt_from_recipients: {e}")
            import traceback
            print(f"[!] Traceback:\n{traceback.format_exc()}")
            raise
    
    def decrypt_with_master_key(self, encrypted_data, encrypted_master_key_hex):
        """
        Decrypt data using master key that has been decrypted
        
        :param encrypted_data: Data encrypted with master key (includes IV and tag)
        :param encrypted_master_key_hex: Master key encrypted with recipient's public key (hex string)
        :return: Decrypted data
        """
        try:
            # This will be called after the recipient has decrypted their master key
            # encrypted_data format: nonce(16) + tag(16) + ciphertext
            encrypted_data_bytes = bytes.fromhex(encrypted_data) if isinstance(encrypted_data, str) else encrypted_data
            
            nonce = encrypted_data_bytes[:16]
            tag = encrypted_data_bytes[16:32]
            ciphertext = encrypted_data_bytes[32:]
            
            from Crypto.Cipher import AES
            cipher = AES.new(self.master_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            print(f"[+] Decrypted data with master key ({len(plaintext)} bytes)")
            return plaintext
        except Exception as e:
            print(f"[!] Decryption with master key failed: {e}")
            raise
    
    def _encrypt_rsa_chunks(self, data):
        """
        Encrypt large data using RSA by splitting into chunks
        
        :param data: Data to encrypt
        :return: Encrypted data with chunk markers
        """
        chunk_size = 200  # Safe chunk size for RSA 2048-bit keys (with padding)
        chunks = []
        
        print(f"\n[ENCRYPT-RSA-CHUNKS] Starting RSA chunk encryption for {len(data)} bytes")
        
        # Verify public key is loaded
        if self.rsa_handler.public_key is None:
            print("[!] Public key not loaded, attempting to load...")
            if not self.rsa_handler.load_public_key():
                raise ValueError("Failed to load public key for RSA chunking")
        
        print(f"[ENCRYPT-RSA-CHUNKS] Public key loaded: {self.rsa_handler.public_key is not None}")
        
        # Add header to identify chunked RSA
        result = b'RSA_CHUNKED_V1:'
        
        # Encrypt each chunk
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        for i, start in enumerate(range(0, len(data), chunk_size)):
            chunk = data[start:start + chunk_size]
            print(f"[ENCRYPT-RSA-CHUNKS] Encrypting chunk {i+1}/{total_chunks} ({len(chunk)} bytes)")
            try:
                encrypted_chunk = self.rsa_handler.encrypt(chunk)
                if not encrypted_chunk:
                    raise ValueError(f"Chunk {i+1} encryption returned None")
                
                # Add chunk size header (2 bytes) + encrypted chunk
                chunk_header = len(encrypted_chunk).to_bytes(2, 'big')
                chunks.append(chunk_header + encrypted_chunk)
                print(f"[ENCRYPT-RSA-CHUNKS] Chunk {i+1} encrypted: {len(chunk)} → {len(chunk_header) + len(encrypted_chunk)} bytes")
            except Exception as e:
                print(f"[!] Chunk {i+1} encryption failed: {e}")
                raise
        
        # Combine all chunks
        result += b''.join(chunks)
        print(f"[ENCRYPT-RSA-CHUNKS] Successfully encrypted {total_chunks} chunks, total size: {len(result)} bytes")
        print(f"[ENCRYPT-RSA-CHUNKS] Result format: RSA_CHUNKED_V1: (15 bytes) + {len(b''.join(chunks))} bytes of chunks\n")
        return result
    
    def _attempt_rsa_chunk_recovery(self, encrypted_data):
        """
        Attempt to recover RSA chunked data if headers are corrupted
        
        :param encrypted_data: Potentially corrupted RSA chunked data
        :return: Recovered chunks list or None
        """
        print(f"[DEBUG-RSA-RECOVERY] Attempting chunk recovery on {len(encrypted_data)} bytes...")
        
        key_size = 256  # RSA-2048
        recovered_chunks = []
        
        # Try to find RSA-sized chunks (256 bytes for RSA-2048)
        # Scan data looking for valid chunk patterns
        pos = 0
        chunk_count = 0
        
        # First, try skipping the header if present and re-align to chunk boundary
        if encrypted_data.startswith(b'RSA_CHUNKED_V1:'):
            data = encrypted_data[15:]
        else:
            data = encrypted_data
            
        # Try to find chunks by looking for 2-byte size headers that make sense
        while pos + 2 < len(data):
            size_bytes = data[pos:pos+2]
            size = int.from_bytes(size_bytes, 'big')
            
            # Valid chunk sizes for RSA-2048: 240-256 bytes
            if 240 <= size <= 256:
                if pos + 2 + size <= len(data):
                    chunk = data[pos+2:pos+2+size]
                    print(f"[DEBUG-RSA-RECOVERY] Found valid chunk {chunk_count+1} at pos {pos}: size={size}")
                    recovered_chunks.append(chunk)
                    pos += 2 + size
                    chunk_count += 1
                    continue
            
            # Try next byte
            pos += 1
        
        if recovered_chunks:
            print(f"[DEBUG-RSA-RECOVERY] Recovered {len(recovered_chunks)} chunks from corrupted data")
            return recovered_chunks
        else:
            print(f"[DEBUG-RSA-RECOVERY] Could not recover any valid chunks")
            return None
    
    def _decrypt_rsa_chunks(self, encrypted_data):
        """
        Decrypt RSA chunked data
        
        :param encrypted_data: Encrypted chunked data
        :return: Decrypted data
        """
        if not encrypted_data.startswith(b'RSA_CHUNKED_V1:'):
            raise ValueError("Invalid RSA chunked data format")
        
        # Remove header
        data = encrypted_data[15:]  # len('RSA_CHUNKED_V1:') = 15
        decrypted_chunks = []
        pos = 0
        chunk_count = 0
        max_chunk_size = 256  # RSA-2048 encrypted chunk size
        
        print(f"[DEBUG-RSA-CHUNKS] Starting RSA chunk decryption, data size: {len(data)}")
        
        while pos < len(data):
            if pos + 2 > len(data):
                print(f"[DEBUG-RSA-CHUNKS] Reached end (not enough bytes for size header)")
                break
                
            # Read chunk size
            chunk_size = int.from_bytes(data[pos:pos+2], 'big')
            pos += 2
            
            # Validate chunk size
            if chunk_size == 0 or chunk_size > max_chunk_size:
                print(f"[DEBUG-RSA-CHUNKS] Chunk {chunk_count} has invalid size: {chunk_size}")
                print(f"[DEBUG-RSA-CHUNKS] Expected size ≤ {max_chunk_size}, got {chunk_size}")
                print(f"[DEBUG-RSA-CHUNKS] Position: {pos-2}, remaining data: {len(data) - pos + 2} bytes")
                
                # Try to recover by looking for next valid chunk or stopping
                if chunk_size > 512:
                    # Likely corruption, try to find next chunk marker or give up
                    print(f"[!] Chunk size ({chunk_size}) indicates data corruption")
                    print(f"[*] Attempting corrupted data recovery...")
                    recovered = self._attempt_rsa_chunk_recovery(encrypted_data)
                    if recovered:
                        print(f"[*] Trying to decrypt recovered chunks...")
                        decrypted_chunks = []
                        for i, chunk in enumerate(recovered):
                            decrypted_chunk = self.rsa_handler.decrypt(chunk)
                            if decrypted_chunk is None:
                                print(f"[!] Recovered chunk {i+1} decryption failed")
                                raise ValueError(f"Failed to decrypt recovered RSA chunk {i+1}")
                            decrypted_chunks.append(decrypted_chunk)
                        print(f"[+] Successfully recovered and decrypted {len(decrypted_chunks)} chunks")
                        return b''.join(decrypted_chunks)
                    else:
                        raise ValueError(f"RSA chunk size {chunk_size} exceeds maximum {max_chunk_size} - data may be corrupted and recovery failed")
                
            if pos + chunk_size > len(data):
                print(f"[DEBUG-RSA-CHUNKS] Chunk {chunk_count} extends beyond data boundaries")
                print(f"[DEBUG-RSA-CHUNKS] Position: {pos}, chunk_size: {chunk_size}, remaining: {len(data) - pos}")
                break
                
            # Extract and decrypt chunk
            encrypted_chunk = data[pos:pos+chunk_size]
            print(f"[DEBUG-RSA-CHUNKS] Decrypting chunk {chunk_count+1}: {len(encrypted_chunk)} bytes")
            
            try:
                decrypted_chunk = self.rsa_handler.decrypt(encrypted_chunk)
            except ValueError as e:
                print(f"[!] CRITICAL: Chunk {chunk_count+1} decryption FAILED")
                print(f"[!] Error: {str(e)}")
                print(f"\n[DEBUG-RSA-CHUNKS] Encrypted chunk data (hex dump):")
                chunk_hex = encrypted_chunk.hex()
                # Print in 32-byte chunks for readability
                for i in range(0, min(len(chunk_hex), 256), 64):
                    print(f"    {chunk_hex[i:i+64]}")
                if len(chunk_hex) > 256:
                    print(f"    ... (total {len(encrypted_chunk)} bytes)")
                
                print(f"\n[DEBUG-RSA-CHUNKS] RSA key diagnostics:")
                print(f"    - Public key loaded: {self.rsa_handler.public_key is not None}")
                print(f"    - Private key loaded: {self.rsa_handler.private_key is not None}")
                print(f"    - Encrypted chunk size: {len(encrypted_chunk)} bytes")
                print(f"    - Chunk position in stream: {chunk_count+1}")
                
                print(f"\n[ROOT CAUSE ANALYSIS]:")
                print(f"  1. RSA_KEY_MISMATCH: File was encrypted with different account's RSA key")
                print(f"     → Account keys may have been regenerated (password reset, account migration)")
                print(f"     → File may have been created by different user")
                print(f"  2. FILE_CORRUPTION: Data corrupted during extraction from steganography")
                print(f"     → Stego media may be damaged")
                print(f"     → Extraction algorithm may have failed")
                print(f"  3. WRONG_PASSWORD: AES layer succeeded but RSA data scrambled")
                print(f"     → Password may have unwrapped wrong AES key")
                raise ValueError(f"Failed to decrypt RSA chunk {chunk_count+1} - {str(e)}")
                
            decrypted_chunks.append(decrypted_chunk)
            pos += chunk_size
            chunk_count += 1
        
        print(f"[DEBUG-RSA-CHUNKS] Successfully decrypted {chunk_count} chunks, total output: {sum(len(c) for c in decrypted_chunks)} bytes")
        return b''.join(decrypted_chunks)
