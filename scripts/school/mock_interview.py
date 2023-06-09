import pyttsx3
from random import randint

voice_engine = pyttsx3.init("nsss")
voices = voice_engine.getProperty("voices")
voice_engine.setProperty("voice", voices[0].id)

questions = ["Tell me something about yourself",
             "How did you hear about this position?",
             "Why do you want to work here?",
             "Why did you decide to apply for this position?",
             "What is your greatest strength?",
             "What are your strengths and weaknesses?",
             "What do you know about this company/organization?",
             "Why should we hire you?",
             "What is your greatest accomplishment?",
             "What are your salary requirements?",
             "Do you have any questions for us?",
             "What are you looking for from a new position?",
             "Are you considering other positions in other companies?",
             "What is the professional achievement you're most proud of?",
             "What kind of working environment do you work best in?",
             "Where do you see yourself in 5 years?",
             "How do you deal with pressure or stressful situations?",
             "Do you think there is a difference between hard work and smart work?",
             "How quickly do you adapt to new technology?",
             "Do you have any interests outside of work?",
             "Do you think our company/organization could do better?"]
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
        print(f"Question {len(asked_questions)}: {question}")
        text_to_speech(question)
        input("Type anything after speaking your answer ")

    outro_text = "The interview has concluded!"
    print(outro_text)
    text_to_speech(outro_text)


if __name__ == '__main__':
    main()
