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
    PATH = os.path.join(current_folder, 'training/'+ fname + '.pkl')
    #PATH = os.path.join(current_folder, 'training/newlabel_'+ fname + '.pkl')
   
    directory = os.path.dirname(PATH)

    obj = []
    count = 0
    if os.path.exists(PATH):
        with open(PATH, 'rb') as f:
            while True:
                try:
                    print pickle.load(f)
                    count += 1
                except EOFError:
                    break
        print 'Total training data number: %d' %count    
    else:
        print 'No such training file %s' % (PATH)

