import subprocess
from time import sleep


def main():
    iterations = 0
    command = "powershell.exe ps spotify | kill"
    while True:
        iterations += 1
        subprocess.run(command)
        print(f"[Command Successfully Ran] ({iterations}): ps spotify | kill")
        sleep(15)


if __name__ == '__main__':
    main()
