import socket
import threading
import sys

def handle_connection(conn, addr, name, shutdown_event):
    """ Handle incoming messages and file transfers from a connection. """
    try:
        while not shutdown_event.is_set():
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break
                if data.startswith(f"{name}:exit"):
                    print(f"Connection with {addr} closed by {name}. Exiting.")
                    shutdown_event.set()
                    break
                elif data.startswith('transfer'):
                    _, filename = data.split(':')
                    new_filename = f'new_{filename}'
                    with open(new_filename, 'wb') as f:
                        while True:
                            bits = conn.recv(4096)
                            if b'EOFEOFEOF' in bits:
                                f.write(bits[:-9])
                                break
                            f.write(bits)
                    print(f"Received file successfully: {new_filename}")
                else:
                    print(data)
            except socket.error:
                shutdown_event.set()
                break
    finally:
        conn.close()
        print("Connection closed. Exiting thread.")

def client_thread(target_port, name, shutdown_event):
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', target_port))
            while not shutdown_event.is_set():
                message = input(f"{name}: ")
                if message == 'exit':
                    s.sendall(f"{name}:exit".encode())
                    shutdown_event.set()
                    break
                elif message.strip() == '':  
                    continue 
                elif message.startswith('transfer'):
                    parts = message.split(maxsplit=1)  
                    if len(parts) < 2:
                        print("Invalid command. Usage: transfer <filename>")
                        continue
                    command, filename = parts
                    s.sendall(f"transfer:{filename}".encode())
                    with open(filename, 'rb') as f:
                        content = f.read()
                        s.sendall(content + b'EOFEOFEOF')
                    print(f"File sent successfully: {filename}")
                else:
                    s.sendall(f"{name}:{message}".encode())
    except socket.error as e:
        print(f"Connection error: {e}")
        shutdown_event.set()

def main():
    shutdown_event = threading.Event()
    name = input("Enter your name: ")
    host = 'localhost'
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, 0))
    server.listen(1)

    print(f"{name}: Server is listening on port {server.getsockname()[1]}")

    target_port = int(input(f"Enter the port number to connect to: "))
    thread = threading.Thread(target=client_thread, args=(target_port, name, shutdown_event))
    thread.daemon = True
    thread.start()

    try:
        conn, addr = server.accept()
        if not shutdown_event.is_set():
            print(f"Connected by {addr}")
            handle_connection(conn, addr, name, shutdown_event)
    finally:
        server.close()
        print("Server has been closed.")

if __name__ == '__main__':
    main()
