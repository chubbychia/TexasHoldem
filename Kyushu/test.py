import pickle
import datetime
import os

if __name__ == '__main__':
    current_folder = os.path.dirname(os.path.abspath(__file__))
    now = datetime.datetime.now()
    TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ str(now)[:10] + '.pkl')
   
    directory = os.path.dirname(TRAINDATA_PATH)

    obj = []
    count = 0
    if os.path.exists(TRAINDATA_PATH):
        with open(TRAINDATA_PATH, 'rb') as f:
            while True:
                try:
                    print pickle.load(f)
                    pickle.load(f)
                    count += 1
                except EOFError:
                    break
        print 'Total training data number: %d' %count    
    else:
        print 'No such training file %s' % (TRAINDATA_PATH)

