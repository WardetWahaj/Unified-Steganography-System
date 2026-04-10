"""
RSA Key Generation and Encryption/Decryption Module
Handles RSA key pair generation and file encryption/decryption
"""
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto import Random
except Exception:
    try:
        from Cryptodome.PublicKey import RSA
        from Cryptodome.Cipher import PKCS1_OAEP
        from Cryptodome import Random
    except Exception:
        raise ImportError("Neither 'Crypto' nor 'Cryptodome' could be imported; please install pycryptodome")

import os


class RSAHandler:
    """Handles RSA encryption and decryption operations"""
    
    def __init__(self, key_dir='keys'):
        """
        Initialize RSA Handler
        
        :param key_dir: Directory to store RSA keys
        """
        self.key_dir = key_dir
        os.makedirs(key_dir, exist_ok=True)
        self.public_key_path = os.path.join(key_dir, 'public.pem')
        self.private_key_path = os.path.join(key_dir, 'private.pem')
        self.public_key = None
        self.private_key = None
    
    def generate_keys(self, key_size=2048):
        """
        Generate RSA key pair
        
        :param key_size: Size of the RSA key (default: 2048 bits)
        """
        print(f"[*] Generating {key_size}-bit RSA key pair...")
        keypair = RSA.generate(key_size)
        
        # Extract public and private keys
        public_key = keypair.publickey()
        public_key_pem = public_key.exportKey('PEM')
        private_key_pem = keypair.exportKey('PEM')
        
        # Save keys to files
        with open(self.public_key_path, 'wb') as f:
            f.write(public_key_pem)
        
        with open(self.private_key_path, 'wb') as f:
            f.write(private_key_pem)
        
        print(f"[+] Public key saved to: {self.public_key_path}")
        print(f"[+] Private key saved to: {self.private_key_path}")
        print("[!] Keep your private key secure!")
        
        return self.public_key_path, self.private_key_path
    
    def load_public_key(self, key_path=None):
        """
        Load public key from file
        
        :param key_path: Path to public key file (optional)
        """
        if key_path is None:
            key_path = self.public_key_path
        
        try:
            with open(key_path, 'rb') as f:
                self.public_key = RSA.importKey(f.read())
            # Update path if custom path is provided
            if key_path != self.public_key_path:
                self.public_key_path = key_path
            print(f"[+] Public key loaded from: {key_path}")
            return True
        except FileNotFoundError:
            print(f"[!] Public key not found at: {key_path}")
            return False
        except Exception as e:
            print(f"[!] Error loading public key: {e}")
            return False
    
    def load_private_key(self, key_path=None):
        """
        Load private key from file
        
        :param key_path: Path to private key file (optional)
        """
        if key_path is None:
            key_path = self.private_key_path
        
        try:
            with open(key_path, 'rb') as f:
                self.private_key = RSA.importKey(f.read())
            # Update path if custom path is provided
            if key_path != self.private_key_path:
                self.private_key_path = key_path
            print(f"[+] Private key loaded from: {key_path}")
            return True
        except FileNotFoundError:
            print(f"[!] Private key not found at: {key_path}")
            return False
        except Exception as e:
            print(f"[!] Error loading private key: {e}")
            return False
    
    def encrypt(self, data):
        """
        Encrypt data using RSA public key
        
        :param data: Data to encrypt (bytes)
        :return: Encrypted data
        """
        if self.public_key is None:
            if not self.load_public_key():
                raise ValueError("Public key not loaded")
        
        try:
            cipher = PKCS1_OAEP.new(self.public_key)
            
            # RSA can only encrypt data smaller than key size
            # For 2048-bit key, max is ~245 bytes
            max_chunk_size = 245
            
            if len(data) <= max_chunk_size:
                encrypted_data = cipher.encrypt(data)
                print(f"[+] RSA encryption successful ({len(data)} bytes)")
                return encrypted_data
            else:
                print(f"[!] Data too large for RSA ({len(data)} bytes > {max_chunk_size} bytes)")
                print("[!] Consider using hybrid encryption (RSA + AES)")
                return None
        except Exception as e:
            print(f"[!] RSA encryption failed: {e}")
            return None
    
    def encrypt_with_public_key(self, data, public_key_pem):
        """
        Encrypt data with a provided public key (as PEM string)
        Useful for multi-recipient encryption
        
        :param data: Data to encrypt (bytes)
        :param public_key_pem: Public key in PEM format (string or bytes)
        :return: Encrypted data
        """
        try:
            # Convert string to bytes if needed
            if isinstance(public_key_pem, str):
                public_key_pem = public_key_pem.encode('utf-8')
            
            public_key = RSA.importKey(public_key_pem)
            cipher = PKCS1_OAEP.new(public_key)
            
            max_chunk_size = 245
            if len(data) <= max_chunk_size:
                encrypted_data = cipher.encrypt(data)
                print(f"[+] RSA encryption with public key successful ({len(data)} bytes)")
                return encrypted_data
            else:
                print(f"[!] Data too large for RSA ({len(data)} bytes > {max_chunk_size} bytes)")
                return None
        except Exception as e:
            print(f"[!] RSA encryption with public key failed: {e}")
            return None
    
    def decrypt(self, encrypted_data):
        """
        Decrypt data using RSA private key
        
        :param encrypted_data: Encrypted data (bytes)
        :return: Decrypted data
        """
        if self.private_key is None:
            if not self.load_private_key():
                raise ValueError("Private key not loaded")
        
        try:
            # Debug: check if data looks like valid RSA encrypted data
            print(f"[DEBUG-RSA] Attempting to decrypt {len(encrypted_data)} bytes")
            print(f"[DEBUG-RSA] Data (first 32 bytes hex): {encrypted_data[:32].hex()}")
            print(f"[DEBUG-RSA] Private key size: {self.private_key.size_in_bits()} bits ({self.private_key.size_in_bytes()} bytes)")
            
            cipher = PKCS1_OAEP.new(self.private_key)
            decrypted_data = cipher.decrypt(encrypted_data)
            print(f"[+] RSA decryption successful ({len(decrypted_data)} bytes)")
            return decrypted_data
        except ValueError as e:
            error_msg = str(e).lower()
            if 'incorrect' in error_msg or 'unable to decrypt' in error_msg or 'decryption failed' in error_msg.lower():
                print(f"[!] RSA decryption failed: {e}")
                print(f"[DEBUG-RSA] This likely means one of:")
                print(f"[DEBUG-RSA]   1. Data wasn't encrypted with this key")
                print(f"[DEBUG-RSA]   2. Data is corrupted")
                print(f"[DEBUG-RSA]   3. Wrong RSA key being used")
                print(f"[!] Possible causes:")
                print(f"    - Data was encrypted with a different RSA key")
                print(f"    - Data is corrupted")
                print(f"    - Wrong decryption key used")
                print(f"[!] The data may not be RSA-encrypted or wrong key used")
                # Raise instead of returning None to provide better error context
                raise ValueError(f"RSA decryption failed - incorrect decryption: {e}")
            else:
                print(f"[!] RSA decryption error: {e}")
                raise ValueError(f"RSA decryption error: {e}")
        except Exception as e:
            print(f"[!] RSA decryption error: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"RSA decryption error: {e}")
    
    def keys_exist(self):
        """Check if RSA key pair exists - checks both file existence and memory"""
        # First check if keys are loaded in memory
        if self.public_key is not None and self.private_key is not None:
            return True
        # Then check if files exist at the specified paths
        return os.path.exists(self.public_key_path) and os.path.exists(self.private_key_path)
    
    def verify_key_pair(self, test_data=None):
        """
        Verify that the loaded public and private keys form a valid pair
        Tests by encrypting with public key and decrypting with private key
        
        :param test_data: Data to test with (default: test message)
        :return: True if keys are paired correctly, False otherwise
        """
        if self.public_key is None or self.private_key is None:
            print("[!] Cannot verify: keys not loaded")
            return False
        
        try:
            if test_data is None:
                test_data = b"RSA_KEY_VERIFICATION_TEST"
            
            # Try to encrypt with public key
            cipher_enc = PKCS1_OAEP.new(self.public_key)
            encrypted = cipher_enc.encrypt(test_data)
            
            # Try to decrypt with private key
            cipher_dec = PKCS1_OAEP.new(self.private_key)
            decrypted = cipher_dec.decrypt(encrypted)
            
            # Check if decryption matched original
            is_valid = decrypted == test_data
            
            if is_valid:
                print(f"[+] RSA key pair verified successfully")
            else:
                print(f"[!] RSA key pair verification FAILED - keys don't match")
                print(f"[!] Original: {test_data[:20]}...")
                print(f"[!] Decrypted: {decrypted[:20]}...")
            
            return is_valid
            
        except Exception as e:
            print(f"[!] RSA key pair verification error: {e}")
            return False
