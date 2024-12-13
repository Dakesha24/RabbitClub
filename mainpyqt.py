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

#import ui PQT5
#from PyQt5.QtWidgets import QApplication
#from ui import MainWindow
import eel

#ambil fungsi yang ada di utils
from utils import send_to_model, load_ollama_model, save_response


#jika ingin exe (pakai pyqt)
# if __name__ == "__main__":
#     app = QApplication([])
#     window = MainWindow()
#     window.show()
#     app.exec_()

eel.init('web')

# Global variables
play_obj = None
stop_playback = False

# Load Whisper model and processor once
processor = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
model.to("cuda" if torch.cuda.is_available() else "cpu")

# Function to load the Ollama model
#dipindahkan ke utils.py ==>

# Microphone settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize PyAudio
p = pyaudio.PyAudio()

# Function to record audio
#dipindahin ke utils =>

# Function to transcribe audio
#dipindahin ke utils

# Function to send input to the Ollama model and get a response
#dipindahkan ke utils.py ==>

# Audio playback function with timer
def play_audio_with_timer(file_path, duration):
    try:
        audio = AudioSegment.from_file(file_path)
        print(f"Playing {file_path}, duration: {duration:.2f} seconds.")
        play_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj.play()
        time.sleep(duration)  # Wait for the audio to finish based on its duration
    except Exception as e:
        print(f"Error playing audio: {e}")

# Function to delete previous audio files
def delete_previous_audio(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {filename}")

# Function to save and play response as audio in chunks
#dipindahin ke utils =>

# Function to split response into chunks based on punctuation (optional)
def split_text(text):
    punctuation_marks = ['.', '?', '!']
    sentences = []
    sentence = ""
    for char in text:
        sentence += char
        if char in punctuation_marks:
            sentences.append(sentence.strip())
            sentence = ""
    if sentence:
        sentences.append(sentence.strip())  # Add the last part if any
    return sentences

def chat_with_model(system_content):
    print("************************")
    print("Welcome to LLMmodel By Lukman")
    print("Enter 'exit' to leave the chat")
    print("Type 'push-talk' to use voice input for the next response")
    print("Type 'stop-say' to stop current playback")
    print("************************")
    
    # Start listening thread for Whisper
    threading.Thread(target=listen_for_input, args=(system_content,), daemon=True).start()

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Ending chat. Goodbye!")
            break
        elif user_input.lower() == 'push-talk':
            print("Please press 'Shift' to record your input.")
        elif user_input.lower() == 'stop-say':
            stop_audio()
            stop_playback = False  # Reset the stop_playback flag
        else:
            llama_response = send_to_model(user_input, system_content)
            if llama_response:
                print("Alicia: " + llama_response)
                save_response(llama_response)
                speak_response_in_chunks(llama_response)  # Speak response in chunks
            else:
                print("No response from Alicia.")

def listen_for_input(system_content):
    while True:
        if keyboard.is_pressed('shift'):
            audio = record_audio()
            user_input = transcribe(audio)
            print(f"You: {user_input}")  # Print the transcribed input
            if user_input.lower() == 'exit':
                print("Ending chat. Goodbye!")
                break
            else:
                llama_response = send_to_model(user_input, system_content)
                if llama_response:
                    print("Alicia: " + llama_response)
                    save_response(llama_response)
                    speak_response_in_chunks(llama_response)  # Speak response in chunks

# Save Response
#dipindahkan ke utils.py

# Load Ollama model
system_content = load_ollama_model()

# Start the chat
chat_with_model(system_content)
