import os
import time
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import pyaudio
import numpy as np
import keyboard
import ollama
from gtts import gTTS
from pydub import AudioSegment
import simpleaudio as sa
import threading
import eel
import json
import re
# Initialize eel with your web files directory
eel.init('www')

@eel.expose
def navigate_to_about():
    """Navigate to about page"""
    return True

@eel.expose
def navigate_to_chat():
    """Navigate back to chat"""
    return True

# Global variables
is_recording = False
play_obj = None
stop_playback = False

# Load Whisper model and processor once
processor = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
model.to("cuda" if torch.cuda.is_available() else "cpu")

# Microphone settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize PyAudio
p = pyaudio.PyAudio()

@eel.expose
def start_recording():
    """
    Start recording audio and return the transcription.
    This function is exposed to JavaScript.
    """
    global is_recording
    try:
        is_recording = True
        audio = record_audio()
        is_recording = False
        transcription = transcribe(audio)
        return transcription
    except Exception as e:
        print(f"Error in start_recording: {e}")
        return None
    finally:
        is_recording = False

@eel.expose
def stop_recording():
    """Stop recording audio."""
    global is_recording
    is_recording = False

@eel.expose
def send_message(message):
    """
    Process a message and return the AI response.
    This function is exposed to JavaScript.
    """
    try:
        system_content = load_ollama_model()
        response = send_to_model(message, system_content)
        if response:
            save_response(response['content'])
            # Expose the emotion for frontend
            eel.set_emotion(response['emotion'])
            # Start a new thread for audio playback
            threading.Thread(target=speak_response_in_chunks, args=(response['content'],)).start()
        return response['content']
    except Exception as e:
        print(f"Error in send_message: {e}")
        return None



# Function to load the Ollama model
def load_ollama_model():
    try:
        with open("personality.txt", "r", encoding='utf-8') as file: 
            system_content = file.read()
            system_content += (
                "\nLukman adalah teman terbaik kamu karena dia mengajari kamu banyak hal"
                "\nSelalu balas dalam bahasa Indonesia. "
                "\nKamu selalu memiliki salah satu emosi ketika menjawab, yaitu senang, marah, atau sedih"
                "\nwajib gunakan tag emosi yangs udah diberikan panduannya untuk menggambarkan emosi"
                "\nTolong saat menjawab, selalu selipkan satu kata kunci emosi dalam jawaban (senang, sedih, marah), tentukan perasaan anda sendiri: "
                "\nselalu tambahkan tag '[MOOD:senang]' untuk senang, '[MOOD:sedih]' untuk sedih, atau '[MOOD:marah]' untuk marah."
                "\ndilarang ada tag lain, hanya boleh tag '[MOOD:senang]' untuk senang, '[MOOD:sedih]' untuk sedih, atau '[MOOD:marah]' untuk marah"
                "\nSelalu balas dalam paragraf, jangan berupa poin poin. "
                "\nHindari referensi tentang diri sendiri yang tidak perlu kecuali jika ditanya, fokus pada percakapan yang ada."  
                "\njangan lupa sertakan tanda kutip ' 'untuk tag emosi jika sudah ada tidak usah"
            )
        return system_content
    except Exception as e:
        print(f"Error loading model: {e}")
        return ""

def extract_emotion(response):
    """
    Extract emotion from response and remove ALL tags except mood tags first,
    then remove mood tags after extracting the emotion.
    """
    # Detect emotion first from mood tags
    emotion = 'senang'  # default emotion
    mood_tags = {
        '[MOOD:senang]': 'senang',
        '[MOOD:sedih]': 'sedih',
        '[MOOD:marah]': 'marah'
    }
    
    # Extract emotion if mood tag exists
    for tag, mood in mood_tags.items():
        if tag in response:
            emotion = mood
            break
    
    # Remove ALL tags using regex
    # This will match anything between [ and ] including the brackets

    clean_response = re.sub(r'\[.*?\]', '', response)
    
    # Clean up any extra whitespace
    clean_response = ' '.join(clean_response.split())
    
    return emotion, clean_response

