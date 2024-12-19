from time import sleep


def progress(process_name: str, iterations: int):
    interval = 0.25
    for i in range(1, iterations + 1):
        print(f"{process_name}... (%{i})")
        sleep(interval)


def main():
    default_iterations = 100
    processes = ("Hacking computer", "Stealing personal info",
                 "Bypassing anti-virus")
    for process in processes:
        progress(process, default_iterations)
    print("\nHacking completed successfully\n")


# This is just for trolling and entertainment purposes
main()
