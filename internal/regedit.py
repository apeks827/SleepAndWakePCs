import logging
import winreg
import subprocess

exclude = [1, 2, 3, 4, 5, 6, 7, 8, 9]

subprocess.run('ipconfig /flushdns', shell=True)


def regedit(name):
    try:
        root = winreg.ConnectRegistry(name, winreg.HKEY_LOCAL_MACHINE)
        with winreg.OpenKey(root,
                            r"SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}") as folders:
            for idx in range(winreg.QueryInfoKey(folders)[0]):
                try:
                    with winreg.OpenKeyEx(folders, winreg.EnumKey(folders, idx)) as folders_info:
                        exclude_adapters = ['WAN Miniport (IKEv2)', 'WAN Miniport (L2TP)', 'WAN Miniport (PPTP)',
                                            'WAN Miniport (PPPOE)', 'WAN Miniport (IP)', 'WAN Miniport (IPv6)',
                                            'Microsoft Kernel Debug Network Adapter',
                                            'WAN Miniport (Network Monitor)',
                                            'ThinkPad Hybrid USB-C and USB-A Dock', 'RAS Async Adapter',
                                                                                    'Wintun Userspace Tunnel',
                                            'TAP-Windows Adapter V9', 'WAN Miniport (SSTP)',
                                            'Microsoft Wi-Fi Direct Virtual Adapter',
                                            'Bluetooth Device (Personal Area Network)',
                                            'Intel(R) Wi-Fi 6 AX201 160MHz', 'Intel(R) Dual Band Wireless-AC',
                                            'Cisco AnyConnect Secure Mobility Client Virtual Miniport Adapter for '
                                            'Windows x64',
                                            'Qualcomm QCA9377 802.11ac Wireless Adapter',
                                            'Intel(R) Dual Band Wireless-AC 8265',
                                            'Intel(R) Dual Band Wireless-AC 3165', 'Lenovo USB Ethernet',
                                            'Intel(R) Dual Band Wireless-AC 3168',
                                            'D-Link DGE-528T Gigabit Ethernet Adapter',
                                            'Microsoft ISATAP Adapter']

                        def get_value(key):
                            return winreg.QueryValueEx(folders_info, key)[0]

                        if get_value("DriverDesc") in exclude_adapters:
                            pass
                        else:
                            if 'Realtek PCIe' or 'Intel(R) Ethernet Connection' or 'Gigabit Ethernet Controller' in get_value("DriverDesc"):
                                print(f'PC Name: {name}, adapter {get_value("DriverDesc")}')
                                print('-----------------------------------------------------------------------')
                                # pass
                            try:
                                path = "SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + winreg.EnumKey(
                                    folders, idx)
                                print(path)
                                winreg.CreateKeyEx(root, path)
                                with winreg.OpenKeyEx(root, path, 0, winreg.KEY_ALL_ACCESS) as reg:
                                    print('Try to set value')
                                    winreg.SetValueEx(reg, 'PnPCapabilities', 0, winreg.REG_DWORD, 0x00000100)
                                    winreg.CloseKey(reg)
                                    # key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, folders_info)
                                    print(f'Complete at {name} with first try')
                            except Exception as err_to_set:
                                print('Err to set Value', err_to_set)
                                try:
                                    path = "SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}\\" + winreg.EnumKey(
                                                 folders, idx)
                                    with winreg.OpenKey(root, path, 0, winreg.KEY_WRITE) as reg:
                                        winreg.SetValueEx(reg, 'PnPCapabilities', 0, winreg.REG_DWORD, 0x00000100)
                                        winreg.CloseKey(reg)
                                        print(f'Complete at {name} with second try')
                                except Exception as err_to_create:
                                    print('Err to create and set', err_to_create)
                except (WindowsError, KeyError, ValueError):
                    continue
    except (WindowsError, KeyError, ValueError):
        logging.exception("Failed to set or create value at PC:", name)

