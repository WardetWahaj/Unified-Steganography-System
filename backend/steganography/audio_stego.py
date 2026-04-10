"""
Audio Steganography Module
Hides data in WAV audio using LSB encoding with integrity verification.
Output is always WAV (lossless) to preserve hidden data perfectly.
"""
import wave
import struct
import os
import hashlib
import shutil


class AudioSteganography:
    """LSB steganography for audio files — inaudible data hiding"""
    
    def __init__(self):
        self.supported_formats = ['wav', 'mp3', 'flac', 'aiff']
        self.temp_dir = 'temp_audio'
        self.MAGIC = b'ASTG'  # 4-byte magic
    
    def _convert_to_wav(self, input_file):
        """Convert non-WAV audio to WAV for processing"""
        import subprocess
        
        ext = os.path.splitext(input_file)[1].lower()[1:]
        if ext == 'wav':
            return input_file
        
        os.makedirs(self.temp_dir, exist_ok=True)
        temp_wav = os.path.join(self.temp_dir, 'converted.wav')
        
        # Try FFmpeg
        try:
            result = subprocess.run([
                'ffmpeg', '-i', input_file, '-ar', '44100', '-ac', '1',
                '-sample_fmt', 's16', temp_wav, '-y'
            ], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return temp_wav
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(input_file)
            audio = audio.set_channels(1).set_frame_rate(44100).set_sample_width(2)
            audio.export(temp_wav, format='wav')
            return temp_wav
        except Exception:
            pass
        
        raise ValueError(f"Cannot convert {ext.upper()} to WAV. Install FFmpeg or pydub.")
    
    def _cleanup_temp(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
    
    def encode(self, input_audio, output_audio, data):
        """
        Hide data in audio using LSB encoding (2 bits per sample byte).
        
        Layout: MAGIC(4B) + LENGTH(4B) + DATA + MD5(16B)
        Capacity: total_frame_bytes / 4 bits → total_frame_bytes / 32 bytes
        """
        wav_file = None
        try:
            wav_file = self._convert_to_wav(input_audio)
            
            audio = wave.open(wav_file, mode='rb')
            params = audio.getparams()
            frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
            audio.close()
            
            # Build payload: MAGIC + LENGTH + DATA + MD5
            checksum = hashlib.md5(data).digest()
            length_bytes = struct.pack('>I', len(data))
            payload = self.MAGIC + length_bytes + data + checksum
            
            # Convert to bits
            payload_bits = ''.join(format(b, '08b') for b in payload)
            
            # Check capacity: 2 bits per sample byte
            capacity_bits = len(frame_bytes) * 2
            if len(payload_bits) > capacity_bits:
                max_bytes = (capacity_bits // 8) - 24  # subtract header+checksum
                raise ValueError(
                    f"Data too large ({len(data)} bytes). "
                    f"This audio can hold up to {max_bytes} bytes."
                )
            
            print(f"[*] Encoding {len(data)} bytes into audio ({len(payload_bits)}/{capacity_bits} bits)")
            
            # Encode 2 bits per byte using bits 2 and 3
            j = 0
            for i in range(0, len(payload_bits), 2):
                a = int(payload_bits[i])
                b = int(payload_bits[i + 1]) if i + 1 < len(payload_bits) else 0
                
                frame_bytes[j] = frame_bytes[j] & 0xF3  # Clear bits 2,3
                frame_bytes[j] |= (a << 3) | (b << 2)   # Set bits 2,3
                j += 1
            
            # Write output
            # Ensure output is .wav
            out_path = os.path.splitext(output_audio)[0] + '.wav'
            with wave.open(out_path, 'wb') as out:
                out.setparams(params)
                out.writeframes(bytes(frame_bytes))
            
            print(f"[+] Encoded {len(data)} bytes into audio → {out_path}")
            return out_path
            
        except Exception as e:
            print(f"[!] Audio encoding error: {e}")
            raise
        finally:
            if wav_file and wav_file != input_audio:
                self._cleanup_temp()
    
    def decode(self, input_audio):
        """
        Extract hidden data from audio. Verifies magic marker and MD5.
        """
        wav_file = None
        try:
            wav_file = self._convert_to_wav(input_audio)
            
            audio = wave.open(wav_file, mode='rb')
            frame_bytes = bytearray(list(audio.readframes(audio.getnframes())))
            audio.close()
            
            # Extract bits (2 per sample byte)
            def extract_bits(start_byte, num_bits):
                bits = []
                j = start_byte
                while len(bits) < num_bits and j < len(frame_bytes):
                    val = (frame_bytes[j] >> 2) & 3  # bits 2,3
                    bits.append((val >> 1) & 1)  # bit 3
                    bits.append(val & 1)          # bit 2
                    j += 1
                return bits[:num_bits], j
            
            # Read header: MAGIC(4B) + LENGTH(4B) = 64 bits = 32 sample bytes
            header_bits, next_byte = extract_bits(0, 64)
            header_bytes = bytes(int(''.join(str(b) for b in header_bits[i:i+8]), 2) 
                                for i in range(0, 64, 8))
            
            magic = header_bytes[:4]
            if magic != self.MAGIC:
                raise ValueError("No hidden data found (magic marker mismatch)")
            
            data_length = struct.unpack('>I', header_bytes[4:8])[0]
            if data_length <= 0:
                raise ValueError("Invalid data length")
            
            # Read data + checksum
            total_bits = (data_length + 16) * 8  # data + MD5
            payload_bits, _ = extract_bits(next_byte, total_bits)
            
            payload_bytes = bytes(int(''.join(str(b) for b in payload_bits[i:i+8]), 2)
                                 for i in range(0, len(payload_bits) - 7, 8))
            
            extracted_data = payload_bytes[:data_length]
            stored_checksum = payload_bytes[data_length:data_length + 16]
            
            actual_checksum = hashlib.md5(extracted_data).digest()
            if stored_checksum != actual_checksum:
                raise ValueError("Data integrity check failed — audio may have been re-encoded")
            
            print(f"[+] Extracted {data_length} bytes, checksum OK")
            return extracted_data
            
        except Exception as e:
            print(f"[!] Audio decoding error: {e}")
            raise
        finally:
            if wav_file and wav_file != input_audio:
                self._cleanup_temp()
    
    def encode_message(self, input_audio, output_audio, message):
        data = message.encode('utf-8')
        return self.encode(input_audio, output_audio, data)
    
    def decode_message(self, input_audio):
        data = self.decode(input_audio)
        return data.decode('utf-8', errors='ignore')