# Function to record audio
def record_audio():
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Recording...")
    frames = []
    
    # Record for 5 seconds (adjust as needed)
    for i in range(0, int(RATE / CHUNK * 5)):
        if not is_recording:
            break
        data = stream.read(CHUNK)
        frames.append(np.frombuffer(data, dtype=np.int16))
    
    stream.stop_stream()
    stream.close()
    
    if frames:
        audio = np.concatenate(frames).astype(np.float32) / 32768.0
        return audio
    return None

# Function to transcribe audio
def transcribe(audio):
    if audio is None:
        return None
        
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.to("cuda" if torch.cuda.is_available() else "cpu")
    
    if 'attention_mask' in inputs:
        attention_mask = inputs.attention_mask.to("cuda" if torch.cuda.is_available() else "cpu")
    else:
        attention_mask = torch.ones(input_features.shape, dtype=torch.int).to("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        predicted_ids = model.generate(input_features, attention_mask=attention_mask)
    
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcription

chat_history = []


# Function to send input to the Ollama model and get a response
def send_to_model(user_input, system_content):
    try:
        # Buat messages dengan riwayat chat
        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]
        
        # Tambahkan riwayat chat ke dalam messages
        for msg in chat_history:
            messages.append(msg)
            
        # Tambahkan input user saat ini
        messages.append({"role": "user", "content": user_input})
        
        # Kirim ke model dengan semua riwayat
        llama_response = ollama.chat(
            model="Llamactm",
            messages=messages
        )
        
        response = llama_response["message"]["content"]
        
        # Extract emotion dan clean response
        emotion, clean_response = extract_emotion(response)
        
        # Simpan pesan user dan response assistant ke history
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": clean_response})
        
        # Batasi riwayat chat (opsional, untuk menghemat memori)
        if len(chat_history) > 4:  # Simpan 10 pertukaran pesan terakhir
            chat_history.pop(0)  # Hapus pesan terlama
            chat_history.pop(0)
            
        return {
            "content": clean_response,
            "emotion": emotion
        }
    except Exception as e:
        print(f"Error getting response from llama: {e}")
        return None

# Function to split text into sentences
def split_text(text):
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in '.!?':
            sentences.append(current.strip())
            current = ""
    if current:
        sentences.append(current.strip())
    return sentences

# Function to create audio chunks and send them to frontend
@eel.expose
def speak_response_in_chunks(response, speed=1.2):
    temp_folder = "www/temp_audio"
    sentences = split_text(response)
    
    # Clear previous audio files
    for file in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, file)
        if file.endswith('.wav'):
            os.remove(file_path)
    
    # Generate audio chunks
    file_paths = []
    for idx, sentence in enumerate(sentences, start=1):
        try:
            print(f"Speaking: {sentence}")
            tts = gTTS(text=sentence, lang='id')
            filename_mp3 = os.path.join(temp_folder, f"response_{idx}.mp3")
            filename_wav = os.path.join(temp_folder, f"response_{idx}.wav")
            
            # Save and convert audio
            tts.save(filename_mp3)
            audio = AudioSegment.from_mp3(filename_mp3)
            audio = audio.speedup(playback_speed=speed)
            
            # Add a small silence at the end for smooth transition
            silence_duration = 100  # 100ms
            audio = audio + AudioSegment.silent(duration=silence_duration)
            
            audio.export(filename_wav, format="wav")
            
            # Collect the file paths for playback
            file_paths.append(f"temp_audio/response_{idx}.wav")
            
            # Clean up the MP3 file after conversion
            os.remove(filename_mp3)
                
        except Exception as e:
            print(f"Error processing sentence {idx}: {e}")
            continue

    # Send file paths to frontend for playback
    eel.startAudioPlayback(file_paths)()


def save_response(response):
    try:
        with open("response.txt", "w") as response_file:
            response_file.write("Assistant: " + response + "\n")
    except Exception as e:
        print(f"Error saving response: {e}")
        

# Start the application
if __name__ == "__main__":
    try:
        chrome_options = {
            "mode": "chrome",
            "port": 8000,
            "cmdline_args": [
                "--start-maximized",
                "--disable-notifications",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-features=TranslateUI",
                "--disable-save-password-bubble",
                "--disable-session-crashed-bubble",
                "--disable-popup-blocking",
                "--disable-overlay-scrollbar"
            ]
        }

        # Start Eel with your HTML file
        eel.start('index.html', mode='chrome', port=8000, size=(1366, 750))
    except Exception as e:
        print(f"Error starting application: {e}")
        
