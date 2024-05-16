import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from keras.callbacks import EarlyStopping
earlystop = EarlyStopping(monitor='val_loss', min_delta=0.005, patience=200, verbose=1, mode='min')

def get_latest_models(root_dir):
    file_info = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            basename = os.path.splitext(filename)[0].split('_')
            if len(basename) == 3:
                edge_name = basename[0]
                datestamp = basename[1]
                timestamp = basename[2]
                if len(datestamp) == 10 and len(timestamp) == 8 and datestamp[4] == '-' and timestamp[2] == '-':
                    file_info.append({'File': edge_name, 'Date': datestamp, 'Time': timestamp, 'Absolute Path': file_path})
    file_info_df = pd.DataFrame(file_info)
    file_info_df['Datetime'] = pd.to_datetime(file_info_df['Date'] + ' ' + file_info_df['Time'], format='%Y-%m-%d %H-%M-%S')
    file_info_df = file_info_df[file_info_df['File'] != 'globalZERO']
    latest_file_indices = file_info_df.loc[file_info_df.groupby('File')['Datetime'].idxmax()]
    latest_paths = latest_file_indices['Absolute Path'].tolist()
    basenames = [os.path.basename(path) for path in latest_paths]
    for basename in basenames:
        print("model name - ",basename)
    print("------------------------------------------------------\n")
    return latest_paths


def aggregating_models(model_paths, GLOBAL_PATH,alias):
    models = [load_model(path) for path in model_paths]
    num_models = len(models)
    average_weights = []
    for layer_idx in range(len(models[0].layers)):
        if models[0].layers[layer_idx].get_weights():
            layer_weights = [model.layers[layer_idx].get_weights() for model in models]
            avg_layer_weights = [np.mean(w, axis=0) for w in zip(*layer_weights)]
            average_weights.append(avg_layer_weights)
        else:
            average_weights.append(None)
    target_model = load_model(model_paths[0])
    for layer_idx, avg_weights in enumerate(average_weights):
        if avg_weights:
            target_model.layers[layer_idx].set_weights(avg_weights)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    model_name = f'{alias}_{timestamp}.h5'
    save_path = os.path.join(GLOBAL_PATH,model_name)
    target_model.save(save_path)


def load_models_from_folder(folder_path):
    models = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.h5'):
            model_name = os.path.splitext(file_name)[0]
            model_path = os.path.join(folder_path, file_name)
            models[model_name] = load_model(model_path)
    return models

# Function to evaluate models on a dataset and get performance metrics
def evaluate_models(models, X_test, y_test):
    metrics = {}
    for model_name, model in models.items():
        # test_loss = model.evaluate(X_test, y_test)
        y_pred_probs = model.predict(X_test)
        # y_pred = y_pred_probs.argmax(axis=1)
        y_pred = y_pred_probs.round()
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        metrics[model_name] = {'Accuracy': accuracy, 'Precision': precision, 'Recall': recall, 'F1 Score': f1}
        # metrics[model_name] = {'Test Loss' : test_loss}
    return metrics

def save_metrics_to_csv(metrics, csv_file):
    df = pd.DataFrame.from_dict(metrics, orient='index')
    df.index.name = 'Model Name'
    df.to_csv(csv_file)

def test_model(folder_path,csv_file,dataset_path):
    df = pd.read_csv(dataset_path)
    X = df.iloc[:, :-1] 
    y = df.iloc[:, -1]   
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    models = load_models_from_folder(folder_path)
    metrics = evaluate_models(models, X_test, y_test)
    save_metrics_to_csv(metrics, csv_file)


def model_to_train(root_dir,model_name):
    file_info = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            basename = os.path.splitext(filename)[0].split('_')
            if len(basename) == 3:
                edge_name = basename[0]
                datestamp = basename[1]
                timestamp = basename[2]
                if len(datestamp) == 10 and len(timestamp) == 8 and datestamp[4] == '-' and timestamp[2] == '-' and edge_name == model_name:
                    file_info.append({'File': edge_name, 'Date': datestamp, 'Time': timestamp, 'Absolute Path': file_path})
    file_info_df = pd.DataFrame(file_info)
    file_info_df['Datetime'] = pd.to_datetime(file_info_df['Date'] + ' ' + file_info_df['Time'], format='%Y-%m-%d %H-%M-%S')
    latest_file_indices = file_info_df.loc[file_info_df.groupby('File')['Datetime'].idxmax()]
    latest_paths = latest_file_indices['Absolute Path'].tolist()
    basenames = [os.path.basename(path) for path in latest_paths]
    for basename in basenames:
        print("model name - ",basename)
    print("------------------------------------------------------\n")
    return latest_paths

def train_model(model_path,alias,dataset_path,GLOBAL_PATH):
    df = pd.read_csv(dataset_path)
    X = df.iloc[:, :-1] 
    y = df.iloc[:, -1]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = load_model(model_path[0])  
    print(model.summary())
    
    model.compile(optimizer="adam",
                  loss='binary_crossentropy',  
                  metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2)
    # model.compile(optimizer='adam', loss='mean_squared_error')
    # model.fit(X_train, y_train, epochs=2000, batch_size=256, verbose=0, validation_data=(X_test, y_test), callbacks=[earlystop])

    models={}
    models["performance metrics"] = model
    metric = evaluate_models(models, X_test, y_test)
    print("\n",metric,"\n")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    model_name = f'{alias}_{timestamp}.h5'
    save_path = os.path.join(GLOBAL_PATH,model_name)
    model.save(save_path)