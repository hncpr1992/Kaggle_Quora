# The code is modified from https://www.kaggle.com/lystdo/lb-0-18-lstm-with-glove-and-magic-features
# Great Appreciation

#########################################
# import packages
import os
import re
import csv
import codecs
import numpy as np
import pandas as pd

from string import punctuation
from collections import defaultdict

from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, LSTM, Embedding, Dropout, Activation
from keras.layers.merge import concatenate
from keras.models import Model
from keras.layers.normalization import BatchNormalization
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers.convolutional import Conv1D
from keras.layers.pooling import GlobalAveragePooling1D

from sklearn.preprocessing import StandardScaler

import sys
#########################################



#########################################
# define constants and parameters
INPUT_DIR = '../input/'
EMBEDDING_FILE = INPUT_DIR + 'glove.840B.300d.txt'
TRAIN_DATA_FILE = INPUT_DIR + 'train.csv'
TEST_DATA_FILE = INPUT_DIR + 'test.csv'
MAX_SEQUENCE_LENGTH = 60
MAX_NB_WORDS = 200000
EMBEDDING_DIM = 300
VALIDATION_SPLIT_RATIO = 0.1

num_lstm = np.random.randint(175, 275)
num_dense1 = np.random.randint(200, 250)
num_dense2 = np.random.randint(150, 200)
rate_drop_lstm = 0.15 + np.random.rand() * 0.25
rate_drop_dense = 0.15 + np.random.rand() * 0.25

act = 'relu'
re_weight = True # whether to re-weight classes to fit the 17.5% share in test set

STAMP = 'lstm_%d_%d %d_%.2f_%.2f'%(num_lstm, num_dense1, num_dense2, rate_drop_lstm, \
        rate_drop_dense)
#########################################



#########################################
# Create word embedding dictionary from 'glove.840B.300d.txt'
print('Create word embedding dictionary')

embeddings_index = {}
f = open(EMBEDDING_FILE)
count = 0

for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

print('Found %d word vectors of glove.' % len(embeddings_index))
#########################################



#########################################
# process texts in datasets
print('Processing text dataset')

def text_to_wordlist(text, remove_stopwords=False, stem_words=False):
	"""
	Function from https://www.kaggle.com/currie32/quora-question-pairs/the-importance-of-cleaning-text
	"""

    # Clean the text, with the option to remove stopwords and to stem words.
    # Convert words to lower case and split them
    text = text.lower().split()

    # Optionally, remove stop words
    if remove_stopwords:
        stops = set(stopwords.words("english"))
        text = [w for w in text if not w in stops]
    
    text = " ".join(text)

    # Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "cannot ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    
    # Optionally, shorten words to their stems
    if stem_words:
        text = text.split()
        stemmer = SnowballStemmer('english')
        stemmed_words = [stemmer.stem(word) for word in text]
        text = " ".join(stemmed_words)
    
    # Return a list of words
    return(text)

# load data and process with text_to_wordlist
texts_1 = [] 
texts_2 = []
labels = []
with codecs.open(TRAIN_DATA_FILE, encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=',')
    header = next(reader)
    for values in reader:
        texts_1.append(text_to_wordlist(values[3]))
        texts_2.append(text_to_wordlist(values[4]))
        labels.append(int(values[5]))
print('Found %s texts in train.csv' % len(texts_1))

test_texts_1 = []
test_texts_2 = []
test_ids = []
with codecs.open(TEST_DATA_FILE, encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=',')
    header = next(reader)
    for values in reader:
        test_texts_1.append(text_to_wordlist(values[1]))
        test_texts_2.append(text_to_wordlist(values[2]))
        test_ids.append(values[0])
print('Found %s texts in test.csv' % len(test_texts_1))

# Tokenize words in all sentences
tokenizer = Tokenizer(num_words=MAX_NB_WORDS)
tokenizer.fit_on_texts(texts_1 + texts_2 + test_texts_1 + test_texts_2)

sequences_1 = tokenizer.texts_to_sequences(texts_1)
sequences_2 = tokenizer.texts_to_sequences(texts_2)
test_sequences_1 = tokenizer.texts_to_sequences(test_texts_1)
test_sequences_2 = tokenizer.texts_to_sequences(test_texts_2)

word_index = tokenizer.word_index
print('Found %s unique tokens' % len(word_index))

# pad all train with MAX_SEQUENCE_LENGTH
data_1 = pad_sequences(sequences_1, maxlen=MAX_SEQUENCE_LENGTH)
data_2 = pad_sequences(sequences_2, maxlen=MAX_SEQUENCE_LENGTH)
labels = np.array(labels)
print('Shape of data tensor:', data_1.shape)
print('Shape of label tensor:', labels.shape)

