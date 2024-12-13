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

def load_ollama_model():
    with open("personality.txt", "r") as file:
        system_content = file.read()
    return system_content

def send_to_model(user_input, system_content):
    try:
        llama_response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_input},
            ],
        )
        return llama_response["message"]["content"]
    except Exception as e:
        print(f"Error getting response from llama: {e}")
        return None


def save_response(response):
    with open("response.txt", "w") as response_file:
        response_file.write("Alicia: " + response + "\n")
    print("Response saved to response.txt.")

def record_audio():
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Listening... Press 'Shift' to record.")
    frames = []

    while True:
        if keyboard.is_pressed('shift'):
            print("Recording... Speak now.")
            frames = []
            while keyboard.is_pressed('shift'):
                data = stream.read(CHUNK)
                frames.append(np.frombuffer(data, dtype=np.int16))
            print("Finished recording.")
            break

    stream.stop_stream()
    stream.close()
    audio = np.concatenate(frames).astype(np.float32) / 32768.0
    return audio


def transcribe(audio):
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

def speak_response_in_chunks(response, speed=1.2):
    # Ensure the temp_audio folder exists
    temp_folder = "temp_audio"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    sentences = split_text(response)  # Split response into chunks based on punctuation marks
    
    # Prepare audio files sequentially with numbers
    audio_files = []
    durations = []  # Store durations of each audio file
    
    for idx, sentence in enumerate(sentences, start=1):
        print(f"Speaking: {sentence}")

        # Save as MP3 first
        tts = gTTS(text=sentence, lang='id')
        filename_mp3 = os.path.join(temp_folder, f"response_{idx}.mp3")
        tts.save(filename_mp3)

        # Convert MP3 to WAV using pydub
        audio = AudioSegment.from_mp3(filename_mp3)
        
        # Speed up the audio with pydub
        audio = audio.speedup(playback_speed=speed)  # Increase speed
        filename_wav = os.path.join(temp_folder, f"response_{idx}.wav")
        audio.export(filename_wav, format="wav")  # Save as WAV

        # Add WAV file to the list
        audio_files.append(filename_wav)
        durations.append(len(audio) / 1000.0)  # Get the duration in seconds

    # Play all audio files sequentially with delay based on their durations
    for i, audio_file in enumerate(audio_files):
        play_audio_with_timer(audio_file, durations[i])

    # After all audio files are played, don't delete until a new session starts
    print("Finished playback. Waiting for new session...")