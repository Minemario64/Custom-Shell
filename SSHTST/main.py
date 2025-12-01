import paramiko
import socket
import threading

sprint = lambda s: s

def handle_client(client_socket):
    # Use Paramiko to handle SSH client connections
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(paramiko.RSAKey.generate(2048))

    server = paramiko.ServerInterface()
    transport.start_server(server=server)

    # Additional code to handle SSH sessions
    server.check_auth_password("2000098075", "^EHLO$")

# Set up the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 180))  # Bind to port 180 for SSH
server_socket.listen(100)

sprint("Paramiko SSH Server running.")

print("(0 . 0)")

while True:
    client, addr = server_socket.accept()
    sprint(f"Accepted connection from {addr}")
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()