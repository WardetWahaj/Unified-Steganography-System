"""
Video Steganography Module
Uses LSB (bit-level) encoding in video frames for imperceptible data hiding.
Preserves original FPS, resolution, and visual quality.
"""
import cv2
import numpy as np
import os
import shutil
import subprocess
import hashlib
import struct


class VideoSteganography:
    """LSB steganography for video files — visually identical output"""
    
    def __init__(self, temp_dir='temp'):
        self.temp_dir = temp_dir
        self.supported_formats = ['mp4', 'avi', 'mov']
        self.MAGIC = b'VSTG'  # 4-byte magic marker

    # ─── Frame extraction ────────────────────────────────
    
    def _get_video_info(self, video_path):
        """Get FPS, frame count, and dimensions from source video"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return fps, total, w, h
    
    def _extract_frames(self, video_path):
        """Extract all frames as lossless PNG"""
        os.makedirs(self.temp_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            # Fallback to FFmpeg
            return self._extract_frames_ffmpeg(video_path)
        
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imwrite(
                os.path.join(self.temp_dir, f"{count + 1}.png"),
                frame, [cv2.IMWRITE_PNG_COMPRESSION, 0]
            )
            count += 1
        cap.release()
        
        if count == 0:
            return self._extract_frames_ffmpeg(video_path)
        
        print(f"[+] Extracted {count} frames")
        return count
    
    def _extract_frames_ffmpeg(self, video_path):
        """Fallback: extract frames via FFmpeg"""
        try:
            subprocess.run([
                "ffmpeg", "-i", str(video_path),
                os.path.join(self.temp_dir, "%d.png")
            ], capture_output=True, text=True, timeout=300, check=True)
            count = len([f for f in os.listdir(self.temp_dir) if f.endswith('.png')])
            print(f"[+] Extracted {count} frames (FFmpeg)")
            return count
        except Exception as e:
            raise RuntimeError(f"Failed to extract frames: {e}")
    
    def _extract_audio(self, video_path, audio_path):
        """Extract audio track"""
        try:
            subprocess.run([
                "ffmpeg", "-i", str(video_path), "-vn", "-acodec", "copy",
                audio_path, "-y"
            ], capture_output=True, timeout=60, check=True)
            return True
        except Exception:
            return False

    # ─── LSB frame encode/decode ─────────────────────────
    
    def _encode_frame_lsb(self, frame_path, bits):
        """
        Embed `bits` (list/array of 0/1) into the LSB of frame pixels (RGB channels).
        Returns number of bits actually embedded.
        """
        frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        flat = frame.flatten()
        n = min(len(bits), len(flat))
        flat[:n] = (flat[:n] & 0xFE) | bits[:n]
        frame = flat.reshape(frame.shape)
        cv2.imwrite(frame_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        return n
    
    def _decode_frame_lsb(self, frame_path, num_bits):
        """Extract `num_bits` LSBs from frame pixels."""
        frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        flat = frame.flatten()
        return (flat[:num_bits] & 1).astype(np.uint8)

    # ─── Merge frames back ───────────────────────────────
    
    def _merge_video(self, output_video, fps, audio_path=None):
        """
        Merge PNG frames into a video using FFmpeg with FFV1 lossless codec.
        FFV1 preserves pixel-perfect data, allowing LSB steganography to work perfectly.
        """
        print(f"\n[MERGE] Starting video merge:")
        print(f"  output_video: {output_video}")
        print(f"  fps: {fps}")
        print(f"  audio_path: {audio_path}")
        
        # Verify FFmpeg is available
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, timeout=5, check=True
            )
            print("[+] FFmpeg is available - using FFV1 lossless codec")
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            raise RuntimeError(
                "FFmpeg is not installed or not in system PATH. "
                "Please install FFmpeg from https://ffmpeg.org/download.html"
            )
        
        frame_pattern = os.path.join(self.temp_dir, "%d.png")
        temp_lossless = os.path.join(self.temp_dir, "lossless.mkv")
        print(f"  frame_pattern: {frame_pattern}")
        
        # Step 1: Create lossless MKV with FFV1 codec
        # FFV1 provides pixel-perfect preservation for steganography
        try:
            cmd = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", frame_pattern,
                "-c:v", "ffv1",          # FFV1 lossless codec
                "-level", "3",            # Highest compression level
                "-g", "1",                # Keyframe interval for best compression
                temp_lossless
            ]
            result = subprocess.run(
                cmd, capture_output=True, timeout=600, check=True, text=True
            )
            print("[+] FFV1 lossless encoding complete")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg FFV1 encoding failed: {error_msg[:300]}")
        except Exception as e:
            raise RuntimeError(f"Failed to merge frames: {str(e)}")
        
        # Step 2: Remux to output format if needed (keeping lossless codec)
        ext = os.path.splitext(output_video)[1].lower()
        
        try:
            if ext == '.mkv':
                # Already in MKV format, just copy
                shutil.copy(temp_lossless, output_video)
                print(f"[+] Output video (FFV1 lossless MKV): {output_video}")
                return output_video
            elif ext == '.mp4':
                # IMPORTANT: MP4 containers do NOT support FFV1 codec
                # Remuxing would require re-encoding, which destroys LSBs
                # Force output to MKV instead (preserves lossless stream)
                output_mkv = output_video.replace('.mp4', '.mkv')
                shutil.copy(temp_lossless, output_mkv)
                print(f"[!] MP4 cannot preserve FFV1 lossless codec")
                print(f"[*] Using MKV format instead to preserve steganographic data")
                print(f"[+] Output video (FFV1 lossless MKV): {output_mkv}")
                return output_mkv
            elif ext in ['.mov', '.avi']:
                # Try remux for other formats, but with caution
                cmd = [
                    "ffmpeg", "-y", "-i", temp_lossless,
                    "-c:v", "copy",  # Copy video codec without re-encoding
                ]
                
                # Add audio if present
                if audio_path and os.path.exists(audio_path):
                    cmd += ["-i", audio_path, "-c:a", "aac", "-b:a", "192k"]
                else:
                    cmd += ["-c:a", "copy"]
                
                cmd.append(output_video)
                
                result = subprocess.run(
                    cmd, capture_output=True, timeout=600, check=True, text=True
                )
                print(f"[+] Output video (remuxed to {ext}): {output_video}")
                return output_video
            else:
                # Unknown format, use MKV
                output_mkv = output_video.replace(ext, '.mkv')
                shutil.copy(temp_lossless, output_mkv)
                print(f"[+] Output video (converted to MKV): {output_mkv}")
                return output_mkv
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            # Fallback: use MKV if remuxing fails
            print(f"[!] Remux failed, using lossless MKV instead")
            output_mkv = output_video.replace(os.path.splitext(output_video)[1], '.mkv')
            shutil.copy(temp_lossless, output_mkv)
            return output_mkv
        except Exception as e:
            raise RuntimeError(f"Failed to remux video: {str(e)}")

    # ─── Merge video (fallback with OpenCV) ─────────────
    
    def _merge_video_opencv(self, output_video, fps, width, height, audio_path=None):
        """
        Fallback: Merge PNG frames into video using OpenCV VideoWriter.
        Note: May not preserve perfect quality but works without FFmpeg.
        """
        print("[*] Using OpenCV fallback for video encoding (FFmpeg not available)...")
        
        # Determine codec based on output format
        ext = os.path.splitext(output_video)[1].lower()
        if ext == '.mp4':
            # Use uncompressed format to preserve LSB data
            # Note: This creates larger files but maintains data integrity
            fourcc = 0  # UNCOMPRESSED
            output_video = output_video.replace('.mp4', '.avi')  # Convert to AVI for uncompressed support
        elif ext == '.avi':
            fourcc = 0  # UNCOMPRESSED
        else:
            fourcc = 0  # UNCOMPRESSED
        
        # Create video writer
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
        if not out.isOpened():
            raise RuntimeError(f"Failed to create video writer for {output_video}")
        
        # Write frames
        frame_count = 0
        for i in range(1, 10000):  # Max 10000 frames
            frame_path = os.path.join(self.temp_dir, f"{i}.png")
            if not os.path.exists(frame_path):
                break
            
            frame = cv2.imread(frame_path)
            if frame is None:
                break
            
            out.write(frame)
            frame_count += 1
        
        out.release()
        
        if frame_count == 0:
            raise RuntimeError("No frames found to write video")
        
        print(f"[+] Wrote {frame_count} frames to {output_video} (OpenCV fallback - uncompressed)")
        
        # Note: Audio not supported in OpenCV fallback
        if audio_path and os.path.exists(audio_path):
            print("[!] Warning: Audio not supported in OpenCV fallback, video will be silent")
        
        # Return the actual output path (may be different if we changed the extension)
        return output_video

    # ─── Cleanup ─────────────────────────────────────────
    
    def _cleanup(self):
        import time, gc
        time.sleep(0.1)
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            try:
                time.sleep(0.5)
                shutil.rmtree(self.temp_dir)
            except Exception:
                print("[!] Could not clean temp directory")

    # ─── Public API ──────────────────────────────────────
    
    def encode(self, input_video, output_video, data):
        """
        Hide data in video using LSB encoding across frame pixels.
        
        Layout (stored in frame LSBs across all frames):
          MAGIC(4B) + DATA_LEN(4B) + DATA + MD5(16B)
        
        Each frame holds W*H*3 bits of capacity.
        """
        try:
            print(f"\n[ENCODE] Starting video steganography")
            print(f"  input_video: {input_video}")
            print(f"  output_video: {output_video}")
            print(f"  data_size: {len(data)} bytes")
            
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
            fps, total_frames, w, h = self._get_video_info(input_video)
            print(f"[*] Video: {w}x{h}, {fps} FPS, {total_frames} frames")
            
            bits_per_frame = w * h * 3
            
            # Build payload: MAGIC + LENGTH + DATA + MD5
            checksum = hashlib.md5(data).digest()
            length_bytes = struct.pack('>I', len(data))
            payload = self.MAGIC + length_bytes + data + checksum
            payload_bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
            
            frames_needed = (len(payload_bits) + bits_per_frame - 1) // bits_per_frame
            if frames_needed > total_frames:
                max_bytes = (total_frames * bits_per_frame // 8) - 24  # subtract header+checksum
                raise ValueError(
                    f"Data too large ({len(data)} bytes). "
                    f"This video can hold up to {max_bytes} bytes."
                )
            
            print(f"[*] Payload: {len(payload)} bytes → {len(payload_bits)} bits across {frames_needed}/{total_frames} frames")
            
            # Extract frames
            print(f"[*] Extracting frames...")
            self._extract_frames(input_video)
            
            # Extract audio
            print(f"[*] Extracting audio...")
            audio_path = os.path.join(self.temp_dir, "audio.aac")
            has_audio = self._extract_audio(input_video, audio_path)
            print(f"[*] Audio extracted: {has_audio}")
            
            # Embed payload bits across frames
            print(f"[*] Embedding data into frames...")
            bit_offset = 0
            for i in range(total_frames):
                frame_path = os.path.join(self.temp_dir, f"{i + 1}.png")
                if not os.path.exists(frame_path):
                    continue
                
                if bit_offset < len(payload_bits):
                    chunk = payload_bits[bit_offset:bit_offset + bits_per_frame]
                    written = self._encode_frame_lsb(frame_path, chunk)
                    bit_offset += written
            
            print(f"[*] Data embedded in {bit_offset // (w * h * 3)} frames")
            
            # Merge back - try FFmpeg first, fallback to OpenCV
            print(f"[*] Merging frames back to video...")
            actual_output = output_video
            try:
                actual_output = self._merge_video(
                    output_video, fps,
                    audio_path if has_audio else None
                )
                print(f"[+] Merge with FFmpeg successful")
            except RuntimeError as e:
                if "FFmpeg is not installed" in str(e):
                    print("[!] FFmpeg not available, using OpenCV fallback...")
                    print("[!] Note: Audio will not be included in OpenCV fallback")
                    # OpenCV fallback returns the actual output path (may be changed to .avi)
                    actual_output = self._merge_video_opencv(output_video, fps, w, h, None)
                    print(f"[+] Merge with OpenCV successful")
                else:
                    raise
            
            self._cleanup()
            print(f"[+] Encoded {len(data)} bytes into video")
            print(f"[+] Final output: {actual_output}")
            
            # Verify file exists
            if not os.path.exists(actual_output):
                raise RuntimeError(f"Output file not created: {actual_output}")
            
            output_size = os.path.getsize(actual_output)
            print(f"[+] Output file size: {output_size} bytes")
            return actual_output
            
        except Exception as e:
            self._cleanup()
            raise
    
    def decode(self, input_video):
        """
        Extract hidden data from a stego video.
        Reads LSBs from frames, verifies magic marker and MD5 checksum.
        """
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
            fps, total_frames, w, h = self._get_video_info(input_video)
            bits_per_frame = w * h * 3
            
            # Extract frames
            self._extract_frames(input_video)
            
            # Read header from first frame: MAGIC(4B) + LENGTH(4B) = 64 bits
            first_frame = os.path.join(self.temp_dir, "1.png")
            if not os.path.exists(first_frame):
                raise FileNotFoundError("No frames extracted")
            
            header_bits = self._decode_frame_lsb(first_frame, 64)
            header_bytes = np.packbits(header_bits).tobytes()
            
            magic = header_bytes[:4]
            if magic != self.MAGIC:
                raise ValueError("No hidden data found (magic marker mismatch)")
            
            data_length = struct.unpack('>I', header_bytes[4:8])[0]
            if data_length <= 0:
                raise ValueError("Invalid data length")
            
            total_payload_bits = (8 + data_length + 16) * 8  # header + data + md5
            frames_needed = (total_payload_bits + bits_per_frame - 1) // bits_per_frame
            
            print(f"[*] Extracting {data_length} bytes from {frames_needed} frames...")
            
            # Read all payload bits
            all_bits = np.zeros(0, dtype=np.uint8)
            for i in range(min(frames_needed, total_frames)):
                frame_path = os.path.join(self.temp_dir, f"{i + 1}.png")
                if not os.path.exists(frame_path):
                    continue
                needed = total_payload_bits - len(all_bits)
                if needed <= 0:
                    break
                frame_bits = self._decode_frame_lsb(frame_path, min(needed, bits_per_frame))
                all_bits = np.concatenate([all_bits, frame_bits])
            
            # Parse payload
            payload = np.packbits(all_bits).tobytes()
            # Skip MAGIC+LENGTH (8 bytes)
            extracted_data = payload[8:8 + data_length]
            stored_checksum = payload[8 + data_length:8 + data_length + 16]
            
            actual_checksum = hashlib.md5(extracted_data).digest()
            if stored_checksum != actual_checksum:
                raise ValueError("Data integrity check failed — video may have been re-encoded")
            
            self._cleanup()
            print(f"[+] Extracted {data_length} bytes, checksum OK")
            return extracted_data
            
        except Exception as e:
            self._cleanup()
            raise
    
    def encode_message(self, input_video, output_video, message):
        """
        Encode text message into video
        
        :param input_video: Path to input video file
        :param output_video: Path to output video file
        :param message: Text message to hide
        """
        data = message.encode('utf-8')
        return self.encode(input_video, output_video, data)
    
    def decode_message(self, input_video):
        """
        Decode text message from video
        
        :param input_video: Path to video file with hidden message
        :return: Extracted text message
        """
        data = self.decode(input_video)
        return data.decode('utf-8', errors='ignore')
