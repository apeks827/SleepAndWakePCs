import subprocess
import time as t


def reboot(name):
    subprocess.Popen(f"shutdown /r /f /t 0 /m \\\{name}")
    t.sleep(1)
