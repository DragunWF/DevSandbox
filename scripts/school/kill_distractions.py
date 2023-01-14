import subprocess
from time import sleep


def main():
    distraction_processes = ("spotify", "discord")
    iterations = 0
    while True:
        iterations += 1
        for process in distraction_processes:
            command = f"powershell.exe ps {process} | kill"
            subprocess.run(command)
        print(f"[Command Successfully Ran]: Iteration: {iterations}")
        sleep(15)


if __name__ == '__main__':
    main()
