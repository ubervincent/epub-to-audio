import utils.epub as epub
import openai
import json
from typing import List
from pydub import AudioSegment
from pathlib import Path

# call openai tts api to convert text to audio
def text_to_audio(json_file: str, output_file: str):
    with open(json_file, "r") as f:
        data = json.load(f)

    text = data[0]['text']

    for i, chunk in enumerate(chunk_text(text)):
        # do the rest of the chunks
        if i < 2:
            continue
        
        response = openai.audio.speech.create(
            model="tts-1-hd",
            voice="shimmer",
            input=chunk,
            speed=1.1
        )        

        response.stream_to_file(f"{output_file}_{i}.mp3") 

MAX_CHUNK_SIZE = 4000

def chunk_text(text: str) -> List[str]:
    if not text:
        raise ValueError("Input text cannot be empty")
        
    chunks = []
    while text:
        # Find the last sentence break within MAX_CHUNK_SIZE
        chunk_end = min(MAX_CHUNK_SIZE, len(text))
        if chunk_end < len(text):
            # Look for the last sentence ending (.!?) before MAX_CHUNK_SIZE
            for punct in ['. ', '! ', '? ']:
                last_punct = text[:chunk_end].rfind(punct)
                if last_punct != -1:
                    chunk_end = last_punct + 1
                    break
        
        chunks.append(text[:chunk_end].strip())
        text = text[chunk_end:].strip()
    
    return chunks

def splice_audio(path_to_folder: str):
    audio_files = list(Path(path_to_folder).glob("*_[0-9]*.mp3"))  # Only get numbered files
    if not audio_files:
        raise FileNotFoundError(f"No MP3 files found in {path_to_folder}")
    
    audio_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x.stem))))  # Extract just the numbers
    
    combined = AudioSegment.silent(duration=0)
    for audio_file in audio_files:
        combined += AudioSegment.from_mp3(audio_file)
    
    combined.export(f"{path_to_folder}/output.mp3", format="mp3")
    

if __name__ == "__main__":
    splice_audio("data")
