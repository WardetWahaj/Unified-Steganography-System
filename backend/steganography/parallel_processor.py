"""
Parallel Video Frame Processor - Multi-threaded frame encoding/decoding
Processes multiple video frames concurrently for maximum throughput
"""

import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional
import time


class ParallelVideoProcessor:
    """
    Multi-threaded video frame processor
    Encodes/decodes multiple frames simultaneously
    """
    
    def __init__(self, max_workers: int = 4, frame_cache_size: int = 100):
        """
        Initialize parallel video processor
        
        :param max_workers: Number of parallel threads (default 4 for i7)
        :param frame_cache_size: Number of frames to cache in memory
        """
        self.max_workers = max_workers
        self.frame_cache_size = frame_cache_size
        self.temp_dir = 'temp_parallel'
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_frames_parallel(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Extract video frames using OpenCV (serial, but optimized)
        
        :param video_path: Path to video file
        :param progress_callback: Function(frame_count, total_frames)
        :return: Number of frames extracted
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Save as lossless PNG with low compression
            frame_path = os.path.join(self.temp_dir, f"{frame_count + 1}.png")
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            
            frame_count += 1
            if progress_callback:
                progress_callback(frame_count, total_frames)
        
        cap.release()
        return frame_count
    
    def encode_frames_parallel(
        self,
        frame_list: List[str],
        data_bits: np.ndarray,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Encode data into multiple video frames in parallel
        
        :param frame_list: List of frame file paths
        :param data_bits: Bits to encode (flattened)
        :param progress_callback: Function(frames_done, total_frames)
        :return: Total bits encoded
        """
        total_frames = len(frame_list)
        bits_per_frame = len(data_bits) // total_frames
        
        def encode_frame_worker(args):
            frame_idx, frame_path = args
            start_bit = frame_idx * bits_per_frame
            end_bit = start_bit + bits_per_frame
            
            # Handle last frame
            if frame_idx == total_frames - 1:
                end_bit = len(data_bits)
            
            frame_bits = data_bits[start_bit:end_bit]
            
            # Read frame
            frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Cannot read frame: {frame_path}")
            
            # Flatten and embed LSBs
            flat = frame.flatten()
            n = min(len(frame_bits), len(flat))
            flat[:n] = (flat[:n].astype(np.uint8) & 0xFE) | frame_bits[:n].astype(np.uint8)
            
            # Reshape and save
            frame = flat.reshape(frame.shape)
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            
            return frame_idx, len(frame_bits)
        
        frames_done = 0
        total_bits = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(encode_frame_worker, (i, frame_list[i]))
                for i in range(total_frames)
            ]
            
            for future in as_completed(futures):
                frame_idx, bits_encoded = future.result()
                frames_done += 1
                total_bits += bits_encoded
                
                if progress_callback:
                    progress_callback(frames_done, total_frames)
        
        return total_bits
    
    def decode_frames_parallel(
        self,
        frame_list: List[str],
        expected_bits: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> np.ndarray:
        """
        Decode data from multiple video frames in parallel
        
        :param frame_list: List of frame file paths
        :param expected_bits: Number of bits to extract
        :param progress_callback: Function(frames_done, total_frames)
        :return: Extracted bits as numpy array
        """
        total_frames = len(frame_list)
        
        def decode_frame_worker(args):
            frame_idx, frame_path = args
            
            frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Cannot read frame: {frame_path}")
            
            flat = frame.flatten()
            lsb_bits = flat & 1
            
            return frame_idx, lsb_bits
        
        frames_done = 0
        all_bits = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(decode_frame_worker, (i, frame_list[i]))
                for i in range(total_frames)
            ]
            
            for future in as_completed(futures):
                frame_idx, bits = future.result()
                all_bits[frame_idx] = bits
                frames_done += 1
                
                if progress_callback:
                    progress_callback(frames_done, total_frames)
        
        # Concatenate in order
        extracted_bits = np.concatenate([all_bits[i] for i in range(total_frames)])
        return extracted_bits[:expected_bits]
    
    def reassemble_video_parallel(
        self,
        output_path: str,
        fps: float = 30.0,
        width: int = 1920,
        height: int = 1080,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Reassemble frames into video file
        
        :param output_path: Path to save video
        :param fps: Frames per second
        :param width: Video width
        :param height: Video height
        :param progress_callback: Function(frames_done, total_frames)
        :return: Path to output video
        """
        frame_files = sorted(
            [f for f in os.listdir(self.temp_dir) if f.endswith('.png')],
            key=lambda x: int(x.split('.')[0])
        )
        
        total_frames = len(frame_files)
        
        # Use FFmpeg for faster video encoding
        try:
            import subprocess
            frame_pattern = os.path.join(self.temp_dir, '%d.png')
            
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True, timeout=600)
            
            if progress_callback:
                progress_callback(total_frames, total_frames)
            
            return output_path
        
        except Exception as e:
            print(f"[!] FFmpeg failed: {e}, falling back to OpenCV")
            
            # Fallback to OpenCV
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frames_written = 0
            for frame_file in frame_files:
                frame_path = os.path.join(self.temp_dir, frame_file)
                frame = cv2.imread(frame_path)
                if frame is not None:
                    out.write(frame)
                    frames_written += 1
                    
                    if progress_callback:
                        progress_callback(frames_written, total_frames)
            
            out.release()
            return output_path


class GPUParallelProcessor:
    """
    GPU-accelerated parallel processor using CUDA
    Significantly faster frame operations
    """
    
    def __init__(self, batch_size: int = 16):
        """
        Initialize GPU parallel processor
        
        :param batch_size: Number of frames to process in one GPU batch
        """
        self.batch_size = batch_size
        self.device = None
        
        try:
            import torch
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"[+] GPU Processor initialized on {self.device}")
        except ImportError:
            print("[-] PyTorch not available for GPU processing")
    
    def encode_frames_gpu(
        self,
        frame_list: List[str],
        data_bits: np.ndarray,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        GPU-accelerated frame encoding
        
        :param frame_list: List of frame paths
        :param data_bits: Bits to encode
        :param progress_callback: Progress callback
        :return: Total bits encoded
        """
        if self.device is None or self.device.type == 'cpu':
            print("[-] GPU not available, using CPU fallback")
            processor = ParallelVideoProcessor()
            return processor.encode_frames_parallel(frame_list, data_bits, progress_callback)
        
        import torch
        
        total_frames = len(frame_list)
        bits_per_frame = len(data_bits) // total_frames
        total_bits_encoded = 0
        
        # Process frames in batches
        for batch_start in range(0, total_frames, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_frames)
            batch_frames = frame_list[batch_start:batch_end]
            
            # Load frames to GPU
            frames_tensor = []
            for frame_path in batch_frames:
                frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
                frame_tensor = torch.from_numpy(frame).to(self.device)
                frames_tensor.append(frame_tensor)
            
            # Process batch
            for i, (frame_path, frame_tensor) in enumerate(zip(batch_frames, frames_tensor)):
                frame_idx = batch_start + i
                start_bit = frame_idx * bits_per_frame
                end_bit = start_bit + bits_per_frame if frame_idx < total_frames - 1 else len(data_bits)
                
                frame_bits = torch.from_numpy(data_bits[start_bit:end_bit]).to(self.device)
                
                # Reshape and apply LSB
                flat = frame_tensor.flatten()
                flat[:len(frame_bits)] = (flat[:len(frame_bits)].byte() & 0xFE) | frame_bits[:len(flat)].byte()
                
                # Move back to CPU and save
                frame_out = flat.cpu().numpy().reshape(frame_tensor.shape)
                cv2.imwrite(frame_path, frame_out, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                
                total_bits_encoded += len(frame_bits)
            
            if progress_callback:
                progress_callback(batch_end, total_frames)
        
        return total_bits_encoded


# Utility function for performance benchmarking
def benchmark_parallel_encoding(
    frame_count: int,
    frame_size: tuple = (1920, 1080),
    data_size_mb: int = 100
):
    """
    Benchmark parallel frame encoding
    
    :param frame_count: Number of frames
    :param frame_size: Frame resolution (width, height)
    :param data_size_mb: Data size to encode in MB
    :return: Encoding rate (frames/sec, MB/sec)
    """
    import tempfile
    
    processor = ParallelVideoProcessor(max_workers=4)
    
    # Create dummy frames
    temp_dir = tempfile.mkdtemp()
    for i in range(frame_count):
        frame = np.random.randint(0, 256, (frame_size[1], frame_size[0], 3), dtype=np.uint8)
        cv2.imwrite(os.path.join(temp_dir, f"{i+1}.png"), frame)
    
    # Create dummy data
    data_bits = np.random.randint(0, 2, data_size_mb * 1024 * 1024 * 8)
    
    # Benchmark
    frame_list = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir)])
    
    start_time = time.time()
    bits_encoded = processor.encode_frames_parallel(frame_list, data_bits)
    elapsed = time.time() - start_time
    
    frames_per_sec = frame_count / elapsed
    mb_per_sec = (bits_encoded / 8 / 1024 / 1024) / elapsed
    
    return frames_per_sec, mb_per_sec, elapsed
