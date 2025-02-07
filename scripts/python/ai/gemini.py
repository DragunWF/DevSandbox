import os
import google.generativeai as genai
from dotenv import load_dotenv

# Set up the API key
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)


def ask_gemini(prompt):
    """Send a prompt to Gemini API and return the response."""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text


# Example usage
if __name__ == "__main__":
    iterations = 1
    while True:
        prompt = input("Prompt: ")
        response = ask_gemini(prompt)
        print(f"Gemini's Response ({iterations}):\n", response)
        iterations += 1
