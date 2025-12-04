"""Wake-on-LAN cycle script for managing PC power states.

This script manages waking up computers via Wake-on-LAN protocol,
tracking their MAC addresses, and monitoring their online status.
"""

import subprocess
import sys
import time
from typing import Dict, List, Optional, Set

from getmac import get_mac_address
from ping3 import ping
from wakeonlan import send_magic_packet
import logging

from internal import picklefunc


# Configuration constants
class Config:
    """Configuration constants for the wake cycle."""
    PC_NAME_TEMPLATE = "ws-tmb-a0{:03d}"
    PCS_COUNT_FILE = "internal/pcs_count.txt"
    EXCLUDE_FILE = "internal/exclude.txt"
    INCLUDE_FILE = "internal/include.txt"
    LOG_FILE = "wakelog.log"
    MAC_TABLE_NAME = "MAC_Table"
    REBOOT_LIST_NAME = "to_reboot"
    
    # Timing configuration
    PING_TIMEOUT_SECONDS = 1
    MAX_PING_RETRIES = 5
    POWER_SCHEME_WAIT_INITIAL = 20
    POWER_SCHEME_WAIT_BETWEEN = 10
    CYCLE_SLEEP_SECONDS = 180
    MAX_WAKE_CYCLES = 10
    
    # Power scheme configuration
    POWER_SCHEME_CHANGE_RETRY = 4


# Logging setup
def setup_logging() -> None:
    """Configure logging with file and console handlers."""
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    
    logging.basicConfig(
        handlers=(file_handler, console_handler),
        format='[%(asctime)s | %(levelname)s]: %(message)s',
        datefmt='%m.%d.%Y %H:%M:%S',
        level=logging.INFO
    )


setup_logging()


def format_pc_name(pc_number: int) -> str:
    """Format PC number into standardized hostname.
    
    Args:
        pc_number: The numeric identifier for the PC
        
    Returns:
        Formatted hostname string (e.g., 'ws-tmb-a0001')
    """
    return Config.PC_NAME_TEMPLATE.format(pc_number)


def read_pc_count() -> int:
    """Read and parse the PC count from configuration file.
    
    Returns:
        Number of PCs + 1, defaults to 0 on error
    """
    try:
        with open(Config.PCS_COUNT_FILE, 'r') as f:
            count = int(f.readline().strip().replace(' ', ''))
            return count + 1
    except Exception as err:
        logging.error(f"Error reading PC count: {err}")
        return 0


def read_filter_list(filename: str) -> List[int]:
    """Read a list of PC numbers from a filter file.
    
    Args:
        filename: Name of the filter file (without path/extension)
        
    Returns:
        List of PC numbers to filter
    """
    result = []
    filepath = f"internal/{filename}.txt"
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result.append(int(line))
                    except ValueError:
                        logging.warning(f"Invalid number in {filename}: {line}")
    except FileNotFoundError:
        logging.warning(f"Filter file not found: {filepath}")
    except Exception as err:
        logging.error(f"Error reading {filename}: {err}")
    
    return result


