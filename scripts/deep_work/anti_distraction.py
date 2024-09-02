from time import sleep
import subprocess


def main() -> None:
    # Distracting programs to eliminate
    # Name of process within the output of the 'ps' command
    programs = ("spotify", "discord", "steam")
    INTERVAL = 60
    minutes_passed = 0

    while True:
        if minutes_passed == 0:
            print("Anti-Distraction has now begun. Have a good deep work session!")

        if minutes_passed < 60:
            print(f"Time Passed: {minutes_passed} Minute(s)")
        else:
            log = f"Time Passed: {minutes_passed // 60} Hours(s)"
            if minutes_passed % 60 != 0:
                log += f" and {minutes_passed % 60} Minute(s)"
            print(log)

        for program in programs:
            command = f"ps {program} | kill"
            subprocess.run(["powershell", "-Command", command],
                           capture_output=True, text=True)

        sleep(INTERVAL)
        minutes_passed += 1


if __name__ == "__main__":
    main()
