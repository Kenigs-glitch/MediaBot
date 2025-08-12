import cv2
import os
from pathlib import Path
from typing import List, Dict, Optional, Union


def get_video_info(video_path: str) -> Optional[Dict[str, Union[float, int]]]:
    """Get video properties"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None
    
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        return {
            'fps': fps,
            'width': width,
            'height': height,
            'frame_count': frame_count,
            'duration': frame_count / fps if fps > 0 else 0
        }
    finally:
        cap.release()


def extract_last_frame(video_path: str, output_path: Optional[str] = None) -> str:
    """Extract the last frame from a video and save as PNG."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame = None
        
        if total_frames <= 0:
            # Fallback: read through all frames
            while True:
                ret, current_frame = cap.read()
                if not ret:
                    break
                frame = current_frame
        else:
            # Try reading the last frame directly
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
            ret, frame = cap.read()
            
            if not ret or frame is None:
                # Fallback: try reading from a few frames before the end
                for offset in [2, 3, 4, 5]:
                    if total_frames - offset >= 0:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - offset)
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            break
        
        if frame is None:
            raise ValueError("Could not read the last frame")
            
    finally:
        cap.release()
    
    # Generate output filename if not provided
    if output_path is None:
        video_name = Path(video_path).stem
        output_path = f"{video_name}_last_frame.png"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the frame as PNG
    if not cv2.imwrite(output_path, frame):
        raise ValueError(f"Could not save frame to: {output_path}")
    
    return output_path


def concatenate_videos(video_paths: List[str], output_path: str, target_fps: Optional[float] = None) -> bool:
    """Concatenate multiple videos using OpenCV"""
    if len(video_paths) < 2:
        raise ValueError("Need at least 2 videos to concatenate")
    
    # Check all files exist
    for video_path in video_paths:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get info from first video for output settings
    first_video_info = get_video_info(video_paths[0])
    if not first_video_info:
        raise ValueError("Could not read first video properties")
    
    output_fps = target_fps or 20.0
    output_width = first_video_info['width']
    output_height = first_video_info['height']
    
    # Create output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, output_fps, (output_width, output_height))
    
    if not out.isOpened():
        raise ValueError("Could not create output video file")
    
    try:
        for video_path in video_paths:
            cap = cv2.VideoCapture(video_path)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize if needed
                if frame.shape[1] != output_width or frame.shape[0] != output_height:
                    frame = cv2.resize(frame, (output_width, output_height))
                
                out.write(frame)
            
            cap.release()
        
        return True
        
    except Exception as e:
        raise Exception(f"Error during video concatenation: {str(e)}")
        
    finally:
        out.release() 