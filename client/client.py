import os
import csv
import socket
import threading
import create_model as cm
import firebase_utils.modules as fb
CLIENT_DATA_PATH = r"client\client_data"

IP = socket.gethostbyname(socket.gethostname())
# IP = "10.23.25.231"
PORT = 4456
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

alias = "vedant"

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
                client.send(alias.encode(FORMAT))
                continue

            elif cmd == "broad":
                print(f"{msg}")
                continue
                
        except Exception as e :
            # print(f"[EXCEPTION] {e}")
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
                client.send(cmd.encode(FORMAT))

            elif cmd == "DELETE":
                client.send(f"{cmd}@{data[1]}".encode(FORMAT))

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


            elif cmd =="CREATE_MODEL":  
                file_id,dataset_name = data[1],data[2]
                if file_id=="model":
                    print(f"aggregating latest global model and local model for {dataset_name} dataset...\n")
                    STORED_MODEL_PATH = "stored_models/" + dataset_name
                    folder_path = os.path.join(CLIENT_DATA_PATH, STORED_MODEL_PATH)
                    model_paths = cm.get_latest_models(folder_path)
                    # print(model_paths)
                    if len(model_paths)>=2:
                        folder_path = os.path.join(folder_path, f"{alias}_models")
                        cm.aggregating_models(model_paths,folder_path,alias)
                        print(f"\nglobal model saved successfully !\n")
                    else:
                        print("invalid or not sufficient models...")

                elif file_id =="metadata":
                    print("this feature only for server side...")


            elif cmd == "DOWNLOAD":
                dataset_name =  data[1]
                MODEL_PATH = "stored_models/" + dataset_name + "/global_models"
                fb.download_from_firebase(CLIENT_DATA_PATH,MODEL_PATH)
                print("download complete")
            
            elif cmd == "TEST":
                dataset_path = data[1]
                dataset_path_dirname = os.path.dirname(dataset_path)
                dataset_name = os.path.basename(dataset_path_dirname)
                STORED_MODEL_PATH = "stored_models/" + dataset_name 
                folder_path = os.path.join(CLIENT_DATA_PATH, STORED_MODEL_PATH,f"{alias}_models")
                dataset_path_name = os.path.basename(dataset_path)
                csv_file = os.path.join(CLIENT_DATA_PATH,"results",f"results_{dataset_name}_{dataset_path_name}")
                cm.test_model(folder_path,csv_file,dataset_path) 
                print("\nresults saved successfully!\n")

            elif cmd == "TRAIN":
                model_type,dataset_path = data[1],data[2]
                dataset_path_dirname = os.path.dirname(dataset_path)
                dataset_name = os.path.basename(dataset_path_dirname)
                STORED_MODEL_PATH = "stored_models/" + dataset_name
                folder_path = os.path.join(CLIENT_DATA_PATH, STORED_MODEL_PATH)
                if model_type == "global":
                    model_path=cm.model_to_train(folder_path,alias)
                elif model_type == "globalZERO":
                    model_path=cm.model_to_train(folder_path,model_type)

                if len(model_path)==1:
                    folder_path = os.path.join(folder_path,f"{alias}_models")
                    cm.train_model(model_path,alias,dataset_path,folder_path)
                else:
                   print("invalid or not sufficient model...") 
                   
                print("\nmodel saved successfully!\n")
                

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