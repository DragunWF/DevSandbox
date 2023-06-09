import pyttsx3
from random import randint

voice_engine = pyttsx3.init("sapi5")
voices = voice_engine.getProperty("voices")
voice_engine.setProperty("voice", voices[0].id)

questions = ["Are you gae", "wanna have sex?"]
asked_questions = []


def text_to_speech(text: str):
    voice_engine.say(text)
    voice_engine.runAndWait()


def choose_random_question():
    random_index = randint(0, len(questions) - 1)
    chosen_question = questions[random_index]
    questions.pop(random_index)
    asked_questions.append(chosen_question)
    return chosen_question


def main():
    print("Welcome to the interview program!")
    while len(questions) > 0:
        question = choose_random_question()
        text_to_speech(question)
        input("Type anything after speaking your answer ")
    text_to_speech("The interview has concluded!")


if __name__ == '__main__':
    main()
