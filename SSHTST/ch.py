# requirements: pip install paramiko
import socket
import threading
import paramiko
import sys
import subprocess
import paramiko.common as paramikocon


HOST_KEY = paramiko.RSAKey.generate(2048)  # generate for demo; load from file in real use

class SimpleServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramikocon.OPEN_SUCCEEDED
        return paramikocon.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Replace with proper auth (publickey) for security
        if username == "test" and password == "test":
            return paramikocon.AUTH_SUCCESSFUL
        return paramikocon.AUTH_FAILED

    def check_channel_exec_request(self, channel, command):
        self.command = command.decode() if isinstance(command, bytes) else command
        self.event.set()
        return True

def handle_client(client):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)
    server = SimpleServer()
    try:
        transport.start_server(server=server)
    except paramiko.SSHException:
        client.close()
        return

    chan = transport.accept(20)
    if chan is None:
        transport.close()
        return

    server.event.wait(10)
    cmd = getattr(server, "command", None)
    if cmd:
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = e.output
        chan.send(output)
    chan.close()
    transport.close()

def serve(port=2222, host="0.0.0.0"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    print(f"Listening on {host}:{port}")
    while True:
        client, addr = sock.accept()
        t = threading.Thread(target=handle_client, args=(client,), daemon=True)
        t.start()

if __name__ == "__main__":
    serve(180)
