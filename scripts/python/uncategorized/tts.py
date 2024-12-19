import pyttsx3

voice_engine = pyttsx3.init("nsss")
voices = voice_engine.getProperty("voices")
voice_engine.setProperty("voice", voices[0].id)


def text_to_speech(text: str) -> None:
    voice_engine.say(text)
    voice_engine.runAndWait()


def main() -> None:
    while True:
        text = input("Type anything to tts: ")
        text_to_speech(text)


if __name__ == "__main__":
    main()
