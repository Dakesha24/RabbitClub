// DOM Elements
const messageInput = document.getElementById('messageInput');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const voiceInputBtn = document.getElementById('voiceInputBtn');
const chatMessages = document.getElementById('chatMessages');
const recordingIndicator = document.getElementById('recordingIndicator');

const historyBtn = document.getElementById('historyBtn');
const historyPopup = document.getElementById('historyPopup');
const closeHistory = document.getElementById('closeHistory');
const historyMessages = document.getElementById('historyMessages');
const loadingIndicator = document.getElementById('loadingIndicator');

const stopRecordingBtn = document.getElementById('stopRecordingBtn');

const typingSpeed = 30;

// State
let isRecording = false;

// Store messages history
let messageHistory = [];


// Function to add a message to the chat
function addMessage(message, isUser = false) {
    // Add to history
    messageHistory.push({ message, isUser, timestamp: new Date().toLocaleTimeString() });
    
    // Clear existing messages in the chat
    chatMessages.innerHTML = '';
    
    // Only show the latest AI response if it's not from the user
    if (!isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add('assistant');
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Typing effect
        typeMessageEffect(messageDiv, message);
    }
    
    // Update history view
    updateHistoryView();
}

async function typeMessageEffect(element, message) {
    let i = 0;
    while (i < message.length) {
        element.textContent += message.charAt(i);
        i++;
        await new Promise(resolve => setTimeout(resolve, typingSpeed));
    }
}

// Function to handle sending messages
async function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        try {
            addMessage(message, true);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            sendMessageBtn.disabled = true;
            
            // Show loading indicator
            loadingIndicator.style.display = 'flex';
            
            const response = await eel.send_message(message)();
            
            if (response) {
                addMessage(response);
            } else {
                addMessage('Sorry, I encountered an error processing your message.', false);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Sorry, there was an error communicating with the assistant.', false);
        } finally {
            sendMessageBtn.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    }
}


// Function to handle voice input
async function startVoiceInput() {
    if (!isRecording) {
        try {
            isRecording = true;
            recordingIndicator.style.display = 'flex';
            voiceInputBtn.style.display = 'none'; // Hide mic button
            stopRecordingBtn.style.display = 'inline-flex'; // Show stop button
            
            // Start recording and get transcription
            const transcription = await eel.start_recording()();
            
            if (transcription) {
                messageInput.value = transcription;
                await sendMessage();
            } else {
                addMessage('Sorry, I couldn\'t understand the audio input.', false);
            }
        } catch (error) {
            console.error('Error recording audio:', error);
            addMessage('Sorry, there was an error processing your voice input.', false);
        } finally {
            stopRecording();
        }
    }
}

function stopRecording() {
    isRecording = false;
    recordingIndicator.style.display = 'none';
    voiceInputBtn.style.display = 'inline-flex'; // Show mic button again
    stopRecordingBtn.style.display = 'none'; // Hide stop button
    eel.stop_recording()(); // You'll need to create this Python function
}

stopRecordingBtn.addEventListener('click', stopRecording);

// Event Listeners
sendMessageBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

voiceInputBtn.addEventListener('click', startVoiceInput);

// Auto-resize textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Listen for Shift key to handle voice recording
// document.addEventListener('keydown', (e) => {
//     if (e.key === 'Shift' && !isRecording) {
//         startVoiceInput();
//     }
// });

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Add welcome message
    addMessage('Hello! Ada yang mau kamu obrolin?', false);
    

});

document.addEventListener('DOMContentLoaded', function() {
    const aboutLogo = document.getElementById('aboutLogo');
    const aboutPopup = document.getElementById('aboutPopup');
    const closeAbout = document.getElementById('closeAbout');

    // Toggle about popup
    aboutLogo.addEventListener('click', function() {
        aboutPopup.classList.add('active');
    });

    // Close about popup
    closeAbout.addEventListener('click', function() {
        aboutPopup.classList.remove('active');
    });

    // Close popup when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === aboutPopup) {
            aboutPopup.classList.remove('active');
        }
    });
});

function updateHistoryView() {
    historyMessages.innerHTML = '';
    messageHistory.forEach(({ message, isUser, timestamp }) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'assistant');
        
        const timeSpan = document.createElement('span');
        timeSpan.classList.add('message-time');
        timeSpan.textContent = timestamp;
        
        const textDiv = document.createElement('div');
        textDiv.textContent = message;
        
        messageDiv.appendChild(timeSpan);
        messageDiv.appendChild(textDiv);
        historyMessages.appendChild(messageDiv);
    });
}

