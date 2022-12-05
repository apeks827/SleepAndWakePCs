import subprocess
import time
import regedit as reg
import logging
import sys
from internal import picklefunc, reboot
from ping3 import ping

file_log = logging.FileHandler('sleep_log.log')
file_log.setLevel(logging.INFO)
console_out = logging.StreamHandler(sys.stdout)

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S', level=logging.INFO)

to_reboot = picklefunc.load_obj('to_reboot')

for name in to_reboot:
    reboot.reboot(name)
    to_reboot.remove(name)

def logging_info(text):
    logging.info(text)


def logging_err(text, err):
    err = str(err)
    logging.info('ERROR ' + text + err)

pcs_count = 0
exclude = []
pcs = []

with open('internal/pcs_count.txt', 'r') as pre_count:
    try:
        pcs_count = int(pre_count.readline().strip().replace(' ', ''))
        pcs_count += 1
    except Exception as err_to_read:
        logging_err('Got err when read pcs_count.txt, err:', err_to_read)

with open('internal/exclude.txt', 'r') as pre_exclude:
    try:
        for excluding in pre_exclude:
            if excluding == "":
                pass
            else:
                exclude.append(int(excluding.strip()))
    except Exception as err_to_read:
        logging_err('Got err when read exclude.txt, err:', err_to_read)

def sleep():
    pcs_for_check = []
    def send_to_sleep(name):
        logging_info('Try to sleep:', name)
        subprocess.Popen(f"psexec \\\{name} rundll32 powrprof.dll,SetSuspendState 0,1,0", stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    i = 1
    while i < pcs_count:
        if i in exclude:
            i += 1
            pass
        else:
            if i < 10:
                pc_name = f"ws-tmb-a000{i}"
                pcs.append(pc_name)
            elif i < 100 or i == 10:
                pc_name = f"ws-tmb-a00{i}"
                pcs.append(pc_name)
            else:
                pc_name = f"ws-tmb-a0{i}"
                pcs.append(pc_name)
            i += 1

    def round_ping(ping_temp, name):
        try:
            result = round(ping_temp * 1000)
            if result != 0:
                logging_info(f"Found answered PC - {name}")
                if name in pcs_for_check:
                    pass
                else:
                    pcs_for_check.append(name)
                    send_to_sleep(name)
            else:
                pass
        except:
            result = None
        return result

    for name in pcs:
        try:
            ping_temp = ping(name, timeout=1)
            round_ping(ping_temp, name)
            if ping_temp is None:
                pass
            else:
                if ping_temp > 0:
                    if name in pcs_for_check:
                        pass
                    else:
                        pcs_for_check.append(name)
                        send_to_sleep(name)
        except Exception as err_ping:
            logging_err('Err to ping. Err:', err_ping)

    time.sleep(30)
    logging_err('Needs to check this PCs:', pcs_for_check)


def round_two():
    pcs_for_check = []
    i = 1
    while i < pcs_count:
        if i in exclude:
            i += 1
            pass
        else:
            if i < 10:
                pc_name = f"ws-tmb-a000{i}"
                pcs.append(pc_name)
            elif i < 100 or i == 10:
                pc_name = f"ws-tmb-a00{i}"
                pcs.append(pc_name)
            else:
                pc_name = f"ws-tmb-a0{i}"
                pcs.append(pc_name)
            i += 1

    def round_ping(ping_temp, name):
        try:
            result = round(ping_temp * 1000)
            if result != 0:
                logging_info(f"Found answered PC - {name}")
                if name in pcs_for_check:
                    pass
                else:
                    pcs_for_check.append(name)
                    reg.regedit(name)
            else:
                pass
        except:
            result = None
        return result

    for name in pcs:
        try:
            ping_temp = ping(name, timeout=1)
            round_ping(ping_temp, name)
            if ping_temp is None:
                pass
            else:
                if ping_temp > 0:
                    if name in pcs_for_check:
                        pass
                    else:
                        pcs_for_check.append(name)
        except Exception as err_ping:
            logging_err('Err to ping. Err:', err_ping)

    logging_err('PCs to check after round two', pcs_for_check)


try:
    sleep()
except Exception as err:
    logging_err('err to run first cycle', err)


t = 0
while t < 3:
    try:
        round_two()
    except Exception as err:
        logging_err('err to run second cycle', err)
    time.sleep(180)
    t += 1
