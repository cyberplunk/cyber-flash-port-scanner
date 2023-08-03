import tracemalloc
tracemalloc.start()

import pyfiglet
import socket
import sys
import asyncio
from datetime import datetime

class HostUnreachableError(Exception):
    pass

async def is_host_up(target, timeout=5):
    try:
        # Try to connect to the target host to check if it is reachable
        await asyncio.wait_for(
            asyncio.open_connection(target, 80), timeout=timeout
        )
        return True
    except (socket.gaierror, asyncio.TimeoutError):
        # Raise a custom exception if the host is unreachable
        raise HostUnreachableError
    except:
        return False

async def scan_ports(target, start_port, end_port, timeout=5, concurrency=100):
    open_ports = []

    async def scan_port(port):
        try:
            # Try to connect to the target host and port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target, port), timeout=timeout
            )
            # If the connection is successful, the port is open
            writer.close()
            await writer.wait_closed()
            open_ports.append(port)
        except:
            # If any error occurs during the connection attempt, the port is considered closed
            pass

    # If start_port is greater than end_port, swap their values
    if start_port > end_port:
        start_port, end_port = end_port, start_port

    # Limit the range of ports from 1 to 65535
    start_port = max(1, start_port)
    end_port = min(end_port, 65535)

    # Scan all ports from the start_port to end_port asynchronously with limited concurrency
    semaphore = asyncio.Semaphore(concurrency)
    async with semaphore:
        tasks = [scan_port(port) for port in range(start_port, end_port + 1)]
        await asyncio.gather(*tasks)

    return open_ports

def get_service_name(port):
    try:
        # Get the service name corresponding to the port, if available
        return socket.getservbyport(port)
    except OSError:
        # If the service name is not found, return "Unknown"
        return "Unknown"

async def main():
    ascii_banner = pyfiglet.figlet_format("CYBER FLASH")
    print(ascii_banner)

    target = input("Enter the target host IP address or hostname: ")
    print("-" * 50)

    try:
        if await is_host_up(target):
            print(f"Host {target} is up.")
        else:
            print(f"Host {target} is unreachable.")
            sys.exit()

        print("Scanning Target: " + target)
        print("Scanning started at: " + str(datetime.now()))
        print("-" * 50)

        start_port = int(input("Enter the starting port to scan: "))
        end_port = int(input("Enter the ending port to scan: "))

        open_ports = await scan_ports(target, start_port, end_port)

        if open_ports:
            print(f"\nOpen ports on {target}:")
            for port in open_ports:
                # Get the service name for each open port
                service_name = get_service_name(port)
                print(f"Port {port}: {service_name} - Open")
        else:
            print(f"\nNo open ports found on {target} in the specified range.")

    except KeyboardInterrupt:
        print("\nScanning interrupted by user.")
    except HostUnreachableError:
        print(f"Host {target} is unreachable.")
    except asyncio.TimeoutError:
        print(f"Timeout: Host {target} is not responding.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
