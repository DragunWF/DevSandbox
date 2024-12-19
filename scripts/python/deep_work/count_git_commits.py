import requests
import datetime

import os
from dotenv import load_dotenv


def get_dates():
    """Get the current date and the date one week ago in ISO 8601 format."""
    now = datetime.datetime.now()
    one_week_ago = now - datetime.timedelta(days=7)
    return now.isoformat(), one_week_ago.isoformat()


def fetch_events(username, token):
    """Fetch events for a GitHub user."""
    url = f"https://api.github.com/users/{username}/events"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve events: {response.status_code}")
    return response.json()


def count_weekly_commits(events, one_week_ago_iso, now_iso):
    """Count the number of commits from the last week."""
    one_week_ago = datetime.datetime.fromisoformat(one_week_ago_iso)
    now = datetime.datetime.fromisoformat(now_iso)
    commit_count = 0
    for event in events:
        if event["type"] == "PushEvent":
            event_date = datetime.datetime.strptime(
                event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if one_week_ago <= event_date <= now:
                commit_count += len(event["payload"]["commits"])
    return commit_count


def main(username, token):
    """Main function to count commits from the last week for a given GitHub user."""
    now_iso, one_week_ago_iso = get_dates()
    events = fetch_events(username, token)
    commit_count = count_weekly_commits(events, one_week_ago_iso, now_iso)
    print(f"Total commits by {username} in the last week: {commit_count}")


if __name__ == "__main__":
    load_dotenv()
    username = "DragunWF"
    # Generate a GitHub token from https://github.com/settings/tokens
    token = os.environ.get("GITHUB_API_TOKEN")
    main(username, token)