# pad all test with MAX_SEQUENCE_LENGTH
test_data_1 = pad_sequences(test_sequences_1, maxlen=MAX_SEQUENCE_LENGTH)
test_data_2 = pad_sequences(test_sequences_2, maxlen=MAX_SEQUENCE_LENGTH)
test_ids = np.array(test_ids)
########################################



########################################
# leaky features
train_df = pd.read_csv(TRAIN_DATA_FILE)
test_df = pd.read_csv(TEST_DATA_FILE)

ques = pd.concat([train_df[['question1', 'question2']], \
        test_df[['question1', 'question2']]], axis=0).reset_index(drop='index')
q_dict = defaultdict(set)
for i in range(ques.shape[0]):
        q_dict[ques.question1[i]].add(ques.question2[i])
        q_dict[ques.question2[i]].add(ques.question1[i])

def q1_freq(row):
    return(len(q_dict[row['question1']]))
    
def q2_freq(row):
    return(len(q_dict[row['question2']]))
    
def q1_q2_intersect(row):
    return(len(set(q_dict[row['question1']]).intersection(set(q_dict[row['question2']]))))

train_df['q1_q2_intersect'] = train_df.apply(q1_q2_intersect, axis=1, raw=True)
train_df['q1_freq'] = train_df.apply(q1_freq, axis=1, raw=True)
train_df['q2_freq'] = train_df.apply(q2_freq, axis=1, raw=True)

test_df['q1_q2_intersect'] = test_df.apply(q1_q2_intersect, axis=1, raw=True)
test_df['q1_freq'] = test_df.apply(q1_freq, axis=1, raw=True)
test_df['q2_freq'] = test_df.apply(q2_freq, axis=1, raw=True)

leaks = train_df[['q1_q2_intersect', 'q1_freq', 'q2_freq']]
test_leaks = test_df[['q1_q2_intersect', 'q1_freq', 'q2_freq']]

ss = StandardScaler()
ss.fit(np.vstack((leaks, test_leaks)))
leaks = ss.transform(leaks)
test_leaks = ss.transform(test_leaks)
#########################################



#########################################
# Create embedding matrix for embedding layer
print('Preparing embedding matrix')

nb_words = min(MAX_NB_WORDS, len(word_index))+1

embedding_matrix = np.zeros((nb_words, EMBEDDING_DIM))
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector
print('Null word embeddings: %d' % np.sum(np.sum(embedding_matrix, axis=1) == 0))
#########################################



#########################################
# Train Validation split
np.random.seed(1992)
perm = np.random.permutation(len(data_1))
idx_train = perm[:int(len(data_1)*(1-VALIDATION_SPLIT))]
idx_val = perm[int(len(data_1)*(1-VALIDATION_SPLIT)):]

data_1_train = np.vstack((data_1[idx_train], data_2[idx_train]))
data_2_train = np.vstack((data_2[idx_train], data_1[idx_train]))
leaks_train = np.vstack((leaks[idx_train], leaks[idx_train]))
labels_train = np.concatenate((labels[idx_train], labels[idx_train]))

data_1_val = np.vstack((data_1[idx_val], data_2[idx_val]))
data_2_val = np.vstack((data_2[idx_val], data_1[idx_val]))
leaks_val = np.vstack((leaks[idx_val], leaks[idx_val]))
labels_val = np.concatenate((labels[idx_val], labels[idx_val]))

weight_val = np.ones(len(labels_val))
if re_weight:
    weight_val *= 0.472001959
    weight_val[labels_val==0] = 1.309028344
#########################################



#########################################
# This part come from https://www.kaggle.com/rethfro/1d-cnn-single-model-score-0-14-0-16-or-0-23
# The embedding layer containing the word vectors
emb_layer = Embedding(
    input_dim=embedding_matrix.shape[0],
    output_dim=embedding_matrix.shape[1],
    weights=[embedding_matrix],
    input_length=MAX_SEQUENCE_LENGTH,
    trainable=False
)

# 1D convolutions that can iterate over the word vectors
conv1 = Conv1D(filters=128, kernel_size=1, padding='same', activation='relu')
conv2 = Conv1D(filters=128, kernel_size=2, padding='same', activation='relu')
conv3 = Conv1D(filters=128, kernel_size=3, padding='same', activation='relu')
conv4 = Conv1D(filters=128, kernel_size=4, padding='same', activation='relu')
conv5 = Conv1D(filters=32, kernel_size=5, padding='same', activation='relu')
conv6 = Conv1D(filters=32, kernel_size=6, padding='same', activation='relu')

