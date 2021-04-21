from argparse import ArgumentParser
import numpy as np
import seaborn as sns
import pandas as pd
from app.lib import Measures, load
from prettytable import PrettyTable

class Dex(object):
    def __init__(self, buffer, observer, src=None, showAttemps=True, offset=0.150, debug=False):
        self.table = PrettyTable()
        self.files = buffer
        self.offset = offset
        self.debug = debug
        self.ratingtask = None
        self.assest = None
        self.comp1, self.comp2 = None, None
        self.observer = observer
        self.sv1 = None
        self.sv2 = None
        self.dv1 = None
        self.dv2 = None
        self.data = {'observer1': [], 'observer2': []}
        self.showAttemps = showAttemps
        self.attemps = 0
        self.oName = None
        self.src = src
        self.process()

    def locate(self, lsts, x1, x2, x3, offset=0.300, debug=False):
        import bisect
        if (debug): print('\n', 'START', x1, x2, x3)
        meta = [lst[0] for lst in lsts]
        i1 = bisect.bisect_left(meta, x1 - offset)
        if (debug): print('i1', i1, x1, lsts[i1])

        if i1 != len(meta):
            lst = lsts[i1][:2]
            meta = [lst[1] for lst in lsts]
            if lst[1] < x2 + offset:
                offset = -offset
            if (debug): print('LIST', lst, 'OFFSET', offset, 'X2-OFF', x2 + offset)
            i2 = bisect.bisect_right(meta, x2 + offset)
            if (debug): print('i2', i2, x2, lsts[i2])
            if i1 == i2 and x3 == lsts[i1][2]:
                return i1
        return -1

    def process(self):
        data1, data2 = ((k, v) for k, v in self.files.items())
        o1, v1 = data1
        o2, v2 = data2

        for e in v2:
            ix = self.locate(v1, e[0], e[1], e[2])
            if ix > -1:
                print(' ---- RESULT', o1, v1[ix], 'vs', o2, e)
                del v1[ix]
            else:
                print('BAD', o2, e)
        self.__compare(v1, v2, 'observer1')
        self.__compare(v2, v1, 'observer2')

    def __observer1(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        self.__compare(v1[1], v2[1])
        self.oName = v1[0]
        if self.showAttemps:
            print('\n{}, attemps: {}'.format(v1[0], self.attemps))
        self.__test(self.comp1, self.comp2)

    def __observer2(self):
        v1, v2 = ((k, v) for k, v in self.files.items())
        self.__compare(v2[1], v1[1])
        self.oName = v2[0]
        if self.showAttemps:
            print('\n{}, attemps: {}'.format(v2[0], self.attemps))
        self.__test(self.comp1, self.comp2)

    def __compare(self, v1, v2, observer):
        if not v1 or not v2:
            return None
        cv1, cv2 = v1.copy(), v2.copy()
        start, end, agree = None, None, 0
        va1 = [0 for v in cv1]

        bars1, bars2 = [], [-1 for v in cv1]
        startV1 = []
        xPlot, yPlot = [], [-1 for v in cv1]
        for i, e1 in enumerate(cv1):
            xPlot.append(round(e1[0]))
            bars1.append(e1[1] - e1[0])
            startV1.append([e1[0], e1[1] - e1[0], e1[1], e1[2]])
            for e2 in cv2:
                diffStart, diffEnd = abs(e1[0] - e2[0]), abs(e1[1] - e2[1])
                if i == 2 and self.debug:
                    print(e1, e2)
                    print(diffStart, diffEnd, diffStart >= 0, diffEnd >= 0, diffEnd <= self.offset, e1[2] == e2[2])
                if diffStart >= 0 and diffStart <= self.offset and diffEnd >= 0 and diffEnd <= self.offset and e1[2] == e2[2]:
                    if self.debug: print(diffStart, diffEnd, e1[2])
                    yPlot[i] = round(e1[0])
                    bars2[i] = e2[1] - e2[0]
                    agree += 1
                    va1[i] += 1
                    cv2.remove(e2)
                    break
        self.attemps = [agree, len(cv1)]
        self.assest = va1
        self.comp1, self.comp2 = xPlot, yPlot
        self.sv1 = startV1
        self.data[observer] += startV1

    def __test(self, v1, v2):
        from sklearn.metrics import cohen_kappa_score
        from nltk import agreement
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)

    def graphBrokenBarh(self):
        # problema con 2 etiquetas en el mismo espacio de tiempo
        # solo segundos (int)
        '''import matplotlib.pyplot as plt
        import math
        fig, ax = plt.subplots()
        colormapping = {'R':'tab:cyan','M1':'tab:blue','N1':'tab:green','VF':'tab:purple','AM':'tab:orange'}
        verts, colors = [], []
        for d in self.sv1:
            verts.append((math.ceil(d[0]), math.ceil(d[1])))
            colors.append(colormapping[d[2]])
        print(verts)
        print(colors)
        ax.broken_barh(
            verts,
            (10, 9),
            facecolors=colors
        )
        ax.broken_barh(
            [(0.15, 1), (3.17, 2), (0.45, 2), (130, 10)],
            (20, 9),
            facecolors=('tab:blue', 'tab:orange', 'tab:green', 'tab:red')
        )
        ax.set_ylim(5, 35)
        ax.set_xlim(0, 90)
        ax.set_xlabel('seconds since start')
        ax.set_yticks([15, 25])
        ax.set_yticklabels(['Observer 1', 'Observer 2'])
        ax.grid(True)
        plt.show()'''
        from bokeh.plotting import figure, output_file, show
        colormap = {'VF': 'red', 'N1': 'green', 'M1': 'blue', 'AM': 'purple', 'R': 'black'}
        observermap = {'observer1': 0.25, 'observer2': 0.2}
        markmap = {'observer1': 'hex', 'observer2': 'triangle'}

        p = figure(title = 'Some')
        p.xaxis.axis_label = 'Timeline'
        p.yaxis.axis_label = 'Observer'

        data = {'data':[],'observer':[],'colors':[], 'marks': []}
        for k, v in self.data.items():
            for e in v:
                data['data'].append(e[0])
                data['observer'].append(observermap[k])
                data['colors'].append(colormap[e[3]])
                data['marks'].append(markmap[k])
                p.line([e[0], e[0] + e[1]], [observermap[k], observermap[k] + 0.025], line_color=colormap[e[3]], line_width=3)
                p.line([e[0], e[0] + e[1]], [observermap[k], observermap[k]], line_color=colormap[e[3]], line_width=3)
            p.scatter(data['data'], data['observer'],
         color=data['colors'], marker=data['marks'], legend_label=k, fill_alpha=0.2, size=10)
            data = {'data':[],'observer':[],'colors':[], 'marks': []}

        p.line(0, 1, line_color="red", line_width=2)
        p.line(0, 0, line_color="red", line_width=2)
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
        dex = Dex(buffer, observer=0, showAttemps=False, src=args.sample, offset=offset)
        #dex.graphBrokenBarh()
    else:
        raise NotImplementedError('Only accepted two observers')

if __name__ == '__main__':
    main()
