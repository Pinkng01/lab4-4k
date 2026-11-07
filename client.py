import socket
import json
import struct
import os
import sys

def send_file(filepath, host='127.0.0.1', port=5995):
    if not os.path.isfile(filepath):
        print(f"[!] File {filepath} not found.")
        return

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    metadata = {
        "filename": filename,
        "filesize": filesize
    }
    metadata_json = json.dumps(metadata).encode('utf-8')
    metadata_len = len(metadata_json)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        client.sendall(struct.pack('>I', metadata_len))

        client.sendall(metadata_json)

        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                client.sendall(chunk)
        
        print(f"[*] File {filename} sent successfully.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <file_path>")
    else:
        send_file(sys.argv[1])