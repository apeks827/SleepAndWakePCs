import logging
import subprocess
import sys
import threading
import time
from getmac import get_mac_address
from tqdm import tqdm
from ping3 import ping

file_log = logging.FileHandler('C:/Progs/RunScripts/logs/WakeAnalyze.log')
console_out = logging.StreamHandler(sys.stdout)

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S', level=logging.INFO)


def logging_info(text):
    logging.info(text)


def logging_err(text, err):
    err = str(err)
    logging.error(f'{text} {err}')


def wake():
    pcs_count = 0
    with open('C:/Progs/RunScripts/internal/pcs_count.txt', 'r') as pre_count:
        try:
            pcs_count = int(pre_count.readline().strip().replace(' ', ''))
            pcs_count += 1
        except Exception as err_to_read:
            logging_err('Got err when read pcs_count.txt, err:', err_to_read)

    exclude = []
    with open("C:/Progs/RunScripts/internal/exclude.txt", "r") as pre_exclude:  # open exclude
        try:
            for excluding in pre_exclude:
                if excluding == "":
                    pass
                else:
                    exclude.append(int(excluding.strip()))
        except Exception as err:
            logging_err('Failed to load exclude', err)

    subprocess.run('ipconfig /flushdns', shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)  # clear cache

    offline = []
    mac_is_none = []
    online = []

    def ping_pc(name):
        try:
            new_mac = get_mac_address(hostname=name)
            if new_mac is None:
                mac_is_none.append(name)
            else:
                pass
        except:
            mac_is_none.append(name)

        t = 1
        while t < 6:
            try:
                ping_temp = round((ping(name, 4) * 1000), 1)
                if t >= 4:
                    if ping_temp > 0:
                        t = 6
                    else:
                        raise
                else:
                    if ping_temp > 0:
                        t = 6
                    else:
                        raise
                time.sleep(5)
                return ping_temp
            except Exception as err:
                # print(f'err {err}')
                if t == 5:
                    return None
                time.sleep(5)
                t += 1

    def main_cycle(i):
        try:
            if i < 10:
                pc_name = f"ws-tmb-a000{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    offline.append(pc_name)
                else:
                    online.append(pc_name)
            elif i < 100 or i == 10:
                pc_name = f"ws-tmb-a00{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    offline.append(pc_name)
                else:
                    online.append(pc_name)
            else:
                pc_name = f"ws-tmb-a0{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    offline.append(pc_name)
                else:
                    online.append(pc_name)
        except Exception as err:
            print(f'err {err}')

    class MyThread(threading.Thread):
        def run(self):
            main_cycle(i)

    pcs = []
    i = 1
    while i < pcs_count:  # Create PCs list
        pcs.append(i)
        i += 1
    for i in tqdm(pcs):
        t = MyThread()
        t.start()
    print('Wait answer from sequence')
    time.sleep(30)
    logging_info('-------------------------------INFO---------------------------------')
    logging_info(f"Be in online {len(online)} PCs: {online}")
    logging_info(f"Be in offline {len(offline)} PCs: {offline}")
    logging_info(f"MAC is None, maybe true offline {len(mac_is_none)} PCs: {mac_is_none}")
    logging_info('-----------------------------END INFO------------------------------')


while True:  # repeat
    try:
        wake()
    except Exception as err_to_wake:
        logging_err('Err to wake', err_to_wake)
    time.sleep(1800)
