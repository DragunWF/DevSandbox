import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Replace with your form ID
FORM_ID = '16Pd3L5KSdNawJgJGqG9mfqnZIT7AREdKDoE71RUYiPQ'

# Minimal scope needed for read-only access to form questions
SCOPES = ['https://www.googleapis.com/auth/forms.body.readonly']


def get_form_questions(form_id):
    """Retrieves and prints the questions from a Google Form."""
    creds = None

    # Important: Delete the existing token.json file to force re-authentication with new scopes
    if os.path.exists('token.json'):
        os.remove('token.json')
        print("Removed old token.json to refresh authentication with correct scopes")

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)  # Make sure this points to your OAuth client credentials
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('forms', 'v1', credentials=creds)

        print(f"Attempting to fetch form with ID: {form_id}")
        # Retrieve the form
        form = service.forms().get(formId=form_id).execute()
        print(
            f"Form Title: {form.get('info', {}).get('title', 'Untitled Form')}\n")

        # Check if the form has items
        if 'items' not in form:
            print('No items found in the form.')
            return

        print("Questions:")
        for item in form['items']:
            print(item)
            if 'questionItem' in item:
                question_item = item['questionItem']
                question = question_item.get('question', {})

                print(f"- {item.get('title', 'Untitled Question')}")
                print(f"  Type: {question.get('questionType', 'Unknown')}")

                # Handle different question types
                if 'choiceQuestion' in question:
                    options = [option.get('value', '')
                               for option in question['choiceQuestion'].get('options', [])]
                    print(f"  Options: {', '.join(options)}")

                # Print required status if available
                if 'required' in question_item:
                    print(f"  Required: {question_item['required']}")

                print()

    except HttpError as error:
        print(f'An error occurred: {error}')
        print(
            f'Error details: {error.reason if hasattr(error, "reason") else "Unknown error"}')


if __name__ == '__main__':
    get_form_questions(FORM_ID)
