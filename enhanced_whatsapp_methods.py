
import cv2
import numpy as np
import hashlib

# Add these methods to your RobustImageSteganography class:

def encode_enhanced_whatsapp(self, input_image, output_image, data):
    """Enhanced method specifically for WhatsApp transmission"""
    try:
        print("[*] WhatsApp-optimized encoding...")
        
        img = cv2.imread(input_image)
        if img is None:
            raise ValueError(f"Cannot read image: {input_image}")
        
        h, w = img.shape[:2]
        if h < 800 or w < 800:
            img = cv2.resize(img, (max(800, w), max(800, h)), interpolation=cv2.INTER_LANCZOS4)
        
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y_channel = img_yuv[:, :, 0].astype(np.float32)
        
        checksum = hashlib.md5(data).digest()[:4]
        full_data = data + checksum
        
        binary_string = ''.join(format(byte, '08b') for byte in full_data)
        length_header = format(len(data), '032b')
        full_binary = length_header + binary_string
        
        redundant_binary = ''
        for bit in full_binary:
            redundant_binary += bit * 7
        
        print(f"[*] Embedding {len(data)} bytes with 7x redundancy ({len(redundant_binary)} bits)")
        
        bit_index = 0
        h, w = y_channel.shape
        
        for i in range(0, h-15, 16):
            for j in range(0, w-15, 16):
                if bit_index >= len(redundant_binary):
                    break
                
                for sub_i in range(0, 16, 8):
                    for sub_j in range(0, 16, 8):
                        if bit_index >= len(redundant_binary):
                            break
                        
                        block = y_channel[i+sub_i:i+sub_i+8, j+sub_j:j+sub_j+8]
                        dct_block = cv2.dct(block)
                        
                        bit = int(redundant_binary[bit_index])
                        
                        if bit == 1:
                            dct_block[3, 3] = abs(dct_block[3, 3]) + 50
                        else:
                            dct_block[3, 3] = -abs(dct_block[3, 3]) - 30
                        
                        y_channel[i+sub_i:i+sub_i+8, j+sub_j:j+sub_j+8] = cv2.idct(dct_block)
                        bit_index += 1
        
        img_yuv[:, :, 0] = np.clip(y_channel, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        
        cv2.imwrite(output_image, result, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        print(f"[+] WhatsApp-ready image created")
        return output_image
        
    except Exception as e:
        print(f"[!] WhatsApp encoding error: {e}")
        raise

def decode_enhanced_whatsapp(self, input_image):
    """Enhanced decoding for WhatsApp-transmitted images"""
    try:
        print("[*] WhatsApp-optimized decoding...")
        
        img = cv2.imread(input_image)
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y_channel = img_yuv[:, :, 0].astype(np.float32)
        
        h, w = y_channel.shape
        extracted_bits = []
        
        for i in range(0, h-15, 16):
            for j in range(0, w-15, 16):
                for sub_i in range(0, 16, 8):
                    for sub_j in range(0, 16, 8):
                        if i+sub_i+8 <= h and j+sub_j+8 <= w:
                            block = y_channel[i+sub_i:i+sub_i+8, j+sub_j:j+sub_j+8]
                            dct_block = cv2.dct(block)
                            
                            coeff = dct_block[3, 3]
                            extracted_bits.append('1' if coeff > 0 else '0')
        
        if len(extracted_bits) < 224:
            raise ValueError("Insufficient data extracted")
        
        print(f"[*] Extracted {len(extracted_bits)} bits from WhatsApp image")
        
        # Decode header with majority voting
        header_bits = ''
        for i in range(0, min(224, len(extracted_bits)), 7):
            group = extracted_bits[i:i+7]
            ones = group.count('1')
            header_bits += '1' if ones > 3 else '0'
            if len(header_bits) >= 32:
                break
        
        if len(header_bits) < 32:
            raise ValueError("Could not decode header")
        
        data_length = int(header_bits[:32], 2)
        
        if data_length <= 0 or data_length > 10000:
            raise ValueError(f"Invalid data length: {data_length}")
        
        print(f"[*] Decoded length: {data_length} bytes")
        
        data_start = 224
        total_data_bits_needed = (data_length + 4) * 8 * 7
        
        if len(extracted_bits) < data_start + total_data_bits_needed:
            print("[!] Using available bits (may be incomplete)")
            available_bits = extracted_bits[data_start:]
        else:
            available_bits = extracted_bits[data_start:data_start + total_data_bits_needed]
        
        data_binary = ''
        for i in range(0, len(available_bits), 7):
            group = available_bits[i:i+7]
            if len(group) >= 4:
                ones = group.count('1')
                data_binary += '1' if ones > 3 else '0'
        
        data_bytes = []
        for i in range(0, len(data_binary), 8):
            byte_str = data_binary[i:i+8]
            if len(byte_str) == 8:
                data_bytes.append(int(byte_str, 2))
        
        if len(data_bytes) >= data_length + 4:
            original_data = bytes(data_bytes[:data_length])
            stored_checksum = bytes(data_bytes[data_length:data_length+4])
            
            calculated_checksum = hashlib.md5(original_data).digest()[:4]
            
            if stored_checksum == calculated_checksum:
                print(f"[+] Successfully decoded {len(original_data)} bytes from WhatsApp image!")
                return original_data
            else:
                print(f"[!] Checksum mismatch but returning data")
                return original_data
        else:
            raise ValueError("Insufficient data decoded")
            
    except Exception as e:
        print(f"[!] WhatsApp decoding error: {e}")
        raise
