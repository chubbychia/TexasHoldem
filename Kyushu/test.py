import pickle
import datetime
import os
import sys

if __name__ == '__main__':
    
    if len(sys.argv) < 2: # 1
        print "Usage:", sys.argv[0], "<FILENAME>"
        sys.exit(1)       # 2

    fname = sys.argv[1]
   
    current_folder = os.path.dirname(os.path.abspath(__file__))
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
   
    directory = os.path.dirname(TRAINDATA_PATH)

    obj = []
    count = 0
    if os.path.exists(TRAINDATA_PATH):
        with open(TRAINDATA_PATH, 'rb') as f:
            while True:
                try:
                    print pickle.load(f)
                    count += 1
                except EOFError:
                    break
        print 'Total training data number: %d' %count    
    else:
        print 'No such training file %s' % (TRAINDATA_PATH)

