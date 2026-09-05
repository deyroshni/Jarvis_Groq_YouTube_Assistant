import os
import webbrowser
import pyttsx3
import speech_recognition as sr
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ==========================
# OOP EXAMPLE: CLASS = BLUEPRINT, OBJECT = INSTANCE
# ==========================

class VoiceAssistant:
    """ all voice-related behavior is grouped in one class."""

    def __init__(self, name):
        self.name = name
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def speak(self, text):
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                command = self.recognizer.recognize_google(audio)
                print("You:", command)
                return command.lower()

            except sr.UnknownValueError:
                print("Sorry, I didn't understand.")
                return ""

            except sr.WaitTimeoutError:
                return ""

            except Exception as e:
                print("Error:", e)
                return ""


class MusicPlayer:
    """This class handles all music-related tasks."""

    def __init__(self, assistant):
        self.assistant = assistant

    def play(self, song):
        try:
            if not song.strip():
                self.assistant.speak("Please tell me the song name.")
                return

            self.assistant.speak(f"Playing {song}")

            with YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
                result = ydl.extract_info(f"ytsearch1:{song}", download=False)
                entries = result.get("entries", [])

                if not entries:
                    self.assistant.speak("Song not found.")
                    return

                video = entries[0]
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                print("Opening:", video_url)
                webbrowser.open(video_url)
                self.assistant.speak(f"Now playing {song}")

        except Exception as e:
            print("ERROR:", e)
            self.assistant.speak("Unable to play song.")


class JarvisAssistant(VoiceAssistant):
    """Inheritance: JarvisAssistant fetches the voice features of VoiceAssistant."""

    def __init__(self, name):
        super().__init__(name)
        self.music_player = MusicPlayer(self)

    def normalize_song_name(self, command):
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract and correct the song name from the user's request. Return only the song name."
                    },
                    {"role": "user", "content": command}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()

        except Exception:
            return command.replace("play", "", 1).strip()

    def chat_with_jarvis(self, command):
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Jarvis. Keep answers short and helpful."},
                    {"role": "user", "content": command}
                ]
            )
            answer = response.choices[0].message.content
            self.speak(answer)

        except Exception as e:
            self.speak(f"Connection error. {e}")

    def handle_command(self, command):
        if command in ["hi", "hello", "hey"]:
            self.speak("Hello Roshni. How can I help you?")

        elif command in ["bye", "exit", "quit"]:
            self.speak("Goodbye Roshni. Have a wonderful day.")
            return False

        elif "play" in command:
            song = command.replace("play", "", 1).strip()

            if not song:
                self.speak("Please tell me which song you want to play.")
                return True

            clean_song = self.normalize_song_name(song)
            self.music_player.play(clean_song)
            return True

        else:
            self.chat_with_jarvis(command)
            return True


# ==========================
# MAIN PROGRAM
# ==========================

if __name__ == "__main__":
    assistant = JarvisAssistant("Jarvis")
    assistant.speak("Hi, I am Jarvis. Which song would you like to listen to today?")

    while True:
        cmd = assistant.listen()

        if not cmd:
            continue

        should_continue = assistant.handle_command(cmd)

        if not should_continue:
            break