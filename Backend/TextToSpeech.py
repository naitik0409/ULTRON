import random# Import random for generating random choices
import asyncio# Import asyncio for asynchronous operations
import edge_tts# Import edge_tts for text-to-speech functionality
import os # Import os for file path handling
from dotenv import dotenv_values # Import dotenv for reading environment variables from a . env file
# Load environment variables from a . env file
env_vars = dotenv_values ( ".env" )
AssistantVoice = env_vars.get( "AssistantVoice")# Get the AssistantVoice from the environment variables
# Asynchronous function to convert text to an audio file
import subprocess

async def TextToAudioFile(text) -> None:
    file_path = r"Data\speech.mp3" # Define the path where the audio file will be saved

    if os.path.exists(file_path):# Check if the file already exists
        os.remove(file_path)# If it exists, remove it to avoid overwriting errors
    # Create the communicate object to generate speech
    communicate = edge_tts. Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(r'Data\speech.mp3' )# Save the generated speech as an MP3 file

async def TTS(Text, func=lambda r=None: True) :
    while True:
        try:
            # Convert text to an audio file asynchronously
            await TextToAudioFile(Text)
            file_path = r"Data\speech.mp3"

            # Verify that the audio file was created and is not empty
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                raise Exception("No audio was received. Please verify that your parameters are correct.")

            # Since pygame is disabled due to Python 3.14 compatibility issues,
            # just generate the audio file and let the web interface handle playback
            print(f"Generated speech audio file: {file_path}")
            print(f"Text to speak: {Text}")

            # Return immediately for real-time response
            return subprocess.Popen(["ffplay", "-autoexit", "-nodisp", file_path])
        except Exception as e: # Handle any exceptions during the process
            print(f"Error in TTS: {e}")

        finally:
            try:
                # Call the provided function with False to signal the end of TTS
                func(False)
                # No pygame cleanup needed since we're not using it
            except Exception as e: # Handle any exceptions during cleanup
                print(f"Error in finally block: {e}")
# Function to manage Text-to-Speech with additional responses for long text
async def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text) . split(". ")# Split the text by periods into a list of sentences

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]
# If the text is very long (more than 4 sentences and 250 characters), add a response message
    if len(Data) > 4 and len(Text) >= 250:
        await TTS(" ". join(Text. split(".") [0:2]) + ". " + random. choice(responses), func)
# Otherwise, just play the whole text
    else:
        await TTS(Text, func)
# Main execution loop
if __name__ == "__main__":
    while True:
        # Prompt user for input and pass it to TextToSpeech function
        asyncio.run(TextToSpeech(input("Enter the text: ")))