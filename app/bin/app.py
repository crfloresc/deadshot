from argparse import ArgumentParser
import numpy as np
from app.lib import Measures, load
from prettytable import PrettyTable

class Dex(object):
    def __init__(self, buffer, observer, offset=0.150, debug=False):
        self.table = PrettyTable()
        self.files = buffer
        self.offset = offset
        self.debug = debug
        self.ratingtask = None
        self.assest = None
        self.comp1, self.comp2 = None, None
        
        if observer == 0:
            self.__observer1()
        elif observer == 1:
            self.__observer2()
        else:
            raise NotImplementedError('Only supported 2 observers')
    
    def __observer1(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        ioa, attemps, self.assest, self.comp1, self.comp2 = self.__compare(v1[1], v2[1])
        for v in [[v1[0]] + self.comp1]:
            self.table.add_row(v)
        for v in [[v2[0]] + self.comp2]:
            self.table.add_row(v)
        print('\n{}, attemps: {}'.format(v1[0], attemps))
        self.__test(self.comp1, self.comp2)
    
    def __observer2(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        ioa, attemps, assest, self.comp1, self.comp2 = self.__compare(v2[1], v1[1])
        self.table.add_row([[v1[0]] + self.comp2])
        self.table.add_row([[v2[0]] + self.comp1])
        print('\n{}, attemps: {}'.format(v2[0], attemps))
        self.__test(self.comp1, self.comp2)
    
    def __compare(self, v1, v2):
        if not v1 or not v2:
            return None
        cv1, cv2 = v1.copy(), v2.copy()
        start, end, agree = None, None, 0
        va1 = [0 for v in cv1]
        
        xPlot, yPlot = [], [-1 for v in cv1]
        for i, e1 in enumerate(cv1):
            xPlot.append(round(e1[0]))
            for e2 in cv2:
                diffStart, diffEnd = abs(e1[0] - e2[0]), abs(e1[1] - e2[1])
                if i == 2 and self.debug:
                    print(e1, e2)
                    print(diffStart, diffEnd, diffStart >= 0, diffEnd >= 0, diffEnd <= self.offset, e1[2] == e2[2])
                if diffStart >= 0 and diffStart <= self.offset and diffEnd >= 0 and diffEnd <= self.offset and e1[2] == e2[2]:
                    if self.debug: print(diffStart, diffEnd, e1[2])
                    yPlot[i] = round(e2[0])
                    agree += 1
                    va1[i] += 1
                    cv2.remove(e2)
        return agree/len(cv1)*100, [agree, len(cv1)], va1, xPlot, yPlot
    
    def __test(self, v1, v2):
        from sklearn.metrics import cohen_kappa_score
        from nltk import agreement
        #import pingouin as pg
        #import pandas as pd
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)
        #data = pd.DataFrame(data={'x':x, 'y':y})
        #cronbach = pg.cronbach_alpha(data=data)
    
    def showAssest(self):
        print('Assest: {}'.format(self.assest))
    
    def showComparation(self):
        print('Observer 1: {}\nObserver 2: {}\n'.format(self.comp1, self.comp2))
    
    def showTable(self):
        print(self.table)
    
    def kappa(self, printRes=True):
        kappa = self.ratingtask.kappa()
        if printRes:
            print('Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4)))
        return kappa
    
    def kalpha(self, printRes=True):
        alpha = self.ratingtask.alpha()
        if printRes:
            print('Krippendorff\'s alpha: {}%'.format(round(alpha * 100, 4)))
        return alpha
    
    def spi(self, printRes=True):
        pi = self.ratingtask.pi()
        if printRes:
            print('Scott\'s pi: {}%'.format(round(pi * 100, 4)))
        return pi

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--audiolen', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-s', required=True, default='./sample', help='Sample path')
    return parser.parse_args()

def main():
    args = getArgs()
    print(args)
    
    buffer, bLen = load(path=args.sample)
    if bLen == 2:
        dex = Dex(buffer, observer=0)
        dex.showAssest()
        dex.kappa()
        dex.kalpha()
        dex.spi()
        dex = Dex(buffer, observer=1)
        dex.kappa()
        dex.kalpha()
        dex.spi()
    else:
        raise NotImplementedError('Only accepted two observers')
    '''z = Measures(buffer, metric='label')
    z.showTable()
    z.mdpo()
    z.kappa()
    z.alpha()
    z.pi()'''

if __name__ == '__main__':
    main()