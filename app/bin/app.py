from argparse import ArgumentParser
import numpy as np
import seaborn as sns
import pandas as pd
from app.lib import Measures, load

class Dex(object):
    def __init__(self, buffer, src=None, offset=0.150, debug=False):
        self.files = buffer
        self.offset = offset
        self.debug = debug
        self.ratingtask = None
        self.assest = None
        self.oName = None
        self.test = {}
        self.src = src
        # For processing
        self.data = {}
        self.agreements = {}
        self.attemps = {}
        # For chart
        self.colormap = {}
        self.observermap = {}
        self.markermap = {}

        self.__setupDicts()
        self.__process()

    def __setupDicts(self):
        val = 0.40
        markers = ['circle', 'circle'] # ['hex', 'triangle']
        self.colormap = {'VF': 'red', 'N1': 'green', 'M1': 'blue', 'AM': 'purple', 'R': 'black'}
        self.pcolormap = {'VF': 'firebrick', 'N1': 'darkolivegreen', 'M1': 'royalblue', 'AM': 'plum', 'R': 'darkslategray'}
        for k, v in self.files.items():
            val = val - 0.05
            self.data[k] = []
            self.agreements[k] = []
            self.attemps[k] = []
            self.observermap[k] = val
            self.markermap[k] = markers[0]
            del markers[0]

    def __locate(self, lsts, x1, x2, x3):
        from bisect import bisect_left, bisect_right, bisect
        print('Start:', 'x1:', x1, 'x2:', x2, 'x3:', x3, 'diff:', abs(x2 - x1))
        offset, diff = self.offset, abs(x2 - x1)
        meta1, meta2 = [lst[0] for lst in lsts], [lst[1] for lst in lsts]
        i1, i2 = None, None
        if diff > 3.75:
            i1 = bisect_left(meta1, x1)
        else:
            i1 = bisect_left(meta1, x1 - offset)
        i2 = bisect_left(meta2, x2 - offset)

        if i1 != len(meta1):
            print('1 -', lsts[i1])
            if abs(lsts[i1][0] - x1) <= offset and abs(lsts[i1][1] - x2) <= offset and lsts[i1][2] == x3:
                print('AGREE!')
                return i1
        if i2 != len(meta2):
            print('2 -', lsts[i2])
            if abs(lsts[i2][0] - x1) <= offset and abs(lsts[i2][1] - x2) <= offset and lsts[i2][2] == x3:
                print('AGREE!')
                return i2
        '''
        i1 = bisect_left(meta1, x1 - offset)
        i1t1 = bisect_left(meta1, x1 + offset)
        i1t2 = bisect_left(meta1, x1)
        i2 = bisect_left(meta2, x2 - offset)
        i2t1 = bisect_left(meta2, x2 + offset)
        i2t2 = bisect_left(meta2, x2)
        if i1 != len(meta1) and i2 != len(meta2):
            print('1 -', lsts[i1], '2 -', lsts[i2])
            if i1t1 != len(meta1) and i2t1 != len(meta2):
                print('1p -', lsts[i1t1], '2p -', lsts[i2t1])
            if i1t2 != len(meta1) and i2t2 != len(meta2):
                print('1n -', lsts[i1t2], '2n -', lsts[i2t2])
            lst1, lst2 = lsts[i1], lsts[i2]
            if i1 == i2 and lst1[0] == lst2[0] and lst1[1] == lst2[1] and lst1[2] == lst2[2]:
                i, start, end, label = i1, *lst1
                #print(lst1)
                #print(abs(olst[0] - x1), abs(olst[1] - x2), olst[2] == x3)
                if abs(start - x1) <= offset and abs(end - x2) <= offset and label == x3:
                    print('AGREE!')
                    return i'''
        return -1

    def __checkIntegrity(self):
        lens = [len(v) for k, v in self.agreements.items()]
        if lens[0] != lens[1]:
            #print(self.agreements)
            print(lens)
            #raise Exception('There are difference between two observers')
        else:
            print(lens)

    def __process(self):
        import time
        t = time.process_time()
        data1, data2 = ((k, v) for k, v in self.files.items())
        o1, v1 = data1
        o2, v2 = data2

        '''for e in v2:
            ix = self.__locate(v1, e[0], e[1], e[2])
            if ix > -1:
                self.data['observer1'].append(v1[ix])
                print(' ---- RESULT', o1, v1[ix], 'vs', o2, e)
                del v1[ix]
            else:
                print('BAD', o2, e)'''
        self.__compare(v1, v2, o1, o2)
        self.__compare(v2, v1, o2, o1)
        self.__checkIntegrity()
        elapsed_time = time.process_time() - t
        #print(elapsed_time)

    def __compare(self, v1, v2, observer1, observer2, flag=1):
        if not v1 or not v2:
            return None
        cv1, cv2 = v1.copy(), v2.copy()
        if flag == 0:
            for i, event1 in enumerate(cv1):
                start1, end1, label1 = event1[0], event1[1], event1[2]
                self.data[observer1].append(event1 + [i])
                for j, event2 in enumerate(cv2):
                    start2, end2, label2 = event2[0], event2[1], event2[2]
                    diffStart, diffEnd = abs(start1 - start2), abs(end1 - end2)
                    if diffStart <= self.offset and diffEnd <= self.offset and label1 == label2:
                        self.agreements[observer2].append(cv2[j] + [j])
                        self.attemps[observer1].append(1)
                        cv2.remove(event2)
                        break
        else:
            for e in cv1:
                ix = self.__locate(cv2, e[0], e[1], e[2])
                self.data[observer1].append(e + [ix])
                if ix > -1:
                    self.agreements[observer2].append(cv2[ix] + [ix])
                    self.attemps[observer1].append(1)
                    del cv2[ix]
                else:
                    self.attemps[observer1].append(0)

    def __test(self, v1, v2):
        from nltk.agreement import AnnotationTask
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = AnnotationTask(data=formatted)

    def old_graphBrokenBarh(self):
        import matplotlib.pyplot as plt
        import math
        fig, ax = plt.subplots()
        colormapping = {'R':'tab:cyan','M1':'tab:blue','N1':'tab:green','VF':'tab:purple','AM':'tab:orange'}
        verts, colors = [], []
        for d in self.data['ZZ']:
            verts.append((math.ceil(d[0]), math.ceil(d[1])))
            colors.append(colormapping[d[2]])
        ax.broken_barh(
            verts,
            (10, 9),
            facecolors=colors
        )
        verts, colors = [], []
        for d in self.data['XX']:
            verts.append((math.ceil(d[0]), math.ceil(d[1])))
            colors.append(colormapping[d[2]])
        ax.broken_barh(
            verts,
            (20, 9),
            facecolors=colors
        )
        ax.set_ylim(5, 35)
        ax.set_xlim(0, 90)
        ax.set_xlabel('seconds since start')
        ax.set_yticks([15, 25])
        ax.set_yticklabels(['Observer 1', 'Observer 2'])
        ax.grid(True)
        plt.show()

    def graphBrokenBarh(self, title = 'IOA - Observer 1 vs. Observer 2', tools = 'wheel_zoom, pan, save, reset,'):
        from bokeh.plotting import figure, output_file, show
        from bokeh.models import Range1d
        AUDIO_MAX_LEN = 90
        p = figure(title=title, tools=tools, y_range=Range1d(bounds=(0, 1)), x_range=(0, 60), sizing_mode='stretch_both')
        p.xaxis.axis_label = 'Timeline'
        p.yaxis.axis_label = 'Observer'
        railmap = {'N1': 0, 'M1': 0.0013, 'R': 0.0026, 'VF': 0.0039, 'AM': 0.0052}
        colorm = {'XX': 'blue', 'ZZ': 'pink'}

        data = {'data':[],'observer':[],'colors':[], 'marks': []}
        for k, v in self.data.items():
            for i, e in enumerate(v):
                start, end, label, iAgree = e[0], e[1], e[2], e[3]
                diff = abs(end - start)
                currObserver, currMarker, currColor = self.observermap[k], self.markermap[k], self.colormap[label]
                currRail = railmap[label]
                data['data'].append(start)
                data['observer'].append(currObserver)
                data['colors'].append(currColor)
                data['marks'].append(currMarker)
                #if iAgree != -1:
                #    currColor = self.pcolormap[label]
                p.line([start, start + diff], [currObserver + currRail, currObserver + currRail], line_color=currColor, line_width=6)
                #p.line([start, start + diff], [currObserver, currObserver + 0.015], line_color=currColor, line_width=2)
                #p.line([end, end], [currObserver, currObserver - 0.010], line_color=currColor, line_width=2)
            p.circle([0], self.observermap[k], color=colorm[k], legend_label=k, fill_alpha=0.2, size=7) # sieze 10
            data = {'data':[],'observer':[],'colors':[], 'marks': []}

        for k, v in self.colormap.items():
            p.line(0, 0, line_color=v, legend_label=k, line_width=6)

        railmap = {'ZZ': 0.25, 'XX': 0.23}
        for k, v in self.agreements.items():
            for e in v:
                start, end, label = e[0], e[1], e[2]
                diff = abs(end - start)
                p.line([start, start + diff], [railmap[k], railmap[k]], line_color='green', line_width=6)

        p.line([0, AUDIO_MAX_LEN], [0.33, 0.33], line_color="gray", line_width=1, line_alpha=0.2)

        ticks = [i for i in range(0, AUDIO_MAX_LEN + 1) if i % 2 == 0]
        #for i in range(0, 90):
        #    if i % 2 == 0: ticks.append(i)

        p.legend.title = 'Etiquetas'
        p.xaxis.ticker = ticks
        p.ygrid.grid_line_dash = [6, 4]
        p.xaxis.bounds = (0, 90)
        p.x_range.min_interval = 7
        #p.x_range.max_interval = 10
        show(p)

    def kappa(self, printRes=True):
        kappa = self.ratingtask.kappa()
        if printRes:
            print('Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4)))
        return kappa

    def saveMetrics(self):
        filename = '{0}/output/metrics.txt'.format(self.src)
        with open(filename, 'a') as out:
            out.write('Observer {0}\n'.format(self.observer + 1))
            out.write('{0}, attemps: {1}\n'.format(self.oName, self.attemps))
            out.write('Cohen\'s Kappa: {0}%\n'.format(round(self.kappa(printRes=False) * 100, 4)))

def getArgs():
    parser = ArgumentParser(prog='deadshot', description='Arguments being passed to the program')
    parser.add_argument('--limit', '-aL', required=False, default=60, help='Audio lenght')
    parser.add_argument('--sample', '-sp', required=True, default='./sample', help='Sample path')
    parser.add_argument('--rev', '-r', required=True, help='Revision of file')
    parser.add_argument('--offset', '-do', required=False, default=0.150, help='Offset')
    return parser.parse_args()

def main():
    args = getArgs()

    buffer, bLen = load(path=args.sample, rev=args.rev, limit=float(args.limit))
    if bLen == 2:
        offset = float(args.offset)
        dex = Dex(buffer, src=args.sample, offset=offset)
        #dex.graphBrokenBarh()
    else:
        raise NotImplementedError('Only accepted two observers')

if __name__ == '__main__':
    main()
