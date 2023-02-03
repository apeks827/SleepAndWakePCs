import logging, sys, subprocess
import threading
import time

from internal import picklefunc
from getmac import get_mac_address

subprocess.run('ipconfig /flushdns', shell=True)  # clear cache

pcs_mac = picklefunc.load_obj("MAC_Table")

file_log = logging.FileHandler('C:/Progs/RunScripts/logs/mac_update.log')
# file_log.setLevel(logging.INFO)
console_out = logging.StreamHandler(sys.stdout)

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S', level=logging.INFO)


def logging_info(text):
    logging.info(text)


pcs_count = 0
with open('C:/Progs/RunScripts/internal/pcs_count.txt', 'r') as pre_count:
    try:
        pcs_count = int(pre_count.readline().strip().replace(' ', ''))
        pcs_count += 1
    except Exception as err_to_read:
        logging.error(f'Got err when read pcs_count.txt, err: {err_to_read}')

err_get_mac = []
true_offline = []


def mac_update(name):  # get MAC
    try:
        if name in pcs_mac:
            pass
        else:
            for_update = {name: None}
            pcs_mac.update(for_update)
    except Exception as err_to_add_PC:
        logging.error(f"Fail to add new PC {err_to_add_PC}")
    try:
        new_mac = get_mac_address(hostname=name)
        if new_mac is None:
            print(f"got None MAC for {name}")
            true_offline.append(name)
            pass
        else:
            if new_mac == pcs_mac.get(name):
                pass
            else:
                logging_info(f'Found new MAC for {name}')
                logging_info(f"Old: {pcs_mac.get(name)}")
                logging_info(f"new MAC is: {new_mac}")
                to_update = {name: new_mac}
                pcs_mac.update(to_update)
                logging_info(f"MAC updated to: {pcs_mac.get(name)}")
                logging_info('------------------------------------------------------')
    except Exception as err_get:
        print(f"err get mac: {name} {err_get}")
        err_get_mac.append(name)


def main_cycle(i):
    if i < 10:
        pc_name = f"ws-tmb-a000{i}"
        mac_update(pc_name)
        i += 1
    elif i < 100 or i == 10:
        pc_name = f"ws-tmb-a00{i}"
        mac_update(pc_name)
        i += 1
    else:
        pc_name = f"ws-tmb-a0{i}"
        mac_update(pc_name)
        i += 1


class MyThread(threading.Thread):
    def run(self):
        main_cycle(i)


i = 1
while i < pcs_count:  # Create PCs list
    t = MyThread()
    t.start()
    i += 1

logging_info('Wait response from threads')
time.sleep(30)

logging_info('------------------------------------------------------')
logging_info(f'Get addr error. SUM is {len(err_get_mac)} PCs: {err_get_mac}')
logging_info(f'True offline. SUM is {len(true_offline)} PCs: {true_offline}')
logging_info('------------------------------------------------------')

picklefunc.save_obj(pcs_mac, "MAC_Table")  # Save MAC list
logging_info('Sequence complete')
