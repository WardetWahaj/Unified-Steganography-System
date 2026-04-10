"""
Image Steganography Module
Uses PNG+LSB for lossless, visually-identical steganography.
No resizing, no quality loss, no format conversion.
"""
import numpy as np
from PIL import Image
import os
import hashlib


class ImageSteganography:
    """Lossless image steganography using LSB encoding in PNG format"""
    
    def __init__(self):
        self.supported_formats = ['png', 'bmp', 'tiff', 'jpg', 'jpeg']
        self.MAGIC = b'STEG'        # 4-byte magic marker
        self.CHECKSUM_LEN = 16       # MD5 checksum bytes
    
    def encode(self, input_image, output_image, data):
        """
        Hide data in image using 1-bit LSB across RGB channels.
        Output is always lossless PNG to preserve every bit.
        
        Capacity: width * height * 3 bits  (≈ 1 MB per megapixel)
        Visual impact: imperceptible (only LSB of each channel changes)
        """
        img = Image.open(input_image).convert('RGB')
        pixels = np.array(img, dtype=np.uint8)
        
        # Build payload: MAGIC(4) + LENGTH(4) + DATA + MD5(16)
        checksum = hashlib.md5(data).digest()
        length_bytes = len(data).to_bytes(4, 'big')
        payload = self.MAGIC + length_bytes + data + checksum
        
        # Convert payload to bit array
        payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        
        # Check capacity
        capacity = pixels.size  # total channel values = W*H*3
        if len(payload_bits) > capacity:
            max_bytes = (capacity // 8) - len(self.MAGIC) - 4 - self.CHECKSUM_LEN
            raise ValueError(
                f"Data too large ({len(data)} bytes). "
                f"This {img.size[0]}x{img.size[1]} image can hold up to {max_bytes} bytes. "
                f"Use a larger image."
            )
        
        # Flatten, embed in LSB, reshape back
        flat = pixels.flatten()
        flat[:len(payload_bits)] = (flat[:len(payload_bits)] & 0xFE) | payload_bits
        pixels = flat.reshape(pixels.shape)
        
        # Always save as PNG (lossless)
        out_path = os.path.splitext(output_image)[0] + '.png'
        Image.fromarray(pixels, 'RGB').save(out_path, 'PNG', compress_level=1)
        
        print(f"[+] Encoded {len(data)} bytes into {img.size[0]}x{img.size[1]} image → {out_path}")
        return out_path
    
    def decode(self, input_image):
        """
        Extract hidden data from a PNG stego image.
        Verifies magic marker and MD5 checksum for integrity.
        """
        img = Image.open(input_image).convert('RGB')
        flat = np.array(img, dtype=np.uint8).flatten()
        
        # Extract all LSBs
        lsb_bits = flat & 1
        
        # Read magic (4 bytes = 32 bits)
        magic_bits = lsb_bits[:32]
        magic = np.packbits(magic_bits).tobytes()
        if magic != self.MAGIC:
            raise ValueError("No hidden data found (magic marker mismatch)")
        
        # Read length (4 bytes = 32 bits)
        length_bits = lsb_bits[32:64]
        data_length = int.from_bytes(np.packbits(length_bits).tobytes(), 'big')
        
        if data_length <= 0 or data_length > (len(flat) // 8):
            raise ValueError(f"Invalid data length: {data_length}")
        
        # Read data + checksum
        total_bits = (data_length + self.CHECKSUM_LEN) * 8
        start = 64
        end = start + total_bits
        if end > len(lsb_bits):
            raise ValueError("Image too small to contain the indicated data")
        
        payload_bits = lsb_bits[start:end]
        payload_bytes = np.packbits(payload_bits).tobytes()
        
        extracted_data = payload_bytes[:data_length]
        stored_checksum = payload_bytes[data_length:data_length + self.CHECKSUM_LEN]
        
        # Verify integrity
        actual_checksum = hashlib.md5(extracted_data).digest()
        if stored_checksum != actual_checksum:
            raise ValueError("Data integrity check failed — file may be corrupted or re-compressed")
        
        print(f"[+] Extracted {data_length} bytes, checksum OK")
        return extracted_data
    
    def encode_message(self, input_image, output_image, message):
        data = message.encode('utf-8')
        return self.encode(input_image, output_image, data)
    
    def decode_message(self, input_image):
        data = self.decode(input_image)
        return data.decode('utf-8', errors='ignore')
