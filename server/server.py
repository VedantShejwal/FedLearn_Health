
import os
import copy
import tqdm
import socket
import threading

IP = socket.gethostbyname(socket.gethostname())
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = r"server\server_data"

clients = []
aliases = []
client_cmd = []

def broadcast (message):
    for client in clients:
        client.send(message)

def combine_string(access_cmd,combined_details):
    for name, details in access_cmd.items():
        if details["access"]:  # Check if access is True
            combined_details += details["detail"]
    print(combined_details)

def update_access(cmd_name, access_value):
    for element in client_cmd: 
        for client_type, commands in element.items(): 
            if client_type == "client": 
                for name, details in commands.items(): 
                    if name == cmd_name: 
                        details["access"] = access_value 
     
    for name, details in access_cmd.items(): 
        if name == cmd_name: 
            details["access"] = access_value 

access_cmd = {
    "LIST": {
        "detail": "\nLIST <id> <dataset_name>: List all the files.\n",
        "access": False},
    "UPLOAD": {
        "detail": "UPLOAD <id> <path>: Upload to server. (id - metadata/model)\n",
        "access": False},
    "DOWNLOAD": {
        "detail": "DOWNLOAD <dataset_name>: Download a global models from firebase.\n",
        "access": False},
    "DELETE": {
        "detail": "DELETE <filename>: Delete a file (not implemented yet).\n",
        "access": False},
    "CREATE_MODEL": {
        "detail": "CREATE_MODEL <id> <dataset_name> : create model from (id - metadata/model).\n",
        "access": True},
    "TRAIN": {
        "detail": "TRAIN <id> <dataset_path> : train model (id - global/globalZERO) on particular dataset\n",
        "access": True},
    "TEST": {
        "detail": "TEST <dataset_path> : test all your model on particular dataset\n",
        "access": True},
    "OPEN": {
        "detail": "OPEN <cmd> : Open the access command.\n",
        "access": False},
    "CLOSE": {
        "detail": "CLOSE <cmd> : Close the access command .\n",
        "access": False},
    "LOGOUT": {
        "detail": "LOGOUT: Disconnect from the server.\n",
        "access": True},
    "HELP": {
        "detail": "HELP: List all the commands.",
        "access": True}
}


def handle_client(conn, addr):
    index= clients.index(conn)
    alias = aliases[index]
    access_key = "admin" if alias == "admin" else "client"

    print(f"\n[NEW CONNECTION] {addr} ---> [{alias}] is connected.\n")
    conn.send(f"OK@Welcome to the File Server {alias}.\n".encode(FORMAT))
    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
            data = data.split("@")
            cmd = data[0]
            
            client_access_cmd = client_cmd[clients.index(conn)]

            if client_access_cmd[access_key][cmd]["access"]==True:

                if cmd == "LIST":
                    file_id, dataset = data[1], data[2]

                    if file_id == "metadata":
                        METADATA_PATH = "metadata/" + dataset 
                        filepath = os.path.join(SERVER_DATA_PATH, METADATA_PATH)
                    files = os.listdir(filepath)
                    send_data = "OK@"
                    if len(files) == 0:
                        send_data += "The server directory is empty"
                    else:
                        send_data += "\n".join(f for f in files)
                    conn.send(send_data.encode(FORMAT))

                elif cmd == "UPLOAD":
                    filename, file_size = data[1], data[2]
                    name,dataset,file_id = filename.split("_")
                    print(f"[{alias}] downloading {file_id}.. .")
                    if file_id == "metadata.csv":
                        METADATA_PATH = "metadata/" + dataset 
                        filepath = os.path.join(SERVER_DATA_PATH, METADATA_PATH ,filename)
                    directory = os.path.dirname(filepath)
                    os.makedirs(directory, exist_ok=True)
                    file= open(filepath, 'wb')
                    file_bytes=b""
                    while True:
                        data = conn.recv(SIZE)
                        if file_bytes[-5:] == b"<END>":
                            break
                        else:
                            file_bytes += data
                    file_bytes = file_bytes[:-5]
                    file.write(file_bytes)
                    file.close()
                    print(f"[{alias}] download completed.")
                    send_data = "OK@File uploaded successfully."
                    conn.send(send_data.encode(FORMAT))

                elif cmd == "DELETE":
                    files = os.listdir(SERVER_DATA_PATH)
                    send_data = "OK@"
                    filename = data[1]
                    if len(files) == 0:
                        send_data += "The server directory is empty"
                    else:
                        if filename in files:
                            os.system(f"rm {SERVER_DATA_PATH}/{filename}")
                            send_data += "File deleted successfully."
                        else:
                            send_data += "File not found."
                    conn.send(send_data.encode(FORMAT))

                elif cmd == "LOGOUT":
                    index= clients.index(conn)
                    clients. remove(conn)
                    alias = aliases[index]
                    broadcast(f"broad@[{alias}] left the server!".encode(FORMAT))
                    aliases.remove(alias)
                    client_cmd.pop(index)
                    break
                
                elif cmd == "HELP":
                    data = "OK@"
                    for name, details in client_access_cmd[access_key].items():
                        if details["access"]:
                            data += details["detail"]
                    conn.send(data.encode(FORMAT))

                elif cmd == "OPEN":
                    cmd_name = data[1]
                    update_access(cmd_name,True)
                    broadcast(f"broad@[{cmd_name}] is open!".encode(FORMAT))

                elif cmd == "CLOSE":
                    cmd_name = data[1]
                    update_access(cmd_name,False)
                    broadcast(f"broad@[{cmd_name}] is closed!".encode(FORMAT))
            else:   
                conn.send("ok@no access".encode(FORMAT))

        except Exception as e:
                index= clients.index(conn)
                clients. remove(conn)
                alias = aliases[index]
                print(f"[EXCEPTION] {e}")
                broadcast(f"broad@[{alias}] left the server due to an error!".encode(FORMAT))
                aliases.remove(alias)
                client_cmd.pop(index)
                break

    print(f"[DISCONNECTED] {addr} ---> [{alias}] is disconnected.\n")
    conn.close()


def main():
    print("[STARTING] Server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening {IP}:{PORT}")

    while True:
        conn, addr = server.accept()
        conn.send("alias@hi".encode(FORMAT))
        alias = conn.recv(SIZE).decode(FORMAT)
        aliases.append(alias)
        clients.append(conn)
        if alias == "admin":
            admin_access_cmd = copy.deepcopy(access_cmd)
            for command, details in admin_access_cmd.items():
                details["access"] = True
            modified_dict = {"admin": admin_access_cmd}
            client_cmd.append(modified_dict)
        else: 
            modified_dict = {"client": access_cmd}
            client_cmd.append(modified_dict)
        broadcast(f"broad@[{alias}] joined the server!".encode(FORMAT))
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    main()