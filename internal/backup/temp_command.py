import subprocess, threading
from wakeonlan import send_magic_packet
from pywol import wake as wake_round_two
from internal import picklefunc
exclude = []
pcs_mac = picklefunc.load_obj("MAC_Table")  # load MACs
with open('C:/Progs/RunScripts/internal/exclude.txt', 'r') as pre_exclude:
    try:
        for excluding in pre_exclude:
            if excluding == "":
                pass
            else:
                exclude.append(int(excluding.strip()))
    except Exception as err_to_read:
        pass


class MyThread(threading.Thread):
    def run(self):
        task(name)


def task(name):
    try:
        send_magic_packet(pcs_mac.get(name))
    except Exception as err_magic:
        pass
    try:
        wake_round_two(pcs_mac.get(name).replace(':', '-'))
    except Exception as err_magic:
        pass
    # subprocess.run(
    #     f'SCHTASKS /Run /S {name} /TN Sleep')
    # print(f'Try to change scheme: {name}')
    # subprocess.Popen(
    #     f"psexec \\\{name} REG ADD HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\238C9FA8-0AAD-41ED-83F4-97BE242C8F20\\7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 /v Attributes /t REG_DWORD /d 2 /f",)
    # subprocess.Popen(
    #     f"psexec \\\{name} powercfg /SETACVALUEINDEX SCHEME_CURRENT 238C9FA8-0AAD-41ED-83F4-97BE242C8F20 7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 0")
    # try:
    #     subprocess.run(f'SCHTASKS /Delete /S {name} /TN Sleep /F', stdout=subprocess.PIPE)
    # except:
    #     pass


pcs = []
i = 10
while i < 367:  # Create PCs list
    if i in exclude:
        if i < 10:
            pass
        elif i < 100 or i == 10:
            pc_name = f"ws-tmb-a00{i}"
            pcs.append(pc_name)
        else:
            pc_name = f"ws-tmb-a0{i}"
            pcs.append(pc_name)
        i += 1
        # pass
    else:
        if i < 10:
            pass
        elif i < 100 or i == 10:
            pc_name = f"ws-tmb-a00{i}"
            pcs.append(pc_name)
        else:
            pc_name = f"ws-tmb-a0{i}"
            pcs.append(pc_name)
        i += 1
        # pass

# i = 261
# while i < 262:  # Create PCs list
#     if i in exclude:
#         if i < 10:
#             pass
#         elif i < 100 or i == 10:
#             pc_name = f"ws-tmb-a00{i}"
#             pcs.append(pc_name)
#         else:
#             pc_name = f"ws-tmb-a0{i}"
#             pcs.append(pc_name)
#         i += 1
#         pass
#     else:
#         i += 1
#         pass

for name in pcs:
    print(name)
    t = MyThread()
    t.start()
