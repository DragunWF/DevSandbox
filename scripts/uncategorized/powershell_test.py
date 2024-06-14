import subprocess

# Define your PowerShell command
command = 'Get-Process'

# Execute the PowerShell command
result = subprocess.run(['powershell', '-Command', command],
                        capture_output=True, text=True)
subprocess.run(['powershell', '-Command', command],
               capture_output=True, text=True)

# Print the output of the command
print(result.stdout)
