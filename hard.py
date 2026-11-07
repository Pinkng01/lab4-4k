import socket
import json
import struct
import os
import threading

def handle_client(client_socket, addr, save_dir):
    try:
        # 1. Receive 4 bytes of JSON length (big-endian unsigned int)
        raw_json_len = client_socket.recv(4)
        if not raw_json_len:
            return
        json_len = struct.unpack('>I', raw_json_len)[0]

        # 2. Receive JSON metadata
        json_data_bytes = b''
        while len(json_data_bytes) < json_len:
            chunk = client_socket.recv(json_len - len(json_data_bytes))
            if not chunk:
                break
            json_data_bytes += chunk
        
        metadata = json.loads(json_data_bytes.decode('utf-8'))
        filename = metadata.get('filename', 'unnamed_file')
        file_size = metadata.get('filesize', 0)

        print(f"[*] Receiving: {filename} ({file_size} bytes) from {addr}")

        # 3. Receive file content
        save_path = os.path.abspath(os.path.join(save_dir, filename))
        print(f"[*] Saving to: {save_path}")
        
        with open(save_path, 'wb') as f:
            received = 0
            while received < file_size:
                to_read = min(file_size - received, 4096)
                chunk = client_socket.recv(to_read)
                if not chunk:
                    print(f"[!] Connection lost after {received} bytes")
                    break
                f.write(chunk)
                received += len(chunk)
            f.flush()
            os.fsync(f.fileno())

        if received == file_size:
            print(f"[*] Successfully saved {received} bytes to {save_path}")
        else:
            print(f"[!] Warning: Received {received}/{file_size} bytes")

    except Exception as e:
        print(f"[!] Error handling client {addr}: {e}")
    finally:
        client_socket.close()

def start_server(host='0.0.0.0', port=5995):
    # Determine the save directory: ~/Desktop
    save_dir = os.path.expanduser("~/Desktop")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
            
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
    except Exception as e:
        print(f"[!] Bind failed: {e}")
        return

    server.listen(5)
    print(f"[*] Server listening on {host}:{port}")
    print(f"[*] Saving files to: {save_dir}")

    try:
        while True:
            client, addr = server.accept()
            print(f"[*] Accepted connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client, addr, save_dir))
            client_handler.daemon = True
            client_handler.start()
    except KeyboardInterrupt:
        print("\n[*] Server shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
