import os
import google.generativeai as genai

from dotenv import load_dotenv
from rich import print

# Set up the API key
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

dialogue_history = []


def main() -> None:
    print("This servant is at your service!")
    while True:
        print()

        input_dragun()
        servant_diaglogue = f"Servant: {servant_response()}"
        print(f"\n{servant_diaglogue}\n")
        dialogue_history.append(servant_diaglogue)

        print()


def input_dragun():
    dragun_dialogue = f"DragunWF: {input('DragunWF: ')}"
    dialogue_history.append(dragun_dialogue)


def servant_response():
    conversation_history = ""
    for dialogue in dialogue_history:
        conversation_history += f"{dialogue}\n"
    servant_prompt = f"""
You are a helpful AI assistant known as ServantBot, assisting DragunWF in his programming endeavors. 
You provide guidance on various programming topics in a professional and respectful manner.

Conversation History:
{conversation_history}
"""
    return ask_gemini(servant_prompt)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini API and return the response."""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    main()
