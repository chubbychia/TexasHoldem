import os
import sys
import numpy as np
from collections import defaultdict
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense, Dropout, Activation
import pickle
from keras import metrics
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

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
                model.add(Dense(units=100, activation='relu', input_dim=13)) 
                model.add(Dense(units=50, activation='relu')) 
                model.add(Dense(units=1, activation='sigmoid')) # output layer = 1
                #loss = 'logcosh' -> less impact by outlier
                #binary_crossentropy
                model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

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
                if sum(Player.TRAIN_COST[self.player_name][0][round_seq][:5]) / 5 > 0.3:
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
            y_pred = self.model.predict(np.reshape(np.asarray(data[:13]), (1, 13)))[0][0]
            x_data = np.reshape(np.asarray(data[:13]), (1, 13))
            y_data = np.asarray(data[13:])
            cost = self.model.train_on_batch(x_data, y_data)
            print "Player(%s) Round(%s) train cost: %s, y_data:%s, y_pred:%s" % (self.player_name, i, cost, y_data, y_pred)
            Player.TRAIN_COST[self.player_name][i].append(cost)
            # save the model
            self.save_model()

    def predict(self, predict_data, round_seq):
        try:
            cost = Player.TRAIN_COST[self.player_name][round_seq]
            predict_value = self.model.predict(np.reshape(np.asarray(predict_data), (1, 13)))[0][0]
            print "Player(%s) Round(%s) predict value: %s" % (self.player_name, round_seq, predict_value)
            return predict_value
        except Exception as err:
            print "fails to predict user behavior, because:%s" % err
            return None

def evaluate_classifier(PATH, player):
   
    train_data = []
    if os.path.exists(PATH):
        with open(PATH, 'rb') as f:
            while True:
                try:
                    train_data.append(pickle.load(f))
                except EOFError:
                    break
        #print len(train_data)
    else:
        print 'No such training file %s' % (PATH)

    x_data=[]
    y_data=[]
    x_test=[]
    y_test=[]
    for i, flat in enumerate(train_data):
        for stg in flat:
            if i < len(train_data)/3:
                x_test.append(stg[:13])
                y_test.append(stg[13:])
            else:
                x_data.append(stg[:13])
                y_data.append(stg[13:])
    
    x_data = np.asarray(x_data)  
    y_data = np.asarray(y_data)  
    x_test = np.asarray(x_test)  
    y_test = np.asarray(y_test)  
    
    #Classifier evaluation. Use newlabel_xxxx-xx-xx.pkl data
    player.model.fit(x_data, y_data, validation_split=0.3, epochs=100, batch_size=128,verbose=0)
    scoretrain = player.model.evaluate(x_data, y_data)
    scoretest = player.model.evaluate(x_test, y_test)
    
    # cost=player.model.predict(x_test)
    # for v, y in zip(cost, y_test):
    #     print 'real y: %s pred y: %s' % (y, v)

    print 'TrainingSet loss and accu: %s \nTestingSet loss and accu: %s' % (scoretrain, scoretest)
    #player.save_model() 
   


if __name__ == '__main__':
    player = Player('XXXX')
    if len(sys.argv) < 2: # 1
        print "Usage:", sys.argv[0], "<FILENAME>"
        sys.exit(1)       # 2

    fname = sys.argv[1]
    NEWLABEL_PATH = os.path.join(current_folder, 'training/newlabel_'+ fname + '.pkl')
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
    evaluate_classifier(TRAINDATA_PATH, player)
    
    # regression problem 
    # 
    # train_data = []
    # if os.path.exists(TRAINDATA_PATH):
    #     with open(TRAINDATA_PATH, 'rb') as f:
    #         while True:
    #             try:
    #                 train_data.append(pickle.load(f))
    #             except EOFError:
    #                 break
    #     #print len(train_data)
    # else:
    #     print 'No such training file %s' % (TRAINDATA_PATH)
    
    #player.save_model() 
    
  