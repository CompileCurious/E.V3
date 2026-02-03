"""Simple CLI shell to receive kernel output and send messages.

Usage: python ev3_shell.py

Connects to the IPC server and prints `state_update` and `llm_response` messages.
You can type messages and press Enter to send them as `user_message` to the kernel.
Type `exit` or `quit` to end the shell.
"""

import threading
import time
import sys
from loguru import logger
from ipc import IPCClient


class EV3Shell:
    def __init__(self, pipe_name=r"\\.\pipe\E.V3.v2", buffer_size=4096):
        self.ipc = IPCClient(pipe_name=pipe_name, buffer_size=buffer_size)
        self.running = False
        self.last_state_data = None

        # register handlers
        self.ipc.register_handler("state_update", self.handle_state_update)
        self.ipc.register_handler("llm_response", self.handle_llm_response)

    def handle_state_update(self, data):
        # store last state for user commands
        self.last_state_data = data
        state = data.get("state", "unknown")
        message = data.get("message", "")
        priority = data.get("priority", 0)
        ts = data.get("timestamp", "")
        print(f"[STATE] {state} (priority={priority}) - {message} {ts}")

        # Suggest actions for important events
        msg_lower = message.lower() if message else ""
        keywords = ("scan", "virus", "defender", "threat", "firewall", "alert")
        if any(k in msg_lower for k in keywords) or priority >= 2:
            print("Suggested actions: [dismiss] remove notification, [details] show metadata, [askllm] ask LLM to interpret")

    def handle_llm_response(self, data):
        message = data.get("message", "")
        print(f"[LLM] {message}")

    def start(self):
        self.running = True

        # connect (with retries)
        connected = self.ipc.connect(timeout_ms=2000)
        if not connected:
            logger.warning("Unable to connect to IPC server. Retrying in background...")
            # retry loop in background
            threading.Thread(target=self._retry_connect, daemon=True).start()
        else:
            logger.info("Connected to kernel")

        # start input loop
        try:
            while self.running:
                try:
                    line = input()
                except EOFError:
                    break

                if not line:
                    continue
                cmd = line.strip()
                if cmd.lower() in ("exit", "quit"):
                    self.stop()
                    break

                # quick commands handled locally
                if cmd.lower() == "dismiss":
                    if self.ipc.connected:
                        self.ipc.send_message("dismiss", {})
                        print("Sent dismiss to kernel")
                    else:
                        print("Not connected: cannot dismiss")
                    continue

                if cmd.lower() == "details":
                    if self.last_state_data:
                        print("DETAILS:", self.last_state_data)
                    else:
                        print("No recent state data available")
                    continue

                if cmd.lower() == "askllm":
                    if self.last_state_data and self.ipc.connected:
                        text = self.last_state_data.get("message", "")
                        self.ipc.send_message("user_message", {"message": f"Please interpret this event: {text}"})
                        print("Requested LLM interpretation")
                    else:
                        print("No data to ask LLM about or not connected")
                    continue

                # send arbitrary user message to service
                if self.ipc.connected:
                    self.ipc.send_message("user_message", {"message": cmd})
                else:
                    print("Not connected to kernel; message not sent.")

        except KeyboardInterrupt:
            pass

    def _retry_connect(self):
        while self.running and not self.ipc.connected:
            time.sleep(2)
            if self.ipc.connect(timeout_ms=2000):
                logger.info("Connected to kernel (retry)")
                break

    def stop(self):
        self.running = False
        try:
            self.ipc.disconnect()
        except Exception:
            pass


def main():
    logger.info("Starting E.V3 CLI shell - connect to the running service to receive outputs")
    shell = EV3Shell()
    shell.start()


if __name__ == "__main__":
    main()
