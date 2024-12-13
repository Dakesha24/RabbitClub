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
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QProgressBar, QWidget, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtGui import (
    QIcon, QFont, QPalette, QColor, QLinearGradient, QPainter, 
    QBrush, QGradient, QFontMetrics
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from utils import send_to_model, load_ollama_model, save_response, record_audio, transcribe, speak_response_in_chunks

class StyleSheet:
    MAIN_WINDOW = """
        QMainWindow {
            background-color: #FFF0F5;
        }
    """
    
    CHAT_BUBBLE = """
        QFrame {
            border-radius: 15px;
            padding: 10px;
        }
    """
    
    INPUT_TEXT = """
        QTextEdit {
            border: 2px solid #FF69B4;
            border-radius: 15px;
            padding: 10px;
            background-color: white;
            font-size: 14px;
        }
        QTextEdit:focus {
            border: 2px solid #FF1493;
        }
    """
    
    SEND_BUTTON = """
        QPushButton {
            background-color: #FF69B4;
            color: white;
            border-radius: 20px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #FF1493;
        }
        QPushButton:pressed {
            background-color: #DB7093;
        }
    """
    
    VOICE_BUTTON = """
        QPushButton {
            background-color: #DDA0DD;
            color: white;
            border-radius: 20px;
            padding: 10px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #BA55D3;
        }
        QPushButton:pressed {
            background-color: #9932CC;
        }
    """
    
    PROGRESS_BAR = """
        QProgressBar {
            border: 2px solid #FF69B4;
            border-radius: 5px;
            text-align: center;
            background-color: white;
        }
        QProgressBar::chunk {
            background-color: #FF69B4;
            border-radius: 3px;
        }
    """

class ChatBubble(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setStyleSheet(StyleSheet.CHAT_BUBBLE)
        self.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        
        if is_user:
            self.setStyleSheet(self.styleSheet() + "QFrame { background-color: #FFB6C1; }")
            layout.setAlignment(Qt.AlignRight)
        else:
            self.setStyleSheet(self.styleSheet() + "QFrame { background-color: #FFC0CB; }")
            layout.setAlignment(Qt.AlignLeft)
            
        layout.addWidget(label)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

class ChatArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.addStretch()
        self.setWidget(container)

    def add_message(self, text, is_user=True):
        bubble = ChatBubble(text, is_user)
        self.layout.insertWidget(self.layout.count() - 1, bubble)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class AudioRecorderThread(QThread):
    finished = pyqtSignal(str)
    
    def run(self):
        try:
            audio = record_audio()
            transcribed_text = transcribe(audio)
            self.finished.emit(transcribed_text)
        except Exception as e:
            print(f"Error in audio recording: {e}")
            self.finished.emit("")

class WorkerThread(QThread):
    progress_update = pyqtSignal(int)
    finished = pyqtSignal()
    
    def run(self):
        for i in range(101):
            self.progress_update.emit(i)
            time.sleep(0.01)
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Assistant")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(StyleSheet.MAIN_WINDOW)
        
        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Chat Assistant")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #FF1493;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Chat area
        self.chat_area = ChatArea()
        layout.addWidget(self.chat_area)
        
        # Input area container
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setSpacing(10)
        
        # Voice input button
        self.voice_button = QPushButton("🎤")
        self.voice_button.setStyleSheet(StyleSheet.VOICE_BUTTON)
        self.voice_button.setFixedSize(50, 50)
        self.voice_button.clicked.connect(self.start_voice_input)
        input_layout.addWidget(self.voice_button)
        
        # Message input
        self.input_text = QTextEdit()
        self.input_text.setStyleSheet(StyleSheet.INPUT_TEXT)
        self.input_text.setFixedHeight(50)
        self.input_text.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.input_text)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(StyleSheet.SEND_BUTTON)
        self.send_button.setFixedSize(100, 50)
        self.send_button.clicked.connect(self.on_send_clicked)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(input_container)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(StyleSheet.PROGRESS_BAR)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Thread setup
        self.worker_thread = WorkerThread()
        self.worker_thread.progress_update.connect(self.update_progress_bar)
        self.worker_thread.finished.connect(self.on_worker_finished)
        
        self.audio_thread = AudioRecorderThread()
        self.audio_thread.finished.connect(self.on_voice_input_finished)
        
        # Load the model
        self.system_content = load_ollama_model()

    def start_voice_input(self):
        self.voice_button.setEnabled(False)
        self.voice_button.setText("🔴")
        self.audio_thread.start()

    def on_voice_input_finished(self, text):
        self.voice_button.setEnabled(True)
        self.voice_button.setText("🎤")
        if text:
            self.input_text.setText(text)
            self.on_send_clicked()

    def on_send_clicked(self):
        user_input = self.input_text.toPlainText().strip()
        if user_input:
            # Add user message
            self.chat_area.add_message(user_input, True)
            self.input_text.clear()
            
            # Show progress bar
            self.progress_bar.setVisible(True)
            self.worker_thread.start()
            
            # Get response from model
            llama_response = send_to_model(user_input, self.system_content)
            if llama_response:
                # Add assistant message
                self.chat_area.add_message(llama_response, False)
                save_response(llama_response)
                # Speak the response
                threading.Thread(target=speak_response_in_chunks, args=(llama_response,)).start()
            else:
                self.chat_area.add_message("Sorry, I couldn't process your request.", False)

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)

    def on_worker_finished(self):
        self.progress_bar.setVisible(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            self.on_send_clicked()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()