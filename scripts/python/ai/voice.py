from kokoro import KPipeline
import sounddevice as sd
import numpy as np

# 'a' = American English, 'f' = Female
pipeline = KPipeline(lang_code='a')


def speak(text):
    # 'af_bella' is a youthful, clear female voice
    # 'speed=1.1' makes it sound more energetic/cute
    generator = pipeline(text, voice='af_bella', speed=1.1)

    print(f"Miku says: {text}")
    for i, (gs, ps, audio) in enumerate(generator):
        sd.play(audio, 24000)
        sd.wait()


# Test it
my_string = "I love you. I love you so much!"
speak(my_string)
