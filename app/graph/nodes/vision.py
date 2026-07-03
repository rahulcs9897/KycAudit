import os
import base64
from io import BytesIO
from typing import Dict, Any
from PIL import Image
from moviepy import VideoFileClip
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.graph.state import KYCState

vision_llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.0)

def analyze_vision_node(state: KYCState) -> Dict[str, Any]:
    """Extracts keyframes and passes them to Llama 4 Vision for concise classification."""
    video_path = state.get("video_file_path")
    
    expected_name = state.get("expected_name", "Unknown")
    expected_dob = state.get("expected_dob", "Unknown")

    if not video_path or not os.path.exists(video_path):
        return {}

    print(f"--- 👁️ EXTRACTING FRAMES FOR VISION ANALYSIS ---")
    base64_frames = []
    try:
        video = VideoFileClip(video_path)
        for t in range(0, int(video.duration), 3):
            img = Image.fromarray(video.get_frame(t))
            img.thumbnail((1024, 1024))
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=70)
            base64_frames.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
        video.close()
    except Exception as e:
        return {"detected_anomalies": [f"VIDEO ERROR: {str(e)}"]}

    # 🔥 STRICTLY CONCISE PROMPT: No conversational output allowed
    vision_prompt = f"""
    You are a strict KYC validation tool. Check these frames for:
    1. A valid Government ID presentation (NOT a coffee/credit card, fake paper, or digital screen).
    2. Legible Name matching '{expected_name}'.
    3. Legible DOB matching '{expected_dob}'.

    OUTPUT RULES:
    - If ALL checks pass perfectly, output exactly: CLEAR
    - If no valid ID is found, output exactly: FRAUD: Invalid Document Type
    - If the name/DOB is missing or incorrect, output exactly: FRAUD: Data Mismatch

    DO NOT include any commentary, description, rules, or introduction. Output exactly one of the labels above.
    """

    message_content = [{"type": "text", "text": vision_prompt}]
    for b64_img in base64_frames[:5]:
        message_content.append({"type": "image_url", "image_url":{"url": f"data:image/jpeg;base64,{b64_img}"}})

    anomalies = []
    try:
        response = vision_llm.invoke([HumanMessage(content=message_content)])
        result = response.content.strip()
        
        # Guard against conversational leakage
        if "CLEAR" not in result.upper():
            # If the model leaks text, extract just the line containing FRAUD
            for line in result.split("\n"):
                if "FRAUD" in line.upper():
                    anomalies.append(line.strip())
                    break
            else:
                anomalies.append(f"VIDEO ANOMALY: {result}")
            print(f"⚠️ VISION FLAG CAUGHT: {anomalies}")
            
    except Exception as e:
        anomalies.append(f"VIDEO ERROR: {str(e)}")

    return {"detected_anomalies": anomalies}