def flush_dns_cache() -> None:
    """Flush the DNS cache to ensure fresh lookups."""
    try:
        subprocess.run('ipconfig /flushdns', shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err:
        logging.error(f"Failed to flush DNS cache: {err}")


def wake_pc(mac_address: str, hostname: str) -> None:
    """Send Wake-on-LAN magic packet to a PC.
    
    Args:
        mac_address: MAC address of the target PC
        hostname: Hostname for logging purposes
    """
    if mac_address is None:
        logging.info(f"Skipping {hostname}: MAC address is None")
        return
    
    try:
        send_magic_packet(mac_address)
        logging.debug(f"Magic packet sent to {hostname} ({mac_address})")
    except Exception as err:
        logging.error(f"Failed to send magic packet to {hostname}: {err}")


def ping_host(hostname: str, timeout: float = Config.PING_TIMEOUT_SECONDS) -> Optional[float]:
    """Ping a host and return round-trip time in milliseconds.
    
    Args:
        hostname: Target hostname to ping
        timeout: Ping timeout in seconds
        
    Returns:
        Round-trip time in milliseconds, or None if host is unreachable
    """
    try:
        result = ping(hostname, timeout)
        if result is None:
            return None
        return round(result * 1000, 1)
    except Exception as err:
        logging.debug(f"Ping failed for {hostname}: {err}")
        return None


def change_power_scheme(hostname: str) -> None:
    """Change Windows power scheme settings via remote execution.
    
    Args:
        hostname: Target PC hostname
    """
    logging.info(f"Changing power scheme for: {hostname}")
    time.sleep(Config.POWER_SCHEME_WAIT_INITIAL)
    
    commands = [
        f"psexec \\\\{hostname} REG ADD HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\238C9FA8-0AAD-41ED-83F4-97BE242C8F20\\7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 /v Attributes /t REG_DWORD /d 2 /f",
        f"psexec \\\\{hostname} powercfg /SETACVALUEINDEX SCHEME_CURRENT 238C9FA8-0AAD-41ED-83F4-97BE242C8F20 7bc4a2f9-d8fc-4469-b07b-33eb785aaca0 0"
    ]
    
    for cmd in commands:
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(Config.POWER_SCHEME_WAIT_BETWEEN)
        except Exception as err:
            logging.error(f"Failed to execute power scheme command: {err}")


def ping_with_retries(
    hostname: str,
    mac_address: str,
    retry_count: int = Config.MAX_PING_RETRIES
) -> Optional[float]:
    """Ping a host with retries, sending wake packets between attempts.
    
    Args:
        hostname: Target hostname
        mac_address: MAC address for wake-on-LAN
        retry_count: Maximum number of retry attempts
        
    Returns:
        Round-trip time in milliseconds if successful, None otherwise
    """
    for attempt in range(1, retry_count + 1):
        ping_result = ping_host(hostname)
        
        if ping_result is not None:
            # Host is responding
            if attempt >= Config.POWER_SCHEME_CHANGE_RETRY:
                change_power_scheme(hostname)
                logging.info(f"{hostname} woke up successfully")
            return ping_result
        
        # Host not responding, try waking it up
        logging.debug(f"{hostname} not responding, attempt {attempt}/{retry_count}")
        wake_pc(mac_address, hostname)
        
        if attempt == retry_count:
            logging.warning(f"{hostname} failed to respond after {retry_count} attempts")
            return None
    
    return None


def update_mac_address(
    hostname: str,
    mac_table: Dict[str, Optional[str]]
) -> Optional[str]:
    """Get and update MAC address for a hostname.
    
    Args:
        hostname: Target hostname
        mac_table: Current MAC address table
        
    Returns:
        Current MAC address or None if unavailable
    """
    # Ensure hostname exists in table
    if hostname not in mac_table:
        mac_table[hostname] = None
    
    try:
        new_mac = get_mac_address(hostname=hostname)
        
        if new_mac is None:
            logging.debug(f"No MAC address found for {hostname}")
            return mac_table.get(hostname)
        
        old_mac = mac_table.get(hostname)
        if new_mac != old_mac:
            logging.info(f"MAC address updated for {hostname}:")
            logging.info(f"  Old: {old_mac}")
            logging.info(f"  New: {new_mac}")
            mac_table[hostname] = new_mac
        
        return new_mac
        
    except Exception as err:
        logging.error(f"Error getting MAC address for {hostname}: {err}")
        return mac_table.get(hostname)


def process_pc(
    pc_number: int,
    mac_table: Dict[str, Optional[str]],
    offline_pcs: List[str],
    no_mac_pcs: List[str],
    reboot_needed: List[str]
) -> None:
    """Process a single PC: check status, wake if needed, update MAC.
    
    Args:
        pc_number: PC number to process
        mac_table: MAC address lookup table
        offline_pcs: List to append offline PCs
        no_mac_pcs: List to append PCs with no MAC
        reboot_needed: List to append PCs that need reboot
    """
    hostname = format_pc_name(pc_number)
    
    # Update MAC address
    mac_address = update_mac_address(hostname, mac_table)
    
    if mac_address is None:
        logging.info(f"{hostname} has no MAC address, attempting wake anyway")
        no_mac_pcs.append(hostname)
        if hostname in mac_table and mac_table[hostname] is not None:
            wake_pc(mac_table[hostname], hostname)
        return
    
    # Ping with retries
    ping_result = ping_with_retries(hostname, mac_address)
    
    if ping_result is None:
        if hostname not in offline_pcs:
            offline_pcs.append(hostname)
            logging.info(f"{hostname} is offline")


def wake_cycle() -> None:
    """Execute one complete wake cycle for all configured PCs."""
    logging.info("Starting wake cycle")
    
    # Read configuration
    pcs_count = read_pc_count()
    if pcs_count == 0:
        logging.error("Invalid PC count, aborting wake cycle")
        return
    
    exclude_list = read_filter_list('exclude')
    include_list = read_filter_list('include')
    
    # Convert to sets for O(1) lookup
    exclude_set: Set[int] = set(exclude_list)
    include_set: Set[int] = set(include_list) if include_list else set(range(1, pcs_count))
    
    # Flush DNS cache for fresh lookups
    flush_dns_cache()
    
    # Load MAC address table
    mac_table: Dict[str, Optional[str]] = picklefunc.load_obj(Config.MAC_TABLE_NAME)
    if mac_table is None:
        mac_table = {}
    
    # Result tracking
    offline_pcs: List[str] = []
    no_mac_pcs: List[str] = []
    reboot_needed: List[str] = []
    
    # Process each PC
    for pc_num in range(1, pcs_count):
        if pc_num in exclude_set:
            continue
        if pc_num not in include_set:
            continue
        
        process_pc(pc_num, mac_table, offline_pcs, no_mac_pcs, reboot_needed)
    
    # Log results
    logging.info("-------------------------------INFO---------------------------------")
    logging.info(f"Offline PCs: {offline_pcs}")
    logging.info(f"PCs with no MAC (possibly truly offline): {no_mac_pcs}")
    logging.info(f"PCs needing reboot: {reboot_needed}")
    logging.info("-----------------------------END INFO-------------------------------")
    
    # Save updated data
    picklefunc.save_obj(mac_table, Config.MAC_TABLE_NAME)
    picklefunc.save_obj(reboot_needed, Config.REBOOT_LIST_NAME)


def main() -> None:
    """Main entry point - run multiple wake cycles."""
    for cycle_num in range(1, Config.MAX_WAKE_CYCLES + 1):
        try:
            logging.info(f"=== Wake cycle {cycle_num}/{Config.MAX_WAKE_CYCLES} ===")
            wake_cycle()
        except Exception as err:
            logging.error(f"Error in wake cycle {cycle_num}: {err}", exc_info=True)
        
        if cycle_num < Config.MAX_WAKE_CYCLES:
            logging.info(f"Sleeping for {Config.CYCLE_SLEEP_SECONDS} seconds...")
            time.sleep(Config.CYCLE_SLEEP_SECONDS)
    
    logging.info("All wake cycles completed")


if __name__ == "__main__":
    main()
