from rich import print
from ollama import chat
from ollama import ChatResponse


def main() -> None:
    response: ChatResponse = chat(model='llama3.2', messages=[
        {
            'role': 'user',
            'content': 'Why is the sky blue?',
        },
    ])

    print(response['message']['content'])

    # or access fields directly from the response object
    print(response.message.content)


if __name__ == '__main__':
    main()
