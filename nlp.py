# -*- coding: utf-8 -*-
"""
"""

import os 
import re
import json
import pickle 
import datetime 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

from tensorflow.keras import Input,Sequential
from tensorflow.keras.utils import plot_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.callbacks import TensorBoard,EarlyStopping
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import LSTM,Dense,Dropout,Embedding,Bidirectional

# Step 1) Data Loading
df = pd.read_csv('https://raw.githubusercontent.com/Ankit152/IMDB-sentiment-analysis/master/IMDB-Dataset.csv')

# Step 2) Data Inspection
df.info()
df.describe().T
df.head()

df.duplicated().sum()
df.isna().sum()

print(df['review'][4])
print(df['review'][10])

# Symbol & HTML Tags need to be removed

# Step 3) Data Cleaning

review = df['review']
sentiment = df['sentiment']

for index, text in enumerate(review):
  # to remove html tags
  # anything with <> will be remove including <>
  # ? to tell re do be greedy so it wont capture everything
  # from the first < to the last > in the document
  review[index] = re.sub('<.*?>','',text)
  review[index] = re.sub('[^a-zA-Z]',' ',text).lower().split()

# Backup the data to save time of loading data from database
review_backup = review.copy()
sentiment_backup = sentiment.copy()

# Step 4) Features Selection
# Step 5) Pre-Processing
vocab_size = 10000
oov_token = '<OOV'
tokenizer = Tokenizer(num_words=vocab_size,oov_token=oov_token)
tokenizer.fit_on_texts(review)
word_index = tokenizer.word_index

print(dict(list(word_index.items())[0:10]))

review_int = tokenizer.texts_to_sequences(review) # Converting text to num

# use median for truncating & padding 
#np.median(length_review)

max_len = np.median([len(review_int[i]) for i in range(len(review_int))])

padded_review = pad_sequences(review_int,maxlen=int(max_len),padding='post',
                              truncating='post')

# For y features
ohe = OneHotEncoder(sparse=False)
sentiment = ohe.fit_transform(np.expand_dims(sentiment,axis=-1))

X_train,X_test,y_train,y_test = train_test_split(padded_review,sentiment,
                                                 test_size=0.3,
                                                 random_state=123)

# Model Development

#X_train = np.expand_dims(X_train,axis=-1) #No need to use on embedding 
#X_test = np.expand_dims(X_test,axis=-1)

input_shape = np.shape(X_train)[1:]
out_dim = 128

model = Sequential()
model.add(Input(shape=(input_shape)))
model.add(Embedding(vocab_size,out_dim))
#model.add(LSTM(128,return_sequences=True))
model.add(Bidirectional(LSTM(128,return_sequences=True)))
model.add(Dropout(0.3))
#model.add(LSTM(128))
model.add(Bidirectional(LSTM(128)))
model.add(Dropout(0.3))
model.add(Dense(2,activation='softmax'))
model.summary()

plot_model(model,show_shapes=(True))

model.compile(optimizer='adam',loss='categorical_crossentropy',
              metrics=['acc'])

#Callback
log_dir = os.path.join("logs_rev", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)

#early_callback = EarlyStopping(monitor='val_loss',patience=5)

hist = model.fit(X_train,y_train,
                 validation_data=(X_test,y_test),
                 epochs=5,
                 callbacks=[tensorboard_callback]) 

# Model evaluation

print(hist.history.keys())

plt.figure()
plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.xlabel('epoch')
plt.legend(['Training Loss', 'Validation Loss'])
plt.show()

plt.figure()
plt.plot(hist.history['acc'])
plt.plot(hist.history['val_acc'])
plt.xlabel('epoch')
plt.legend(['Training Acc', 'Validation Acc'])
plt.show()

print(model.evaluate(X_test,y_test))

#Model Analysis
pred_y = model.predict(X_test)
pred_y = np.argmax(pred_y,axis=1)
true_y = np.argmax(y_test,axis=1)

#print(confusion_matrix(true_y,pred_y))
cr = classification_report(true_y,pred_y)
print(cr)

# Commented out IPython magic to ensure Python compatibility.
# Load the TensorBoard notebook extension
# %load_ext tensorboard
# %tensorboard --logdir logs_rev

# Model Saving

# Tokenizer
TOKENIZER_SAVE_PATH = os.path.join(os.getcwd(),'sample_data','Models',
                                   'tokenizer.json')
token_json = tokenizer.to_json()
with open(TOKENIZER_SAVE_PATH,'w') as file:
  json.dump(token_json,file)

# OHE 
OHE_SAVE_PATH = os.path.join(os.getcwd(),'sample_data','Models','ohe.pkl')
with open(OHE_SAVE_PATH,'wb') as file:
  pickle.dump(ohe,file)

# Model
MODEL_SAVE_PATH = os.path.join(os.getcwd(),'sample_data','Models',
                               'model.h5')
with open(MODEL_SAVE_PATH,'wb') as file:
  pickle.dump(ohe,file)