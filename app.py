from flask import Flask, render_template, jsonify, request
import speech_recognition as sr
from openai import OpenAI
import os
from pathlib import Path
from playsound import playsound
import threading
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Your Flask application code goes here


app = Flask(__name__)

client = OpenAI(api_key= os.environ['openai_api_key'])
print(os.environ['openai_api_key'])


@app.route('/')
def index():
    # Render an HTML page with a button
    return render_template('index.html')


@app.route('/listen', methods=['POST'])
def listen():
    # Initialize the recognizer
    r = sr.Recognizer()
    r.energy_threshold = 4000
    r.dynamic_energy_threshold = True
    r.dynamic_energy_adjustment_damping = 0.15
    r.dynamic_energy_ratio = 1.5
    with sr.Microphone(device_index=None) as source:
        print("Listening...")


        try:
            audio = r.listen(source,timeout=2)
            print("Listening Completed....")
            # Recognize speech using Google's speech recognition
            transcripted = r.recognize_google(audio)
            print("Transcription Completed")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful  assistant of Rehan Ai. who help everyone with their queries and give the right answer "},
                    {"role": "user", "content": "Who are you?"},
                    {"role": "assistant", "content": "As an AI language model, I am programmed to assist you with your queries and concer to the best of my abilities"},
                    {"role": "user", "content": "Where was it?"},
                    {"role": "user", "content": f"this is the transcripted text: {transcripted}"}

                ]
            )
            print(response.choices[0].message.content)

            speech_file_path = Path(__file__).parent / "output.mp3"
            res = client.audio.speech.create(
                model="tts-1",
                voice="echo",
                input=response.choices[0].message.content
            )
            res.stream_to_file(speech_file_path)
            audio_file = open("./output.mp3", "rb")
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

            transcript_output = transcript.text

            # Construct the JSON response
            response_data = {'transcripted': transcripted, 'transcript_output': transcript_output}

            # Start a separate thread to play the sound
            threading.Thread(target=playsound, args=(speech_file_path,)).start()

            return jsonify(response_data)

        except sr.WaitTimeoutError:
            return jsonify({'transcripted': 'No speech detected within the timeout period.'})
        except sr.UnknownValueError:
            return jsonify({'transcripted': 'Could not understand audio'})
        except sr.RequestError as e:
            return jsonify({'transcripted': f'Request to Google API failed: {e}'})
        except Exception as e:
            return jsonify({'transcripted': f'An unexpected error occurred: {e}'})


if __name__ == '__main__':
    app.run(debug=True)
