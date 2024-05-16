import os
import csv
import socket
import threading
import create_model as cm
import firebase_utils.modules as fb

SERVER_DATA_PATH = r"server\server_data"

IP = socket.gethostbyname(socket.gethostname())
PORT = 4456
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

aliases = "admin"


def receive():
    while True:
        try:
            data = client.recv(SIZE).decode(FORMAT)
            cmd, msg = data.split("@")

            if cmd == "DISCONNECTED":
                print(f"[SERVER]: {msg}")
                break
            elif cmd == "OK":
                print(f"{msg}")

            elif cmd == "alias":
                client.send(aliases.encode(FORMAT))
                continue

            elif cmd == "broad":
                print(f"{msg}")
                continue

        except:
            print("logging out!")
            client.close()
            break


def write():
    
    while True:
        try:
            data = input("")
            data = data.split(" ")
            cmd = data[0]

            if cmd == "HELP":
                client.send(cmd.encode(FORMAT))

            elif cmd == "LOGOUT":
                client.send(cmd.encode(FORMAT))
                break

            elif cmd == "LIST":
                client.send(f"{cmd}@{data[1]}@{data[2]}".encode(FORMAT))

            elif cmd == "DELETE":
                client.send(f"{cmd}@{data[1]}".encode(FORMAT))


            elif cmd =="CREATE_MODEL":  
                file_id,dataset_name = data[1],data[2]

                if file_id == "metadata":
                    print(f"creating globalZERO for {dataset_name} dataset...")
                    METADATA_PATH = "metadata/" + dataset_name 
                    folder_path = os.path.join(SERVER_DATA_PATH, METADATA_PATH)
                    if cm.metadata_checker(folder_path):
                        STORED_MODEL_PATH = "stored_models/" + dataset_name
                        global_path = os.path.join(SERVER_DATA_PATH, STORED_MODEL_PATH,"global_models")
                        cm.create_architecture(folder_path,global_path)
                        print(f"\nglobalZERO saved successfully !\n")

                    else:
                        print("invalid or not sufficient metadatas...")

                if file_id=="model":
                    print(f"creating global model for {dataset_name} dataset...\n")
                    STORED_MODEL_PATH = "stored_models/" + dataset_name
                    folder_path = os.path.join(SERVER_DATA_PATH, STORED_MODEL_PATH)
                    model_paths = cm.get_latest_models(folder_path)
                    # print(model_paths)
                    if len(model_paths)>=2:
                        folder_path = os.path.join(folder_path, "global_models")
                        cm.aggregating_models(model_paths,folder_path)
                        print(f"\nglobal model saved successfully !\n")
                    else:
                        print("invalid or not sufficient models...")


            elif cmd == "UPLOAD":
                file_id,path = data[1],data[2]

                if file_id=="metadata":
                    file = open(path, "rb")
                    file_size = os.path.getsize(path)
                    filename = os.path.basename(path)
                    send_data = f"{cmd}@{alias}_{filename}@{str(file_size)}"
                    # print(send_data)
                    client.send(send_data.encode(FORMAT))
                    data = file.read()
                    print(f"Sending {filename} to server...")
                    client.sendall(data)
                    client.send(b"<END>")
                    file.close()
                    print("File sent successfully...press <HELP>\n")

                elif file_id=="model":
                    filepaths = path.split("\\")
                    filename = os.path.basename(path)
                    print(f"Sending {filename} to server...")
                    CLOUD_PATH = "stored_models/"+ filepaths[-3]+"/"+filepaths[-2]
                    print(CLOUD_PATH)
                    fb.upload_to_firebase(path,CLOUD_PATH)
                    print("upload complete\n")


            elif cmd =="OPEN" or cmd =="CLOSE":
                if data[1] == "DOWNLOAD" or data[1] == "UPLOAD":
                    client.send(f"{cmd}@{data[1]}".encode(FORMAT))
                else:
                    print("cant give access to client")
            
            elif cmd == "DOWNLOAD":
                dataset_name =  data[1]
                MODEL_PATH = "stored_models/" + dataset_name
                fb.download_from_firebase(SERVER_DATA_PATH,MODEL_PATH)
                print("download complete")

        except Exception as e :
            print(f"[EXCEPTION] {e}")
            print("Disconnected from the server.")
            client.close()
            break

if __name__ == "__main__":

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()