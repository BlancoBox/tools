import socket
import threading

def handle_client(client_socket):
    remote_host = 'localhost'  # Replace with your server's address
    remote_port = 80  # Replace with the port of your server

    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    while True:
        # Receive data from the client
        client_data = client_socket.recv(4096)
        if not client_data:
            break

        # Forward data to the remote server
        remote_socket.send(client_data)

        # Receive data from the remote server
        remote_response = remote_socket.recv(4096)
        if not remote_response:
            break

        # Forward data back to the client
        client_socket.send(remote_response)

    client_socket.close()
    remote_socket.close()

def main():
    server_host = '0.0.0.0'  # Listen on all interfaces
    server_port = 8080  # Replace with the port you want to listen on

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)

    print(f"[*] Listening on {server_host}:{server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
