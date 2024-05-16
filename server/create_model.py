import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from tensorflow.keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, BatchNormalization


def metadata_checker(folder_path):
    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    if len(csv_files) < 2:
        return False 
    df_ref = pd.read_csv(os.path.join(folder_path, csv_files[0]))
    for csv_file in csv_files[1:]:
        df_compare = pd.read_csv(os.path.join(folder_path, csv_file))
        if not df_ref.equals(df_compare):
            return False 
    return True  

def creating_model(input_shape,output_shape,loss_function,activation_function):
    # model = tf.keras.Sequential([
    #     tf.keras.layers.Dense(100, input_shape=input_shape),
    #     tf.keras.layers.BatchNormalization(),
    #     tf.keras.layers.Activation('softmax'),
    #     tf.keras.layers.Dropout(0.2),
    #     tf.keras.layers.Dense(100),
    #     tf.keras.layers.BatchNormalization(),
    #     tf.keras.layers.Activation('softmax'),
    #     tf.keras.layers.Dropout(0.2),
    #     tf.keras.layers.Dense(output_shape,activation=activation_function)
    # ])
    # model.compile(optimizer='adam',
    #               loss=loss_function,
    #               metrics=['accuracy'])
    model = Sequential([
        Dense(100, input_shape=input_shape, kernel_initializer='he_uniform', activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        Dense(100, kernel_initializer='he_uniform', activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        Dense(100, kernel_initializer='he_uniform', activation='relu'),
        BatchNormalization(),
        Dense(1, kernel_initializer='he_uniform', activation='linear'),
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def create_architecture(folder_path,GLOBAL_PATH):
    metadata_file = os.listdir(folder_path)[0]
    metadata_file = os.path.join(folder_path,metadata_file)
    metadata = pd.read_csv(metadata_file)
    output_shape = metadata['Num_Unique_Values'][-1:].values[0]
    input_shape = (int(metadata.shape[0])-1,)
    if output_shape<=1:
        print("no classess to predict")
        return
    elif output_shape==2:
        output_shape = 1
        loss_function = 'binary_crossentropy'
        activation_function = 'sigmoid'
    else:
        output_shape = output_shape
        loss_function = 'sparse_categorical_crossentropy'
        activation_function = 'softmax'

    print("input shape     :", input_shape)
    print("output shape    :", output_shape)
    print("loss function   :", loss_function)
    print("activ. function :", activation_function)

    model = creating_model(input_shape,output_shape,loss_function,activation_function)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") 
    model_name = f'globalZERO_{timestamp}.h5'
    save_path = os.path.join(GLOBAL_PATH,model_name)
    model.save(save_path)



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
    file_info_df = file_info_df[file_info_df['File'] != 'global']
    file_info_df = file_info_df[file_info_df['File'] != 'globalZERO']
    latest_file_indices = file_info_df.loc[file_info_df.groupby('File')['Datetime'].idxmax()]
    latest_paths = latest_file_indices['Absolute Path'].tolist()
    basenames = [os.path.basename(path) for path in latest_paths]
    for basename in basenames:
        print("model name - ",basename)
    print("------------------------------------------------------\n")
    return latest_paths

def aggregating_models(model_paths, GLOBAL_PATH):
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
    model_name = f'global_{timestamp}.h5'
    save_path = os.path.join(GLOBAL_PATH,model_name)
    target_model.save(save_path)
