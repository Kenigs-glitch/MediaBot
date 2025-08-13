import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from config import (
    MAX_FRAMES_PER_SEGMENT, DEFAULT_FPS, TEMP_DIR,
    TEMP_FRAME_PREFIX, TEMP_VIDEO_PREFIX, COMFYUI_OUTPUT_DIR
)
from media_utils import process_image_to_video, wait_for_generation, get_latest_video
from video_utils import extract_last_frame, concatenate_videos


class LongVideoGenerator:
    def __init__(self, comfyui_url: str, workflow_file: str, generation_timeout: int):
        """Initialize the long video generator"""
        self.comfyui_url = comfyui_url
        self.workflow_file = workflow_file
        self.generation_timeout = generation_timeout
        self.temp_dir = TEMP_DIR
        self.segments: List[Dict] = []
        logger.info(f"Initialized LongVideoGenerator with ComfyUI URL: {comfyui_url}, workflow: {workflow_file}")
        
    async def generate_video_segment(self, prompt: str, image_path: str, n_frames: int) -> str:
        """Generate a single video segment"""
        logger.info(f"Generating video segment with prompt: {prompt}, image: {image_path}, frames: {n_frames}")
        
        # Process the image to video
        prompt_id = await process_image_to_video(
            prompt,
            image_path,
            n_frames,
            self.comfyui_url,
            self.workflow_file
        )
        logger.info(f"Got prompt ID from ComfyUI: {prompt_id}")
        
        # Wait for generation to complete
        await wait_for_generation(prompt_id, self.comfyui_url, self.generation_timeout)
        logger.info("Generation completed, looking for output video")
        
        # Get the generated video
        video_path = get_latest_video(COMFYUI_OUTPUT_DIR)
        if not video_path:
            logger.error(f"No output video found in {COMFYUI_OUTPUT_DIR}")
            raise Exception("No output video found")
        
        logger.info(f"Found output video at: {video_path}")
        
        # Copy video to temp directory with unique name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        segment_path = self.temp_dir / f"{TEMP_VIDEO_PREFIX}{timestamp}.mp4"
        logger.info(f"Copying video from {video_path} to {segment_path}")
        
        try:
            shutil.copy2(str(video_path), str(segment_path))
            logger.info(f"Successfully copied video to {segment_path}")
            try:
                os.remove(video_path)
                logger.info(f"Successfully removed original video at {video_path}")
            except Exception as e:
                logger.warning(f"Failed to remove original video at {video_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to copy video from {video_path} to {segment_path}: {e}")
            raise
        
        return str(segment_path)
    
    async def generate_long_video(
        self,
        initial_prompt: str,
        initial_image: str,
        segments_data: List[Dict[str, any]]
    ) -> str:
        """
        Generate a long video by concatenating multiple segments
        
        segments_data: List of dicts with keys:
            - frames: int (number of frames)
            - prompt: Optional[str] (if None, uses previous prompt)
        """
        video_segments = []
        current_image = initial_image
        current_prompt = initial_prompt
        
        try:
            # Generate each segment
            for i, segment in enumerate(segments_data):
                frames = segment['frames']
                prompt = segment.get('prompt') or current_prompt
                
                # Generate video segment
                video_path = await self.generate_video_segment(prompt, current_image, frames)
                video_segments.append(video_path)
                
                # Extract last frame for next segment if not the last one
                if i < len(segments_data) - 1:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    last_frame_path = self.temp_dir / f"{TEMP_FRAME_PREFIX}{timestamp}.png"
                    current_image = extract_last_frame(video_path, str(last_frame_path))
                    current_prompt = prompt
            
            # Concatenate all segments
            if len(video_segments) > 1:
                output_path = self.temp_dir / f"final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                concatenate_videos(video_segments, str(output_path), DEFAULT_FPS)
                return str(output_path)
            else:
                return video_segments[0]
                
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files(video_segments)
    
    def _cleanup_temp_files(self, keep_files: Optional[List[str]] = None):
        """Clean up temporary files except the ones in keep_files"""
        keep_files = set(keep_files or [])
        
        for pattern in [f"{TEMP_FRAME_PREFIX}*", f"{TEMP_VIDEO_PREFIX}*"]:
            for file in self.temp_dir.glob(pattern):
                if str(file) not in keep_files:
                    try:
                        os.remove(file)
                    except Exception:
                        pass  # Ignore cleanup errors 