import os
from logging import exception

import time

from proxysqlpkg.proxysql_obj import ProxySQLNode
# from rich.console import Console

from pynput import keyboard
# from threading import Thread


class Monitor:
    """
    The class representing the running monitor
    """
    MODE_PROXYSQL_PXC_SUMMARY = 1
    MODE_PROXYSQL_PXC_LOG = 2
    MODE_PROXYSQL_PXC_QUERY_RULE_USAGE = 3
    MODE_PROXYSQL_PXC_QUERY_RULE_USAGE_STATS = 4
    MODE_RUN = 1
    MODE_PAUSE = 2
    MODE_STOP = 0

    def __init__(self, proxy_node: ProxySQLNode = None):
        self.status = self.MODE_RUN
        self.refresh_rate = 1  # seconds
        self.last_lines = 0
        self.proxy_node = proxy_node
        self.commands_text = ("Press 'q' to quit, 'p' to pause, 's' to start again."
                              "\n '1' for connection; 2 for galera log entries; 3 for query rules")

    # def display_summary(self, incoming_data: [str] = []):
    #     output = []
    #     output.append("=== PXC CLUSTER connection Overview  ===")
    #     output.append(self.commands_text)
    #     output.append(" ")
    #     output.extend(incoming_data)
    #
    #     return output

    def print_output(self, lines:[] = []):
        os.system('cls' if os.name == 'nt' else 'clear')

        for line in lines:
            print(f"{line}")

    def monitor(self):
        """
        This method executes the queries and retrieves a list of strings with results, whatever you may want to print
        Returns: list of strings

        """
        global monitor_mode

        if self.proxy_node is None:
            raise exception("ProxySQL NOde canot be None when monitoring")

        print("Starting Monitor...")
        print(self.commands_text)

        '''
        If Monitor is active (RUN) then it prints the data, otherwise it will only update the timestamp and how the pause message
        '''
        while not monitor_process_status == Monitor.MODE_STOP:
            output = [f"Current time: {time.strftime("%Y-%m-%d %H:%M:%S")}"]
            output.append(self.commands_text)
            output.append("=== ProxySQL PXC CLUSTER monitor  ===")
            output.append("------------------------------------ ")

            # Here is possible to invoke and add whatever data we want to show.
            if monitor_process_status != Monitor.MODE_PAUSE:
                if monitor_mode == self.MODE_PROXYSQL_PXC_SUMMARY:
                    output.append("=== Connections overview  ===")
                    output.append("-----------------------------")
                    output.extend(self.proxy_node.monitor_get_connectivity_summary())
                    output.append("-----------------------------")
                    output.append("=== Connections by backend  ===")
                    output.append("-------------------------------")
                    output.extend(self.proxy_node.monitor_get_connection_by_backend())
                    output.append("-----------------------------")
                    output.append("=== Connections by Frontend Users  ===")
                    output.append("--------------------------------------")
                    output.extend(self.proxy_node.monitor_get_connections_by_user())

                elif monitor_mode == self.MODE_PROXYSQL_PXC_LOG:
                    output.append("=== Galera log  ===")
                    output.append("-------------------")
                    output.extend(self.proxy_node.monitor_get_mysql_galera_log())

                elif monitor_mode == self.MODE_PROXYSQL_PXC_QUERY_RULE_USAGE:
                    output.append("=== Query rules  ===")
                    output.append("--------------------")
                    output.extend(self.proxy_node.monitor_get_query_rules_for_running_PXC_cluster())

                elif monitor_mode == self.MODE_PROXYSQL_PXC_QUERY_RULE_USAGE_STATS:
                    output.append("=== Query rules with usage  ===")
                    output.append("-------------------------------")
                    output.extend(self.proxy_node.monitor_query_rules_with_usage_stats())




                else:
                    output = self.display_summary()
            else:
                output.extend(["== Monitor Paused =="])

            self.print_output(output)

            time.sleep(self.refresh_rate)

        print("\nMonitor stopped.")

    def start(self,refresh = 1):
        """
        This method starts the monitor
        Returns:Void

        """
        global monitor_process_status
        monitor_process_status = Monitor.MODE_RUN
        self.refresh_rate = refresh
        self.monitor()
        self.stop()

    def stop(self):
        """
        This method stops the monitor
        Returns: Void
        """
        global monitor_process_status
        monitor_process_status = self.MODE_STOP
        listener.stop()


def on_press(key):
    """
    This method is called when a key is pressed
    and change the state of the process accordingly
    Args:
        key:

    Returns:Void
    """
    global monitor_mode
    global monitor_process_status
    global clear_entry
    try:
        if key.char == 'q':
            monitor_process_status = Monitor.MODE_STOP
            listener.stop()
        elif key.char == 'p':
            monitor_process_status = Monitor.MODE_PAUSE
        elif key.char == 's':
            monitor_process_status = Monitor.MODE_RUN
        elif key.char == '1':
            monitor_mode = Monitor.MODE_PROXYSQL_PXC_SUMMARY
        elif key.char == '2':
            monitor_mode = Monitor.MODE_PROXYSQL_PXC_LOG
        elif key.char == '3':
            monitor_mode = Monitor.MODE_PROXYSQL_PXC_QUERY_RULE_USAGE
        elif key.char == '4':
            monitor_mode = Monitor.MODE_PROXYSQL_PXC_QUERY_RULE_USAGE_STATS


    except AttributeError:
        pass

    except KeyboardInterrupt:
        monitor_process_status = Monitor.MODE_STOP


clear_entry = False
monitor_process_status = Monitor.MODE_RUN
monitor_mode = Monitor.MODE_PROXYSQL_PXC_SUMMARY

listener = keyboard.Listener(on_press=on_press)
listener.start()


