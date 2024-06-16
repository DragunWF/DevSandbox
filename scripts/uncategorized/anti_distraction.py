from time import sleep
import subprocess


def main() -> None:
    # Distracting programs to eliminate
    programs = ("spotify", "discord")  # Name of process in the 'ps' command
    INTERVAL = 60
    minutes_passed = 0

    while True:
        minutes_passed += 1
        minutes_str = f"{minutes_passed} Minute(s)"
        if minutes_passed < 60:
            print(f"Time Passed: {minutes_str}")
        else:
            print(f"Time Passed: {minutes_passed // 60} Hours(s) and {minutes_str}")

        for program in programs:
            command = f"ps {program} | kill"
            subprocess.run(["powershell", "-Command", command],
                           capture_output=True, text=True)

        sleep(INTERVAL)


if __name__ == "__main__":
    main()
