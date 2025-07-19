import os
import re
import time
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import pyttsx3
from pytube import Search
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading

# --- CONFIGURATION ---
SPOTIFY_CLIENT_ID = '9cff449028b34ad482312b53ba0da51d'
SPOTIFY_CLIENT_SECRET = '293654cd3ead483bbd53b594a8f962e3'
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
WAKE_WORDS = ['rose', 'sara', 'computer']

# --- SETUP TTS ENGINE ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
female_voice_found = False
for voice in voices:
    if 'female' in voice.name.lower() or 'female' in voice.id.lower():
        engine.setProperty('voice', voice.id)
        female_voice_found = True
        break
if not female_voice_found:
    print("No female voice found. Using default voice.")

def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# --- SETUP SPOTIFY ---
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
))

# --- VOICE RECOGNITION ---
recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen_for_wake_word():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for wake word...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"Heard: {text}")
        for wake_word in WAKE_WORDS:
            if wake_word in text:
                return True
    except sr.UnknownValueError:
        pass
    return False

def listen_for_command():
    speak("Listening for your command.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Command: {command}")
        return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return None

# --- SPOTIFY CONTROL ---
def transfer_playback_to_active_device():
    devices = sp.devices()
    if devices['devices']:
        device_id = devices['devices'][0]['id']
        sp.transfer_playback(device_id=device_id, force_play=True)
    else:
        speak("No active Spotify device found. Please open Spotify on your device and try again.")

def play_spotify_song(song=None, artist=None):
    query = ""
    if song and artist:
        query = f"track:{song} artist:{artist}"
    elif song:
        query = f"track:{song}"
    elif artist:
        query = f"artist:{artist}"
    else:
        speak("Please specify a song or artist.")
        return
    results = sp.search(q=query, type='track', limit=1)
    tracks = results.get('tracks', {}).get('items', [])
    if tracks:
        track = tracks[0]
        uri = track['uri']
        transfer_playback_to_active_device()
        sp.start_playback(uris=[uri])
        speak(f"Playing {track['name']} by {track['artists'][0]['name']} on Spotify.")
    else:
        speak("Sorry, I couldn't find that song on Spotify.")

def spotify_control(action):
    try:
        if action == "pause":
            sp.pause_playback()
            speak("Music paused.")
        elif action == "resume":
            sp.start_playback()
            speak("Resuming music.")
        elif action == "next": 
            sp.next_track()
            speak("Playing next song.")
        elif action == "previous":
            sp.previous_track()
            speak("Playing previous song.")
        elif action == "stop":
            sp.pause_playback()
            speak("Music stopped.")
    except Exception as e:
        speak("Sorry, I couldn't control Spotify playback.")

# --- YOUTUBE PLAYBACK ---
def play_youtube_song(song, artist=None):
    query = f"{song} {artist}" if artist else song
    speak(f"Searching YouTube for {query}")
    try:
        s = Search(query)
        video = s.results[0]
        webbrowser.open(video.watch_url)
        speak(f"Playing {video.title} on YouTube.")
    except Exception as e:
        speak("Sorry, I couldn't find that song on YouTube.")

# --- COMMAND PARSING ---
def parse_command(command):
    print(f"parse_command received: {command}")  # Debug print

    # Spotify play command
    if command.startswith("play "):
        # Try to extract "play [song] by [artist]"
        match = re.match(r"play (.+?) by (.+)", command)
        if match:
            song = match.group(1)
            artist = match.group(2)
            play_spotify_song(song, artist)
            return
        else:
            # Just "play [song]"
            song = command[5:]
            play_spotify_song(song)
            return

    # Spotify control commands
    if "pause" in command:
        spotify_control("pause")
        return
    if "resume" in command:
        spotify_control("resume")
        return
    if "next" in command:
        spotify_control("next")
        return
    if "previous" in command:
        spotify_control("previous")
        return
    if "stop" in command:
        spotify_control("stop")
        return

    # YouTube commands
    if "youtube" in command or "on youtube" in command or "find" in command:
        match = re.search(r"(play|find) (.+?)( by (.+))?( on youtube)?$", command)
        if match:
            song = match.group(2)
            artist = match.group(4)
            play_youtube_song(song, artist)
            return

    speak("Sorry, I didn't understand that command.")

def show_gif(gif_path):
    def animate(counter):
        frame = frames[counter]
        counter = (counter + 1) % frame_count
        label.configure(image=frame)
        root.after(50, animate, counter)  # Adjust speed as needed

    root = tk.Tk()
    root.title("Assistant Face")
    root.resizable(False, False)
    gif = Image.open(gif_path)
    desired_size = (400, 400)  # Change to your preferred width and height
    frames = [
        ImageTk.PhotoImage(frame.copy().convert('RGBA').resize(desired_size, Image.LANCZOS))
        for frame in ImageSequence.Iterator(gif)
    ]
    frame_count = len(frames)
    label = tk.Label(root)
    label.pack()
    animate(0)
    root.mainloop()

def start_gif_face():
    show_gif("assistant.gif")  # Replace with your GIF file name if different

# Start the GIF in a separate thread so it doesn't block your assistant
threading.Thread(target=start_gif_face, daemon=True).start()

# --- MAIN LOOP ---
def main():
    speak("Assistant is ready. Say your command.")
    while True:
        command = listen_for_command()
        if command:
            speak(f"You said: {command}. Executing now.")
            parse_command(command)
        time.sleep(1)

if __name__ == "__main__":
    main()