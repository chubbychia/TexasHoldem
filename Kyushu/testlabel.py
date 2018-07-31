import os
import numpy as np
import sys
import pickle

current_folder = os.path.dirname(os.path.abspath(__file__))



def save_append_training_data(behavior,date):
        TRAINDATA_PATH = os.path.join(current_folder, 'training/newlabel_'+ date +'.pkl')
        directory = os.path.dirname(TRAINDATA_PATH)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        if os.path.exists(directory):
            with open(TRAINDATA_PATH,'a') as f:
                # Pickle dictionary using protocol 0.
                #print '*** Save %s' %behavior
                pickle.dump(behavior, f)


def load_training_data(fname):
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
    obj = []
    if os.path.exists(TRAINDATA_PATH):
        with open(TRAINDATA_PATH, 'rb') as f:
            while True:
                try:
                    obj.append(pickle.load(f))
                except EOFError:
                    break
        #print obj
    else:
        print 'No such training file %s' % (TRAINDATA_PATH)
    return obj



def main():
   
    if len(sys.argv) < 2: # 1
        print "Usage:", sys.argv[0], "<FILENAME>"
        sys.exit(1)       # 2

    fname = sys.argv[1]
    train_data = []
    new_train_data=[]
    train_data = load_training_data(fname)
    for flat in train_data:
        new_train_data=[]
        for stg in flat:
            if int(stg[37]) == 1:
                new_label_data = stg[:37] + [1]
            else:
                new_label_data = stg[:37] + [0]
            new_train_data.append(new_label_data)
        save_append_training_data(new_train_data,fname)

if __name__ == '__main__':
    main()