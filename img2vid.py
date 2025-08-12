import json
import requests
import time
import os

# Configuration
COMFYUI_URL = "http://192.168.100.11:8188"
WORKFLOW_FILE = "wan2.2_img_to_vid.json"  # Your exported workflow file

# Parameters to modify
NEW_PROMPT = "a video of a dog running in a park"
NEW_HEIGHT = 720
NEW_WIDTH = 1280
NEW_FRAMES = 101  # Number of frames to generate
NEW_INPUT_IMAGE = "1000000231.jpg"  # Input image filename

def modify_and_run_workflow():
    # Load workflow
    if not os.path.exists(WORKFLOW_FILE):
        print(f"Error: {WORKFLOW_FILE} not found!")
        return
    
    with open(WORKFLOW_FILE, 'r') as f:
        workflow = json.load(f)
    
    # Function to recursively search and replace values
    def replace_in_dict(obj, old_prompt, new_prompt, old_height, new_height, old_width, new_width, old_frames, new_frames, old_image, new_image):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value == old_prompt:
                    obj[key] = new_prompt
                    print(f"✓ Updated prompt")
                elif value == old_height or value == str(old_height):
                    obj[key] = new_height
                    print(f"✓ Updated height: {old_height} -> {new_height}")
                elif value == old_width or value == str(old_width):
                    obj[key] = new_width
                    print(f"✓ Updated width: {old_width} -> {new_width}")
                elif value == old_frames or value == str(old_frames):
                    obj[key] = new_frames
                    print(f"✓ Updated frames: {old_frames} -> {new_frames}")
                elif value == old_image:
                    obj[key] = new_image
                    print(f"✓ Updated input image: {old_image} -> {new_image}")
                else:
                    replace_in_dict(value, old_prompt, new_prompt, old_height, new_height, old_width, new_width, old_frames, new_frames, old_image, new_image)
        elif isinstance(obj, list):
            for item in obj:
                replace_in_dict(item, old_prompt, new_prompt, old_height, new_height, old_width, new_width, old_frames, new_frames, old_image, new_image)
    
    # Replace values
    print("Modifying workflow...")
    replace_in_dict(workflow, 
                   "a video of a beautiful blondie woman doing gymnastics on the floor", NEW_PROMPT,
                   720, NEW_HEIGHT,
                   1280, NEW_WIDTH,
                   101, NEW_FRAMES,
                   "combined_opencv_last_frame.png", NEW_INPUT_IMAGE)
    
    # Send to ComfyUI
    print(f"\nSending to ComfyUI at {COMFYUI_URL}")
    print(f"Prompt: {NEW_PROMPT}")
    print(f"Size: {NEW_WIDTH}x{NEW_HEIGHT}")
    print(f"Frames: {NEW_FRAMES}")
    print(f"Input image: {NEW_INPUT_IMAGE}")
    
    try:
        response = requests.post(f"{COMFYUI_URL}/prompt", 
                               json={"prompt": workflow, "client_id": "python_client"})
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result['prompt_id']
            print(f"✓ Queued successfully! Prompt ID: {prompt_id}")
            
            # Simple polling for completion
            print("Waiting for completion...")
            while True:
                history_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    if prompt_id in history_data:
                        print("✓ Generation completed!")
                        break
                
                time.sleep(3)  # Check every 3 seconds
                print(".", end="", flush=True)
        
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        print("Make sure ComfyUI is running and accessible at the specified address")

if __name__ == "__main__":
    modify_and_run_workflow()