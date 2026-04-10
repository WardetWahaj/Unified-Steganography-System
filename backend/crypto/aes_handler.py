"""
AES Encryption Module
Handles AES encryption/decryption with password-based key derivation and HMAC verification
"""
try:
    from Crypto.Cipher import AES
    from Crypto import Random
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Hash import SHA256, HMAC
except Exception:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome import Random
        from Cryptodome.Protocol.KDF import PBKDF2
        from Cryptodome.Hash import SHA256, HMAC
    except Exception:
        raise ImportError("Neither 'Crypto' nor 'Cryptodome' could be imported; please install pycryptodome")

import hashlib
import os


class AESHandler:
    """Handles AES encryption and decryption operations with HMAC verification"""
    
    # Magic header to verify correct decryption
    MAGIC_HEADER = b'STEGO_AES_V1'
    
    @staticmethod
    def pad(data):
        """Pad data to AES block size using PKCS7"""
        pad_len = AES.block_size - (len(data) % AES.block_size)
        return data + bytes([pad_len] * pad_len)
    
    @staticmethod
    def unpad(data):
        """Remove PKCS7 padding from data"""
        if len(data) == 0:
            raise ValueError("Cannot unpad empty data")
        pad_len = data[-1]
        if pad_len > AES.block_size or pad_len == 0:
            raise ValueError("Invalid padding")
        # Verify padding is correct
        if data[-pad_len:] != bytes([pad_len] * pad_len):
            raise ValueError("Invalid padding")
        return data[:-pad_len]
    
    @staticmethod
    def derive_key(password, salt):
        """
        Derive AES key from password using PBKDF2
        
        :param password: Password string
        :param salt: Salt for key derivation
        :return: 32-byte key for AES-256
        """
        return PBKDF2(password.encode('utf-8'), salt, dkLen=32, count=100000)
    
    def encrypt(self, data, password):
        """
        Encrypt data using AES-256 in CBC mode with HMAC verification
        
        :param data: Data to encrypt (bytes)
        :param password: Password for encryption
        :return: Encrypted data (salt + IV + HMAC + ciphertext)
        """
        try:
            # Generate random salt and IV
            salt = os.urandom(16)
            iv = Random.new().read(AES.block_size)
            
            # Derive key from password and salt
            key = self.derive_key(password, salt)
            
            # Add magic header to data to verify correct decryption
            data_with_header = self.MAGIC_HEADER + data
            
            # Encrypt the data
            cipher = AES.new(key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(self.pad(data_with_header))
            
            # Compute HMAC of IV + ciphertext
            hmac_obj = HMAC.new(key, digestmod=SHA256)
            hmac_obj.update(iv + ciphertext)
            hmac_digest = hmac_obj.digest()
            
            # Return: salt(16) + IV(16) + HMAC(32) + ciphertext
            encrypted_data = salt + iv + hmac_digest + ciphertext
            
            print(f"[+] AES encryption successful ({len(encrypted_data)} bytes)")
            return encrypted_data
        except Exception as e:
            print(f"[!] AES encryption failed: {e}")
            return None
    
    def decrypt(self, encrypted_data, password):
        """
        Decrypt data using AES-256 in CBC mode with HMAC verification
        
        :param encrypted_data: Encrypted data (salt + IV + HMAC + ciphertext)
        :param password: Password for decryption
        :return: Decrypted data
        :raises: ValueError if password is incorrect or data is corrupted
        """
        try:
            # Minimum size: salt(16) + IV(16) + HMAC(32) + at least one block(16) = 80 bytes
            if len(encrypted_data) < 80:
                raise ValueError(f"Encrypted data too short ({len(encrypted_data)} bytes)")
            
            # Extract components: salt(16) + IV(16) + HMAC(32) + ciphertext
            salt = encrypted_data[:16]
            iv = encrypted_data[16:32]
            hmac_digest = encrypted_data[32:64]
            ciphertext = encrypted_data[64:]
            
            # Derive key from password and salt
            key = self.derive_key(password, salt)
            
            # Verify HMAC
            hmac_obj = HMAC.new(key, digestmod=SHA256)
            hmac_obj.update(iv + ciphertext)
            try:
                hmac_obj.verify(hmac_digest)
            except ValueError:
                raise ValueError("Incorrect password - HMAC verification failed")
            
            # Decrypt the data
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(ciphertext)
            
            # Unpad the data (this will raise ValueError if padding is invalid)
            decrypted_data = self.unpad(decrypted_data)
            
            # Verify magic header
            if not decrypted_data.startswith(self.MAGIC_HEADER):
                raise ValueError("Incorrect password - magic header verification failed")
            
            # Remove magic header
            decrypted_data = decrypted_data[len(self.MAGIC_HEADER):]
            
            print(f"[+] AES decryption successful ({len(decrypted_data)} bytes)")
            return decrypted_data
        except ValueError as e:
            print(f"[!] AES decryption failed: {e}")
            raise
        except Exception as e:
            print(f"[!] AES decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")
