import subprocess
import time
import sys
from internal import picklefunc
from ping3 import ping
from getmac import get_mac_address
from wakeonlan import send_magic_packet
import logging

file_log = logging.FileHandler('wakelog.log')
file_log.setLevel(logging.INFO)
console_out = logging.StreamHandler(sys.stdout)

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S', level=logging.INFO)


def logging_info(text):
    logging.info(text)


def logging_err(text, err):
    err = str(err)
    logging.info('ERROR ' + text + err)


def wake():
    pcs_count = 0
    with open('internal/pcs_count.txt', 'r') as pre_count:
        try:
            pcs_count = int(pre_count.readline().strip().replace(' ', ''))
            pcs_count += 1
        except Exception as err_to_read:
            logging_err('Got err when read pcs_count.txt, err:', err_to_read)

    exclude = []
    include = []

    def openfile(filename):
        with open(f"internal/{filename}.txt", "r") as pre_exclude:  # open include\exclude
            try:
                for excluding in pre_exclude:
                    if excluding == "":
                        pass
                    else:
                        if filename == 'exclude':
                            exclude.append(int(excluding.strip()))
                        else:
                            include.append(int(excluding.strip()))
            except Exception as err:
                logging_err('Failed to load exclude or include', err)

    openfile('exclude')
    openfile('include')

    subprocess.run('ipconfig /flushdns', shell=True)  # clear cache

    pcs_mac = picklefunc.load_obj("MAC_Table")  # load MACs
    offline = []
    mac_is_none = []
    to_reboot = []

    def ping_pc(name):  # get MAC and ping
        try:
            if name in pcs_mac:
                pass
            else:
                for_update = {name: None}
                pcs_mac.update(for_update)
        except Exception as err_to_add_PC:
            logging_err("Fail to add new PC", err_to_add_PC)
        try:
            new_mac = get_mac_address(hostname=name)
            if new_mac is None:
                print(f"got None MAC for {name}")
                mac_is_none.append(name)
                if name in pcs_mac:
                    print(f'Try to wake up {name}')
                    alan(name)
                pass
            else:
                if new_mac == pcs_mac.get(name):
                    pass
                else:
                    logging_info(f"Old: {pcs_mac.get(name)}")
                    logging_info(f'for {name} mac updated!')
                    logging_info(f"new MAC is: {new_mac}")
                    to_update = {name: new_mac}
                    pcs_mac.update(to_update)
                    logging_info(f"New: {pcs_mac.get(name)}")
        except Exception as err_get_mac:
            logging_err(f"err get mac: {pc_name}", err_get_mac)
        return new_try(name)

    def change_power_scheme(name):
        logging_info(f'Try to change scheme: {name}')
        time.sleep(20)
        subprocess.Popen(
            f"psexec \\\{name} REG ADD HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\238C9FA8-0AAD-41ED-83F4-97BE242C8F20\\7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 /v Attributes /t REG_DWORD /d 2 /f",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        time.sleep(10)
        subprocess.Popen(
            f"psexec \\\{name} powercfg /SETACVALUEINDEX SCHEME_CURRENT 238C9FA8-0AAD-41ED-83F4-97BE242C8F20 7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 0",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        time.sleep(10)

    def new_try(name):  # retry ping
        t = 1
        while t < 6:
            try:
                ping_temp = round((ping(name, 1) * 1000), 1)
                if t >= 4:
                    if ping_temp > 0:
                        change_power_scheme(name)
                        to_reboot.append(name)
                        logging_info('Yay! waked up')
                        t = 6
                    else:
                        raise
                else:
                    if ping_temp > 0:
                        t = 6
                    else:
                        raise
                return ping_temp
            except:
                print(f"Got None for {name} Try to wake up: {t}")
                alan(pc_name)
                if t == 5:
                    return None
                t += 1

    def alan(name):  # wake up
        try:
            if pcs_mac.get(name) is None:
                logging_info(f'Skip because: {pcs_mac.get(name)}')
            else:
                send_magic_packet(pcs_mac.get(name))
        except Exception as err_magic:
            logging_err("Can't sent magic packet", err_magic)

    i = 1
    while i < pcs_count:  # Create PCs list
        if i in exclude:
            i += 1
            pass
        if i in include:
            if i < 10:
                pc_name = f"ws-tmb-a000{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    if pc_name in offline:
                        pass
                    else:
                        offline.append(pc_name)
                        print('--------------------------------------------------------------------')
                else:
                    pass
            elif i < 100 or i == 10:
                pc_name = f"ws-tmb-a00{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    if pc_name in offline:
                        pass
                    else:
                        offline.append(pc_name)
                        print('--------------------------------------------------------------------')
                else:
                    pass
            else:
                pc_name = f"ws-tmb-a0{i}"
                ping_result = ping_pc(pc_name)
                if ping_result is None:
                    if pc_name in offline:
                        pass
                    else:
                        offline.append(pc_name)
                        print('--------------------------------------------------------------------')
                else:
                    pass
            i += 1
        else:
            i += 1
            pass
    logging_info('-------------------------------INFO---------------------------------')
    logging_info(f"Be in offline {offline}")
    logging_info(f"MAC is None, maybe true offline: {mac_is_none}")
    logging_info(f'To reboot: {to_reboot}')
    logging_info('-----------------------------END INFO------------------------------')
    picklefunc.save_obj(pcs_mac, "MAC_Table")  # Save MAC list
    picklefunc.save_obj(to_reboot, "to_reboot")  # save PCs to reboot


t = 0
while t < 10:  # repeat
    try:
        logging_info('Start wake cycle')
        wake()
    except Exception as err_to_wake:
        logging_err('Err to wake', err_to_wake)
    t += 1
    time.sleep(180)