historyBtn.addEventListener('click', () => {
    historyPopup.classList.add('active');
});

closeHistory.addEventListener('click', () => {
    historyPopup.classList.remove('active');
});

// Close history popup when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === historyPopup) {
        historyPopup.classList.remove('active');
    }
});


// Tambahkan di bagian awal script.js
const fullscreenBtn = document.getElementById('fullscreenBtn');
const fullscreenIcon = document.getElementById('fullscreenIcon');

function toggleFullScreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.log(`Error attempting to enable fullscreen: ${err.message}`);
        });
        fullscreenIcon.classList.remove('fa-expand');
        fullscreenIcon.classList.add('fa-compress');
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
            fullscreenIcon.classList.remove('fa-compress');
            fullscreenIcon.classList.add('fa-expand');
        }
    }
}

// Event listener untuk tombol fullscreen
fullscreenBtn.addEventListener('click', toggleFullScreen);

// Event listener untuk perubahan status fullscreen
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) {
        fullscreenIcon.classList.remove('fa-compress');
        fullscreenIcon.classList.add('fa-expand');
    } else {
        fullscreenIcon.classList.remove('fa-expand');
        fullscreenIcon.classList.add('fa-compress');
    }
});

// Character animation states
// Character animation states
const characterStates = {
    current: 'idle',
    transitioning: false
};

// Emotion mapping
const emotionMap = {
    'marah': 'angry',
    'sedih': 'sad',
    'senang': 'idle'
};

// Animation duration settings (in milliseconds)
const ANIMATION_DURATION = {
    in: 600,    // Durasi _in.gif
    idle: 20000,  // Durasi menampilkan _idle.gif
    out: 600    // Durasi _out.gif
};

function updateCharacterAnimation(emotion) {
    const characterImage = document.getElementById('characterImage');
    const mouthImage = document.getElementById('mouthImage');
    if (!characterImage || !mouthImage) {
        console.error('Character or mouth element not found');
        return;
    }

    // Map emotion dari Bahasa Indonesia ke nama file
    const mappedEmotion = emotionMap[emotion] || 'idle';
    console.log('Updating animation to:', mappedEmotion);
    
    // Jangan mulai animasi baru jika masih dalam transisi
    if (characterStates.transitioning) return;
    
    // Jangan ulangi animasi yang sama
    if (characterStates.current === mappedEmotion) return;

    // Set status transisi dan update current emotion
    characterStates.transitioning = true;
    characterStates.current = mappedEmotion;  // Update current emotion di awal

    async function playAnimationSequence() {
        try {
            if (mappedEmotion === 'idle') {
                characterImage.src = 'assets/character/idle/idle.gif';
                mouthImage.src = 'assets/character/idle/idle_closedmouth.png';
                characterStates.transitioning = false;
                return;
            }

            // 1. Play entrance animation
            console.log('Playing entrance animation');
            characterImage.src = `assets/character/${mappedEmotion}/${mappedEmotion}_in.gif`;
            await new Promise(resolve => setTimeout(resolve, ANIMATION_DURATION.in));

            // 2. Play idle animation
            console.log('Playing idle animation');
            characterImage.src = `assets/character/${mappedEmotion}/${mappedEmotion}_idle.gif`;
            await new Promise(resolve => setTimeout(resolve, ANIMATION_DURATION.idle));

            // 3. Play exit animation
            console.log('Playing exit animation');
            characterImage.src = `assets/character/${mappedEmotion}/${mappedEmotion}_out.gif`;
            await new Promise(resolve => setTimeout(resolve, ANIMATION_DURATION.out));

            // Tetap pada emosi yang sama setelah sequence selesai
            characterImage.src = 'assets/character/idle/idle.gif';
            mouthImage.src = 'assets/character/idle/idle_closedmouth.png';
            
            characterStates.transitioning = false;
            // PENTING: Jangan reset ke idle di sini
        } catch (error) {
            console.error('Error in animation sequence:', error);
            characterStates.transitioning = false;
        }
    }

    playAnimationSequence();


}


let currentEmotion = 'senang'; // Default emotion
let isPlayingAudio = false; // Indicates if the audio is playing
let isAnalyzing = false;
let audioContext;
let analyser;
let javascriptNode;
let audioSourceNode;
let audioBuffer;
let lastAmplitude = 0; // Untuk menyimpan amplitudo sebelumnya
let mouthState = "closed"; // Menyimpan status mulut (terbuka atau tertutup)
let mouthAnimationSpeed = 68; // Kecepatan animasi mulut dalam milidetik (lebih kecil lebih cepat)
let lastMouthChange = Date.now(); // Waktu terakhir mulut berubah
const mouthImage = document.getElementById('mouthImage');

