import os
import numpy as np
from collections import defaultdict
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense, Dropout, Activation
from keras.optimizers import RMSprop
import pickle
from keras import metrics

current_folder = os.path.dirname(os.path.abspath(__file__))
# HDF5 file, you have to pip3 install h5py if don't have it
MODEL_PATH = os.path.join(current_folder, "model/%s/behavior.h5")


class Player(object):
    PLAYER_MODEL = {}
    TRAIN_COST = defaultdict(lambda: defaultdict(list))

    def __init__(self, player_name):
        self.player_name = player_name
        self.is_known_guy = False

        if player_name not in Player.PLAYER_MODEL:
            if os.path.exists(self.model_path):
                model = load_model(self.model_path)
                self.is_known_guy = True
            else: 
                model = Sequential()
                model.add(Dense(units=100, activation='relu', input_dim=37)) # first layer = 37 dim; Hidden layer = 100 dim
                model.add(Dense(units=1, activation='sigmoid')) # output layer = 1
                #loss = 'logcosh' -> less impact by outlier
                model.compile(loss='logcosh', optimizer='adam')

            Player.PLAYER_MODEL[player_name] = model
        else:
            self.is_known_guy = True

    @property
    def model(self):
        return Player.PLAYER_MODEL[self.player_name]

    @property
    def model_path(self):
        return MODEL_PATH % self.player_name

    @property
    def is_bluffing_guy(self):
        for round_seq in (0, 1, 2, 3):
            if self.is_known_guy or len(Player.TRAIN_COST[self.player_name][round_seq]) > 10:
                if sum(Player.TRAIN_COST[self.player_name][round_seq][:5]) / 5 > 0.3:
                    return True
                return False
        return None

    def save_model(self):
        dir_name = os.path.dirname(self.model_path)
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        self.model.save(self.model_path)

    def train(self, train_data):
        for i, data in enumerate(train_data):
            y_pred = self.model.predict(np.reshape(np.asarray(data[:37]), (1, 37)))[0][0]
            x_data = np.reshape(np.asarray(data[:37]), (1, 37))
            y_data = np.asarray(data[37:])
            cost = self.model.train_on_batch(x_data, y_data)
            print "Player(%s) Round(%s) train cost: %s, y_data:%s, y_pred:%s" % (self.player_name, i, cost, y_data, y_pred)
            Player.TRAIN_COST[self.player_name][i].append(cost)
            # save the model
            self.save_model()

    def predict(self, predict_data, round_seq):
        try:
            cost = Player.TRAIN_COST[self.player_name][round_seq]
            predict_value = self.model.predict(np.reshape(np.asarray(predict_data), (1, 37)))[0][0]
            print "Player(%s) Round(%s) predict value: %s" % (self.player_name, round_seq, predict_value)
            return predict_value
        except Exception as err:
            print "fails to predict user behavior, because:%s" % err
            return None


if __name__ == '__main__':
    #train_data = [[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7616892911010558], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.32238667900092505], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9956521739130435], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9956521739130435]]
    player = Player('XXXX')
    fname = '2018-07-26'
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
    train_data = []
    if os.path.exists(TRAINDATA_PATH):
        with open(TRAINDATA_PATH, 'rb') as f:
            while True:
                try:
                    train_data.append(pickle.load(f))
                except EOFError:
                    break
        #print len(train_data)
    else:
        print 'No such training file %s' % (TRAINDATA_PATH)

    x_data=[]
    y_data=[]
    x_test=[]
    y_test=[]
    for i, flat in enumerate(train_data):
        for stg in flat:
            if i < len(train_data)/3:
                x_test.append(stg[:37])
                y_test.append(stg[37:])
            else:
                x_data.append(stg[:37])
                y_data.append(stg[37:])
    
    x_data = np.asarray(x_data)  
    y_data = np.asarray(y_data)  
    x_test = np.asarray(x_test)  
    y_test = np.asarray(y_test)  
    
    history = player.model.fit(x_data, y_data, validation_split=0.33, epochs=150, batch_size=10, verbose=0)
    score = player.model.evaluate(x_test, y_test, batch_size=32)
    
    print score
   
    # list all data in history
    #print(history.history.keys())
   


    # a.predict([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1)
