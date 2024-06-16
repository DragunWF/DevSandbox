from time import sleep
import subprocess


def main() -> None:
    # Distracting programs to eliminate
    programs = ("spotify", "discord")  # Name of process in the 'ps' command
    INTERVAL = 60
    minutes_passed = 0

    while True:
        minutes_passed += 1
        if minutes_passed < 60:
            print(f"Time Passed: {minutes_passed} Minute(s)")
        else:
            print(f"Time Passed: {minutes_passed // 60} Hours(s) and {minutes_passed % 60} Minute(s)")

        for program in programs:
            command = f"ps {program} | kill"
            subprocess.run(["powershell", "-Command", command],
                           capture_output=True, text=True)

        sleep(INTERVAL)


if __name__ == "__main__":
    main()