// Fungsi untuk memproses dan menganalisis file audio dalam urutan yang benar
async function processAudioFiles(audioFiles) {
    console.log('Processing audio files:', audioFiles);
    console.log('Current emotion:', currentEmotion);

    if (!audioFiles || audioFiles.length === 0) {
        console.error('No audio files found');
        return;
    }

    // Sort audio files based on the number at the end of the filename
    audioFiles.sort((a, b) => {
        const numA = parseInt(a.match(/response_(\d+)\.wav$/)[1]);
        const numB = parseInt(b.match(/response_(\d+)\.wav$/)[1]);
        return numA - numB;
    });

    // Function to process and play each file in sequence
    let currentFileIndex = 0;

    function playNextFile() {
        if (currentFileIndex >= audioFiles.length) {
            console.log('All audio files have been played');
            isPlayingAudio = false;
            isAnalyzing = false; // Stop analyzing when playback is finished
            return;
        }

        const file = audioFiles[currentFileIndex];
        console.log('Processing file:', file);

        const request = new XMLHttpRequest();
        request.open('GET', file, true);
        request.responseType = 'arraybuffer';

        request.onload = function() {
            audioContext.decodeAudioData(request.response, function(buffer) {
                audioBuffer = buffer;
                playAudioBuffer();
                currentFileIndex++;
            }, function(e) {
                console.error('Error decoding audio data:', e);
            });
        };
        request.send();
    }

    function playAudioBuffer() {
        audioSourceNode = audioContext.createBufferSource();
        audioSourceNode.buffer = audioBuffer;

        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;  // Ukuran FFT menentukan resolusi analisis
        audioSourceNode.connect(analyser);
        analyser.connect(audioContext.destination);
        audioSourceNode.connect(audioContext.destination);

        audioSourceNode.start(0);

        isPlayingAudio = true; // Set flag isPlayingAudio menjadi true
        startAnalyzingAudio();

        audioSourceNode.onended = function() {
            console.log('Audio ended');
            playNextFile();
        };
    }

    playNextFile();
}

// Fungsi untuk menerima emosi dan memperbarui animasi mulut
function startAnalyzingAudio() {
    console.log('Starting audio analysis with emotion:', currentEmotion);

    const characterImage = document.getElementById('characterImage');
    const mouthImage = document.getElementById('mouthImage');
    if (!characterImage || !mouthImage) {
        console.error('Character or mouth element not found');
        return;
    }

    const mappedEmotion = emotionMap[currentEmotion] || 'idle';
    console.log('Updating animation to:', mappedEmotion);

    if (!audioContext) {
        console.error('Audio context not initialized');
        return;
    }

    if (!isAnalyzing) {
        isAnalyzing = true;
        javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);
        javascriptNode.connect(audioContext.destination);
        analyser.connect(javascriptNode);

        javascriptNode.onaudioprocess = function() {
            if (!isAnalyzing) {
                javascriptNode.disconnect();
                analyser.disconnect();
                return;
            }

            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(dataArray);

            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }

            let averageAmplitude = sum / dataArray.length;

            const now = Date.now();

            if (now - lastMouthChange > mouthAnimationSpeed) {
                if (averageAmplitude > lastAmplitude) {
                    mouthState = "open";
                } else if (averageAmplitude < lastAmplitude) {
                    mouthState = "closed";
                }

                if (averageAmplitude < 20 && mouthState === "open") {
                    mouthState = "closed"; 
                }

                lastMouthChange = now;

                mouthImage.src = `assets/character/${mappedEmotion}/${mappedEmotion}_${mouthState}mouth.png`;
            }

            lastAmplitude = averageAmplitude;
        };
    }
}


// Expose function untuk Python
eel.expose(set_emotion);
function set_emotion(emotion) {
    console.log("Emotion received from backend:", emotion);
    currentEmotion = emotion; // Update current emotion
    updateCharacterAnimation(emotion);
    if (isPlayingAudio) {
        startAnalyzingAudio();
    }
}



// Fungsi untuk memulai pemrosesan file audio dari folder yang ditentukan
eel.expose(startAudioPlayback);
function startAudioPlayback(audioFiles) {
    console.log('Starting audio playback with files:', audioFiles);
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('AudioContext created');
    }
    processAudioFiles(audioFiles);
}
