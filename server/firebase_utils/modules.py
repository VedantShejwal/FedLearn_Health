import os
import shutil
import pyrebase
import firebase_admin
from firebase_admin import storage, credentials, db

cred = credentials.Certificate(r"client\firebase_utils\federated-learning-c4283-firebase-adminsdk-xmdd3-5a25ebd3ed.json")

try:
    app = firebase_admin.get_app()
except ValueError:
    app = firebase_admin.initialize_app(cred, {
        'storageBucket': "federated-learning-c4283.appspot.com"
    })

bucket = storage.bucket(app=firebase_admin.get_app(), name="federated-learning-c4283.appspot.com")

firebaseConfig = {
  "apiKey": "AIzaSyCLaXd7alRWxBAgeLN33dID5XlS3w_j610",
  "authDomain": "federated-learning-c4283.firebaseapp.com",
  "databaseURL": "https://federated-learning-c4283-default-rtdb.firebaseio.com",
  "projectId": "federated-learning-c4283",
  "storageBucket": "federated-learning-c4283.appspot.com",
  "messagingSenderId": "424557807998",
  "appId": "1:424557807998:web:e0b3fc66c7195439478b2f",
  "measurementId": "G-WDLN8SFXQ2"
}


firebase=pyrebase.initialize_app(firebaseConfig)

storage=firebase.storage()

def upload_to_firebase(folder_path, cloud_folder_path):
    if os.path.isdir(folder_path): 
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                destination_path = os.path.join(cloud_folder_path, os.path.basename(folder_path), relative_path)
                storage.child(destination_path.replace('\\', '/')).put(file_path.replace('\\', '/'))
        print(f"Uploaded {folder_path} to {cloud_folder_path}")
    elif os.path.isfile(folder_path):
        destination_path = os.path.join(cloud_folder_path, os.path.basename(folder_path))
        storage.child(destination_path.replace('\\', '/')).put(folder_path)
        print(f"Uploaded {folder_path} to {cloud_folder_path}")
    else:
        print("invalid paths")


def move_file(src, dst):
    try:
        shutil.move(src, dst)
        # print(f"File moved from {src} to {dst}")
    except Exception as e:
        pass
        # print(f"Error occurred while moving file: {e}")


def download_from_firebase(folder_path, cloud_folder_path):
    print("downloading...")
    blobs = bucket.list_blobs(prefix=cloud_folder_path)

    for blob in blobs:
        
        if cloud_folder_path in blob.name:

            blob_basename = os.path.basename(blob.name)
            blob_path = os.path.dirname(blob.name)
            
            local_file_path = os.path.join(folder_path, blob_path)
            os.makedirs(local_file_path, exist_ok=True)
            dst = os.path.join(local_file_path,blob_basename)
            cwd = os.getcwd()
            src = os.path.join(cwd,blob_basename)
            storage.child(blob.name).download(filename=blob_basename, path=local_file_path)
            move_file(src, dst)
