import os
import numpy as np
from collections import defaultdict
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense

current_folder = os.path.dirname(os.path.abspath(__file__))
# HDF5 file, you have to pip3 install h5py if don't have it
MODEL_PATH = os.path.join(current_folder, "./model/%s/behavior.h5")


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
                model.add(Dense(units=50, input_dim=25))
                model.add(Dense(units=1,))
                model.compile(loss='mse', optimizer='sgd')

            Player.PLAYER_MODEL[player_name] = model

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
            y_pred = self.model.predict(np.reshape(np.asarray(data[:25]), (1, 25)))[0][0]
            x_data = np.reshape(np.asarray(data[:25]), (1, 25))
            y_data = np.asarray(data[25:])
            cost = self.model.train_on_batch(x_data, y_data)
            print "Player(%s) Round(%s) train cost: %s, y_data:%s, y_pred:%s" % (self.player_name, i, cost, y_data, y_pred)
            Player.TRAIN_COST[self.player_name][i].append(cost)
            # save the model
            self.save_model()

    def predict(self, predict_data, round_seq):
        try:
            cost = Player.TRAIN_COST[self.player_name][round_seq]
            predict_value = self.model.predict(np.reshape(np.asarray(predict_data), (1, 25)))[0][0]
            print "Player(%s) Round(%s) predict value: %s" % (self.player_name, round_seq, predict_value)
            return predict_value
        except Exception as err:
            print "fails to predict user behavior, because:%s" % err
            return None


if __name__ == '__main__':
    train_data = [[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7616892911010558], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.32238667900092505], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9956521739130435], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9956521739130435]]

    a = Player('austin')
    print a.model_path
    # a.train(train_data)
    # a.predict([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1)
