import time
import sys
import os

# Ensure repo root is on sys.path so local packages can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ipc.native_pipe import IPCClient


if __name__ == '__main__':
    # Use the v2 pipe name (service uses "\\.\pipe\E.V3.v2")
    client = IPCClient(pipe_name=r"\\.\pipe\E.V3.v2")
    ok = client.connect(2000)
    if not ok:
        print('connect failed')
        sys.exit(1)
    print('connected')
    client.send_message('user_message', {'message': 'hi from test'})
    print('message sent')
    time.sleep(1)
    client.disconnect()
    print('disconnected')