# Define inputs
seq1 = Input(shape=(MAX_SEQUENCE_LENGTH,))
seq2 = Input(shape=(MAX_SEQUENCE_LENGTH,))

# Run inputs through embedding
emb1 = emb_layer(seq1)
emb2 = emb_layer(seq2)

# Run through CONV + GAP layers
conv1a = conv1(emb1)
glob1a = GlobalAveragePooling1D()(conv1a)
conv1b = conv1(emb2)
glob1b = GlobalAveragePooling1D()(conv1b)

conv2a = conv2(emb1)
glob2a = GlobalAveragePooling1D()(conv2a)
conv2b = conv2(emb2)
glob2b = GlobalAveragePooling1D()(conv2b)

conv3a = conv3(emb1)
glob3a = GlobalAveragePooling1D()(conv3a)
conv3b = conv3(emb2)
glob3b = GlobalAveragePooling1D()(conv3b)

conv4a = conv4(emb1)
glob4a = GlobalAveragePooling1D()(conv4a)
conv4b = conv4(emb2)
glob4b = GlobalAveragePooling1D()(conv4b)

conv5a = conv5(emb1)
glob5a = GlobalAveragePooling1D()(conv5a)
conv5b = conv5(emb2)
glob5b = GlobalAveragePooling1D()(conv5b)

conv6a = conv6(emb1)
glob6a = GlobalAveragePooling1D()(conv6a)
conv6b = conv6(emb2)
glob6b = GlobalAveragePooling1D()(conv6b)

mergea = concatenate([glob1a, glob2a, glob3a, glob4a, glob5a, glob6a])
mergeb = concatenate([glob1b, glob2b, glob3b, glob4b, glob5b, glob6b])

# We take the explicit absolute difference between the two sentences
# Furthermore we take the multiply different entries to get a different measure of equalness
diff = Lambda(lambda x: K.abs(x[0] - x[1]), output_shape=(4 * 128 + 2*32,))([mergea, mergeb])
mul = Lambda(lambda x: x[0] * x[1], output_shape=(4 * 128 + 2*32,))([mergea, mergeb])

# Add the magic features
magic_input = Input(shape=(leaks.shape[1],))
magic_dense = BatchNormalization()(magic_input)
magic_dense = Dense(64, activation='relu')(magic_dense)

# Add the distance features (these are now TFIDF (character and word), Fuzzy matching, 
# nb char 1 and 2, word mover distance and skew/kurtosis of the sentence vector)
# distance_input = Input(shape=(20,))
# distance_dense = BatchNormalization()(distance_input)
# distance_dense = Dense(128, activation='relu')(distance_dense)

# Merge the Magic and distance features with the difference layer
# merge = concatenate([diff, mul, magic_dense, distance_dense])
merge = concatenate([diff, mul, magic_dense])

# The MLP that determines the outcome
x = Dropout(0.2)(merge)
x = BatchNormalization()(x)
x = Dense(300, activation='relu')(x)

x = Dropout(0.2)(x)
x = BatchNormalization()(x)
pred = Dense(1, activation='sigmoid')(x)
#########################################



#########################################
# add class weight
if re_weight:
    class_weight = {0: 1.309028344, 1: 0.472001959}
else:
    class_weight = None
#########################################



#########################################
# train the model
model = Model(inputs=[seq1, seq2, leaks], outputs=pred)
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['acc'])
print(STAMP)

# set early stopping (large patience should be usefule)
early_stopping =EarlyStopping(monitor='val_loss', patience=20)
bst_model_path = STAMP + '.h5' 
model_checkpoint = ModelCheckpoint(bst_model_path, save_best_only=True, save_weights_only=True)

hist = model.fit([data_1_train, data_2_train, leaks_train], labels_train, \
        validation_data=([data_1_val, data_2_val, leaks_val], labels_val, weight_val), \
        epochs=200, batch_size=2048, shuffle=True, \
        class_weight=class_weight, callbacks=[early_stopping, model_checkpoint])

model.load_weights(bst_model_path) # sotre model parameters in .h5 file
bst_val_score = min(hist.history['val_loss'])
#########################################



########################################
# make the submission
print('Start making the submission before fine-tuning')

preds = model.predict([test_data_1, test_data_2, test_leaks], batch_size=8192, verbose=1)
preds += model.predict([test_data_2, test_data_1, test_leaks], batch_size=8192, verbose=1)
preds /= 2

submission = pd.DataFrame({'test_id':test_ids, 'is_duplicate':preds.ravel()})
submission.to_csv('%.4f_'%(bst_val_score)+STAMP+'.csv', index=False)
#########################################