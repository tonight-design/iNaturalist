#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 24 22:21:22 2019

@author: jas10022
"""
from __future__ import absolute_import, division, print_function

import tensorflow as tf
import numpy as np
from skimage import transform 
from skimage.color import rgb2gray
import pandas as pd
from PIL import Image
from resizeimage import resizeimage
import pickle


tf.logging.set_verbosity(tf.logging.INFO)

def CNN(train_data, train_labels, eval_data, eval_labels, output_nodes_number, model_name, model_type):
    
    
    if model_type == "lower":
        #tensorflow model function for lowerNN
        def cnn_model(features, labels, mode):
            
            input_layer = tf.reshape(features["x"], [-1, 75, 75,1])
            
            # Convolutional Layer #1
            conv1 = tf.layers.conv2d(
                  inputs=input_layer,
                  filters=32,
                  kernel_size=[5, 5],
                  padding="same",
                  activation=tf.nn.relu)
            
              # Pooling Layer #1
            pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)
            
              # Convolutional Layer #2 and Pooling Layer #2
            conv2 = tf.layers.conv2d(
                  inputs=pool1,
                  filters=64,
                  kernel_size=[5, 5],
                  padding="same",
                  activation=tf.nn.relu)
            pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)
            
              # Dense Layer
            pool2_flat = tf.reshape(pool2, [-1,  18 * 18 * 64])
            dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)
            dropout = tf.layers.dropout(
                  inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
            
              # Logits Layer
            logits = tf.layers.dense(inputs=dropout, units=output_nodes_number)
            
            predicted_classes =tf.argmax(input=logits, axis=1)
            predictions = {
                        'class_ids': predicted_classes[:, tf.newaxis],
                        'probabilities': tf.nn.softmax(logits, name="softmax_tensor"),
                        'logits': logits,
                    }
            export_outputs = {
              'prediction': tf.estimator.export.PredictOutput(predictions)
              }
            if mode == tf.estimator.ModeKeys.PREDICT:  
                return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, export_outputs=export_outputs)
            
              # Calculate Loss (for both TRAIN and EVAL modes)
            loss = tf.losses.sigmoid_cross_entropy(multi_class_labels=labels, logits = logits)
            
              # Configure the Training Op (for TRAIN mode)
            if mode == tf.estimator.ModeKeys.TRAIN:
                optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
                train_op = optimizer.minimize(
                    loss=loss,
                    global_step=tf.train.get_global_step())
                return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)
            
              # Add evaluation metrics (for EVAL mode)
            eval_metric_ops = {
                  "accuracy": tf.metrics.accuracy(
                      labels=labels, predictions=predictions["class_ids"])
            }
            return tf.estimator.EstimatorSpec(
                  mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)
    
    if model_type == "upper":
        #tensorflow model function for upperNN
        def cnn_model(features, labels, mode):
            
            input_layer = tf.reshape(features["x"], [-1, 75, 75, 1])
            
            # Convolutional Layer #1
            conv1 = tf.layers.conv2d(
                  inputs=input_layer,
                  filters=32,
                  kernel_size=[5, 5],
                  padding="same",
                  activation=tf.nn.relu)
            
              # Pooling Layer #1
            pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)
            
              # Convolutional Layer #2 and Pooling Layer #2
            conv2 = tf.layers.conv2d(
                  inputs=pool1,
                  filters=64,
                  kernel_size=[5, 5],
                  padding="same",
                  activation=tf.nn.relu)
            pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)
            
              # Dense Layer
            pool2_flat = tf.reshape(pool2, [-1, 18 * 18 * 64])
            dense = tf.layers.dense(inputs=pool2_flat, units=1024, activation=tf.nn.relu)
            dropout = tf.layers.dropout(
                  inputs=dense, rate=0.4, training=mode == tf.estimator.ModeKeys.TRAIN)
            
              # Logits Layer
            logits = tf.layers.dense(inputs=dropout, units=output_nodes_number)
            
            predicted_classes =tf.argmax(input=logits, axis=1)
            predictions = {
                        'class_ids': predicted_classes[:, tf.newaxis],
                        'probabilities': tf.nn.softmax(logits, name="softmax_tensor"),
                        'logits': logits,
                    }
            export_outputs = {
              'prediction': tf.estimator.export.PredictOutput(predictions)
              }
            if mode == tf.estimator.ModeKeys.PREDICT:  
                return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions, export_outputs=export_outputs)
            
              # Calculate Loss (for both TRAIN and EVAL modes)
            loss = tf.losses.sigmoid_cross_entropy(multi_class_labels=labels, logits = logits)
            
              # Configure the Training Op (for TRAIN mode)
            if mode == tf.estimator.ModeKeys.TRAIN:
                optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)
                train_op = optimizer.minimize(
                    loss=loss,
                    global_step=tf.train.get_global_step())
                return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)
            
              # Add evaluation metrics (for EVAL mode)
            eval_metric_ops = {
                  "accuracy": tf.metrics.accuracy(
                      labels=labels, predictions=predictions["class_ids"])
            }
            return tf.estimator.EstimatorSpec(
                  mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)
        
    def serving_input_receiver_fn():
      inputs = {
        "x": tf.placeholder(tf.float32, [None, 28, 28, 1]),
        }
     
      return tf.estimator.export.ServingInputReceiver(inputs, inputs)
    #This is where we need to load up the data for each group

    # Create the Estimator
    cnn_classifier = tf.estimator.Estimator(
        model_fn=cnn_model, model_dir="/tmp/" + model_name)
    
    # Set up logging for predictions
    tensors_to_log = {"probabilities": "softmax_tensor"}
    
    logging_hook = tf.train.LoggingTensorHook(
        tensors=tensors_to_log, every_n_iter=50)
    
    # Train the model
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": train_data},
        y=train_labels,
        batch_size=100,
        num_epochs=None,
        shuffle=True)
    
    # Train one step and display the probabilties
    cnn_classifier.train(
        input_fn=train_input_fn,
        steps=1,
        hooks=[logging_hook])
    #change steps to 20000
    cnn_classifier.train(input_fn=train_input_fn, steps=10)
    
    # Evaluation of the neural network
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": eval_data},
        y=eval_labels,
        num_epochs=1,
        shuffle=False)
    
    eval_results = cnn_classifier.evaluate(input_fn=eval_input_fn)
    print(eval_results)
    
    #instead of predicting on a test data set we will save the model
    #model_dir = cnn_classifier.export_savedmodel(
       # model_name,
        #serving_input_receiver_fn=serving_input_receiver_fn)
        
    return  cnn_classifier


# example of how to implement
# make sure when we group all the training data that the data is seperated into 
# training and test data to make sure the model is accurate on a new set of data that
# the neural network has not see yet

#this data is already in 28 x 28 format so it did not need to resize the pictures
#also this data is also gray scaled already so we dont need to apply it to this either
#retrieving the data
((train_data, train_labels),
 (eval_data, eval_labels)) = tf.keras.datasets.mnist.load_data()

train_data = train_data/np.float32(255)
train_labels = train_labels.astype(np.int32)  # not required

eval_data = eval_data/np.float32(255)
eval_labels = eval_labels.astype(np.int32)  # not required

test_data = pd.read_csv("test.csv")

test_data = test_data.values.reshape((-1, 28, 28, 1))
test_data = test_data.astype('float32') /255

#this line creates and trains the entire model the inputs are below and must be given 
# an output number of nodes, for this there is 10
model_location = CNN(train_data,train_labels,eval_data,eval_labels,10, "save", "lower")

#this is how we can load a specific model and then predict on that model
sess = tf.Session()

init=tf.global_variables_initializer()

sess.run(init)

tf.saved_model.loader.load(sess, [tf.saved_model.tag_constants.SERVING], model_location)
predictor  = tf.contrib.predictor.from_saved_model(model_location)

#Prediction call
predictions = predictor({'x':test_data})

pred_class = np.array([p['class_ids'] for p in predictions]).squeeze()
print(pred_class)

#once the model has been created we can predict on a new set of data the output
#class_ids is the column of the predictions
y_classes = list(pred_class)

y = pd.DataFrame.from_dict(y_classes)

true_prediction = y.class_ids.astype(np.int32)

output1 = pd.DataFrame({'ImageId':range(1,28001),'Label':true_prediction})

output1.to_csv(r'/Users/jas10022/Documents/GitHub/iNaturalist/output1.csv', index=False)


#this is how we can create a data file with all the images in a 1,75,75 shape 
#modify the for loop in order to use it and the allImages are all the images file names
#update the .open method to the directory of the train images then the + im
# the Images variable will contain all the picures each resized to 75 by 75

upperNN = pd.read_csv('upperNN .csv')

file_names = upperNN['File_Name']
file_names = file_names[4999:265213]

Images = np.empty([1,75, 75])
i = 0
a = 0
for im in file_names:
        if i >= 5000:
            Images = Images[1:]
            output = open(str(a)+'.pkl', 'wb')
            pickle.dump(Images, output)
            output.close()            
            Images = np.empty([1,75, 75])
            a += 1
            i = 0
        img = Image.open(im, 'r').convert('LA')
        cover = resizeimage.resize_cover(img, [75, 75], validate=False)
        np_im = np.array(cover)
    
        pix_val_flat = np.array([x for sets in np_im for x in sets])
        train_data = pix_val_flat[:,0].astype('float64') /255
        train_data = np.resize(train_data, (1,75,75))
        
        Images = np.concatenate((Images,train_data))
        i += 1
        print(i)
        
Images = np.empty([1,75, 75])
i = 0
a = 54

for num in range(59,65):
    if i == 5:
        Images = Images[1:]
        output = open(str(a)+'.pkl', 'wb')
        pickle.dump(Images, output)
        output.close()            
        Images = np.empty([1,75, 75])
        i = 0
        a += 1
    pkl_file = open(str(num) + '.pkl', 'rb')

    data1 = pickle.load(pkl_file)

    Images = np.concatenate((Images,data1))
    
    pkl_file.close()
    print(i)
    i += 1
    
#how to read 3d array

pkl_file = open('54.pkl', 'rb')
pkl_file1 = open('55.pkl', 'rb')
pkl_file2 = open('56.pkl', 'rb')
pkl_file3 = open('57.pkl', 'rb')
pkl_file4 = open('58.pkl', 'rb')
pkl_file5 = open('58.pkl', 'rb')
pkl_file6 = open('60.pkl', 'rb')
pkl_file7 = open('61.pkl', 'rb')
pkl_file8 = open('62.pkl', 'rb')
pkl_file9 = open('63.pkl', 'rb')
pkl_file10 = open('64.pkl', 'rb')

data1 = pickle.load(pkl_file)
data2 = pickle.load(pkl_file1)
data3 = pickle.load(pkl_file2)
data4 = pickle.load(pkl_file3)
data5 = pickle.load(pkl_file4)
data6 = pickle.load(pkl_file5)
data7 = pickle.load(pkl_file6)
data8 = pickle.load(pkl_file7)
data9 = pickle.load(pkl_file8)
data10 = pickle.load(pkl_file9)
data11 = pickle.load(pkl_file10)

pkl_file.close()
    
Images = np.empty([1,75, 75])
i = 0
for num in range(0,1010):
    current = pd.read_csv('/Users/jas10022/Documents/GitHub/iNaturalist/Data/Lower_NN_Data/' + str(num) + '.csv')
    for id in current['ImageId']:
        file_num = int(id / 25000)
        index = id - (file_num * 25000)
        if file_num == 0:
            im = data1[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 1:
            im = data2[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 2:
            im = data3[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 3:
            im = data4[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 4:
            im = data5[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 5:
            im = data6[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 6:
            im = data7[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 7:
            im = data8[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 8:
            im = data9[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 9:
            im = data10[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
        if file_num == 10:
            im = data11[index].reshape(1,75,75)
            Images = np.concatenate((Images,im))
    Images = Images[1:]
    output = open(str(i) + '.pkl', 'wb')
    pickle.dump(Images, output)
    output.close()
    Images = np.empty([1,75, 75])
    print(i)
    i += 1

#to look at pictures
import matplotlib.pyplot as plt

plt.imshow(Images[2], cmap="gray")
plt.subplots_adjust(wspace=0.5)
plt.show()

#how to save 3d array
output = open('data.pkl', 'wb')
pickle.dump(Images, output)
output.close()

#Bellow is how to train the UpperNN model for the catagories, I gave the example for the Kingdom

#this reads the first file of image data
#each of the files have 25000 images except for the last one
pkl_file = open('54.pkl', 'rb')
data1 = pickle.load(pkl_file)
pkl_file.close()

#This reads the Label data and extracts the specific values from the file read above
upperNN = pd.read_csv('Data/upperNN.csv')
Labels = upperNN['Kingdom'][0:25000]

#this splits the data into training and val data for the model and also reshapes the label data
from sklearn.model_selection import train_test_split
X_train, X_val, y_train, y_val = train_test_split(data1, Labels, test_size = 0.05, random_state = 0)
y_train = np.asarray(y_train).reshape((-1,1))
y_val = np.asarray(y_val).reshape((-1,1))

#this will run and create the model in the local working directory
model_location = CNN(X_train,y_train,X_val,y_val,1, "Kingdom_Model", "upper")

col_names = ['class', 'family','kingdom','order','phylum']

for cat in col_names:
    upperNN = pd.read_csv('Data/upperNN.csv')
    Labels = upperNN[cat][0:25000]
    
    #this splits the data into training and val data for the model and also reshapes the label data
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(data1, Labels, test_size = 0.05, random_state = 0)
    y_train = np.asarray(y_train).reshape((-1,1))
    y_val = np.asarray(y_val).reshape((-1,1))
    
    #this will run and create the model in the local working directory
    model_location = CNN(X_train,y_train,X_val,y_val,1, "Kingdom_Model", "upper")
