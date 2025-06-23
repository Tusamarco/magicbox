import os
from logging import exception

import keyboard

import time

# import keyboard
from proxysqlpkg.proxysql_obj import ProxySQLNode
from rich.console import Console

from pynput import keyboard
from threading import Thread

class Monitor:
    MODE_PROXYSQL_PXC_SUNMMARY = 1
    MODE_PROXYSQL_PXC_QUERY_RULE_USAGE = 2
    MODE_RUN = 1
    MODE_PAUSE = 2
    MODE_STOP = 0

    def __init__(self,proxy_node:ProxySQLNode = None):
        self.status = self.MODE_RUN
        self.mode = self.MODE_PROXYSQL_PXC_SUNMMARY
        self.refresh_rate = 1  # seconds
        self.last_lines = 0
        self.proxy_node = proxy_node
        self.console = Console(width=400,soft_wrap=True)


    #
    # def clear_previous_output(self):
    #     # Move cursor up and clear lines from previous output
    #     for _ in range(self.last_lines):
    #         sys.stdout.write('\x1b[1A\x1b[2K')  # Move up and clear line
    #     sys.stdout.flush()
    #     self.last_lines = 0

    def display_summary(self, incoming_data:[str] = ""):
        output = []
        output.append("=== PXC CLUSTER connection Overview  ===")
        output.append("Press 'q' to quit, 'p' to pause, 's' to start again 'm' to toggle mode")
        output.append(" ")
        count = 0
        while count < len(incoming_data):
            output.append(incoming_data[count])
            count += 1
        return output

    def print_output(self, lines):
        self.console.clear(True)
        os.system('cls' if os.name == 'nt' else 'clear')

        for line in lines:
            print(f"{line}")
            # self.console.print(line, end="\r")
            # print(line)
        # self.last_lines = len(lines)

    def monitor(self):
        global clear_entry
        if self.proxy_node is None:
            raise exception("ProxySQL NOde canot be None when monitoring")

        print("Starting Monitor...")
        print("Press 'q' to quit, 'p' to pause, 's' to start again 'm' to toggle mode")

        # while self.running:
        while not monitor_process_status == Monitor.MODE_STOP:
           if monitor_process_status != Monitor.MODE_PAUSE:
               if self.mode == self.MODE_PROXYSQL_PXC_SUNMMARY:
                    output = self.display_summary(self.proxy_node.monitor_get_connectivity_summary())
               else:
                    output = self.display_summary()

               self.print_output(output)

           if clear_entry:
                self.console.print("\b \b", end="")
           time.sleep(self.refresh_rate)

        print("\nMonitor stopped.")


    def start(self):
        # Start monitoring
        global monitor_process_status
        monitor_process_status = Monitor.MODE_RUN
        self.monitor()
        self.stop()



    def stop(self):
        global monitor_process_status
        monitor_process_status = self.MODE_STOP
        listener.stop()

def on_press(key):
    global monitor_process_status
    global clear_entry
    try:
        if key.char == 'q':
            monitor_process_status = Monitor.MODE_STOP
            listener.stop()
        elif key.char == 'p':
            monitor_process_status = Monitor.MODE_PAUSE
            clear_entry = True
        elif key.char == 's':
            monitor_process_status = Monitor.MODE_RUN
            clear_entry = True


    except AttributeError:
        pass
#
#
# if __name__ == "__main__":q
#     try:
#         monitor = Monitor()
#         monitor.keyboard_listner_start()
#     except KeyboardInterrupt:
#         print("\nMonitoring stopped by user.")
#     except Exception as e:
#         print(f"An error occurred: {e}")

clear_entry = False
monitor_process_status = Monitor.MODE_RUN

listener = keyboard.Listener(on_press=on_press)
listener.start()


