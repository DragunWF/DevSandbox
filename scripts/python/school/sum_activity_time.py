from rich import print


def sum_online_activities():
    social_media = [30, 30, 90]
    browsing = [60, 15]
    video_games = [180, 60, 119]
    other = [90]
    studying = [120]
    print(f"Social Media: {sum(social_media)}")
    print(f"Browsing: {sum(browsing)}")
    print(f"Video Games: {sum(video_games)}")
    print(f"Studying: {sum(studying)}")
    print(f"Other: {sum(other)}")


def sum_offline_activities():
    other = [120, 90, 60]
    academics = [120, 120, 180]
    research = [75, 60]
    meditation = [15]
    print(f"Other: {sum(other)}")
    print(f"Academics: {sum(academics)}")
    print(f"Research: {sum(research)}")
    print(f"Meditation: {sum(meditation)}")


def main():
    print("Online:")
    sum_online_activities()
    print("\nOffline")
    sum_offline_activities()


if __name__ == "__main__":
    main()
