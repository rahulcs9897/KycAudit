import os
import tempfile
from typing import Dict, Any
from moviepy import VideoFileClip
from groq import Groq
from app.graph.state import KYCState

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio_node(state: KYCState) -> Dict[str, Any]:
    """Extracts audio from the video locally, then sends the lightweight audio to Groq."""

    video_path = state.get("video_file_path")

    if not video_path or not os.path.exists(video_path):
        return {"error_message": "Video file not found."}

    print(f"--- 🎬 EXTRACTING AUDIO FROM VIDEO: {video_path} ---")

    try:
        # 1. Load the video file
        video = VideoFileClip(video_path)

        # 2. Create a temporary file to hold the extracted audio
        temp_audio_path = os.path.join(tempfile.gettempdir(),"extracted_kyc_audio.mp3")

        # 3. Write the audio track to the temporary file (silently)
        video.audio.write_audiofile(temp_audio_path, logger=None)

        # Close the video to free up system memory
        video.close()

        print(f"--- 🎙️ SENDING EXTRACTED AUDIO TO GROQ WHISPER ---")

        # 4. Send the lightweight .mp3 file to Groq
        with open(temp_audio_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_audio_path, file.read()),
                model="whisper-large-v3",
                response_format="text",
            )

        # 5. Clean up the temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        return {"transcript": transcription}

    except Exception as e:
        print(f"❌ Audio Extraction/Transcription Failed: {str(e)}")
        return {"error_message": str(e)}


