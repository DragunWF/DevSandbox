from time import sleep
import subprocess

# Distracting programs to eliminate
programs = ("spotify", "discord")  # Name of process in the 'ps' command
INTERVAL = 60
iteration = 0

while True:
    iteration += 1
    print(f"Iteration: {iteration}")
    for program in programs:
        command = f"ps {program} | kill"
        subprocess.run(["powershell", "-Command", command],
                       capture_output=True, text=True)
    sleep(INTERVAL)
