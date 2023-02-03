import subprocess
import time as t


def reboot(name):
    subprocess.Popen(f"shutdown /r /f /t 0 /m \\\{name}")
    t.sleep(1)


def del_task(name):
    try:
        subprocess.run(f'SCHTASKS /Delete /S {name} /TN Sleep /F', stdout=subprocess.PIPE)
    except:
        pass


def run_task(name):
    subprocess.run(
        f'SCHTASKS /Run /S {name} /TN Sleep')


def create_wake_task(name):
    subprocess.run(
        f'SCHTASKS /Create /S {name} /TN Wake /XML "C:\Progs\RunScripts\internal\Wake.xml" /F')


def create_task(name):
    subprocess.run(
        f'SCHTASKS /Create /S {name} /RU "SYSTEM" /SC DAILY /TN Sleep /TR "rundll32.exe powrprof.dll,SetSuspendState 0,1,0" /ST 23:05 /RL HIGHEST /F')
