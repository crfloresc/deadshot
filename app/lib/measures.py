from bisect import bisect_left
from bokeh.plotting import figure, output_file, show
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, LabelSet, Range1d, HoverTool
#from nltk import agreement
from time import process_time

class Dex(object):
    def __init__(self, sample, dataset, src=None, offset=0.150, limit=60.00, debug=False):
        self.sample = sample
        self.files = dataset
        self.src = src
        self.offset = offset
        self.limit = limit
        self.debug = debug
        # For processing
        self.data = {}
        self.agreements = {}
        self.tempAgreements = {}
        self.attemps = {}
        # For chart
        self.colormap = {}
        self.observermap = {}
        self.railmap = {}
        self.ioacolormap = {}
        self.ioarailmap = {}
        # For agree
        self.ratingtask = None

        self.__setupDicts()
        self.__process()

    def __setupDicts(self):
        val = 0.40
        self.colormap = {'VF': 'red', 'N': 'green', 'M': 'blue', 'AM': 'purple', 'R': 'black'}
        self.railmap = {'N': 0, 'M': 0.0013, 'R': 0.0026, 'VF': 0.0039, 'AM': 0.0052}
        self.ioacolormap = {'agreement': 'green', 'noAgreement': 'red'}
        self.ioarailmap = {'agreement': 0.25, 'noAgreement': 0.24}
        for k, v in self.files.items():
            val = val - 0.05
            self.data[k] = []
            self.agreements[k] = []
            self.tempAgreements[k] = []
            self.attemps[k] = []
            self.observermap[k] = val

    def __checkIntegrity(self):
        o1, o2 = (len(v) for k, v in self.agreements.items())
        print([o1, o2])
        return True if o1 == o2 else False

    def __compare(self, v1, v2, observer1, observer2, num):
        cv1, cv2 = v1.copy(), v2.copy()
        #self.data[observer1] = [tuple(_) for _ in cv1]
        #self.agreements[observer2] = [tuple(_) for e in cv1 for _ in cv2 if (abs(e[0] - _[0]) <= self.offset) and (abs(e[1] - _[1]) <= self.offset) and (e[2] == _[2])]
        #'''
        for i, event1 in enumerate(cv1):
            start1, end1, label1 = event1
            self.data[observer1].append(event1)
            #res = res + [tuple(_) for _ in cv2 if (abs(start1 - _[0]) <= self.offset) and (abs(end1 - _[1]) <= self.offset) and (label1 == _[2])]
            for j, event2 in enumerate(cv2):
                start2, end2, label2 = event2
                diffStart, diffEnd = abs(start1 - start2), abs(end1 - end2)
                if diffStart <= self.offset and diffEnd <= self.offset and label1 == label2:
                    self.agreements[observer2].append(cv2[j])
                    self.tempAgreements[observer2].append(cv2[j])
                    cv2.remove(event2)
                    break
        #self.agreements[observer2] = res
        #'''

    def __test(self, v):
        #ts, te = 0 * 100, 0.124560 * 100
        #cv = v.copy()
        cv = [(0, 0.124560, 'R'), (0, 0.144560, 'VF'), (0.201564, 0.856712, 'N')]
        limit = 1
        d = 441
        res = []
        ie = None
        track = [_ for _ in range(0, int(limit) * d)]
        for i in range(0, int(limit) * d):
            #if ie:
            #    del cv[ie]
            #    ie = None
            for j, (ts, te, label) in enumerate(cv):
                #if not ie:
                #    ie = j
                ds = i - ts * d
                de = i - te * d
                if ds >= 0 and de <= 0:
                    res.append(label)
                    track[i] = label
                    break
        print(track)
        print(len(track))
        print(len(res))

    def __process(self):
        t = process_time()
        data1, data2 = ((k, v) for k, v in self.files.items())
        o1, v1 = data1
        o2, v2 = data2
        if not v1 or not v2:
            raise Exception('v1 or v2 not present')

        self.__compare(v1, v2, o1, o2, 1)
        self.__compare(v2, v1, o2, o1, 2)
        if not self.__checkIntegrity():
            print(self.agreements)
            raise Exception('There are difference between two observers')
        elapsed_time = process_time() - t
        print(elapsed_time)
        self.__test(v1)
        self.__test(v2)

    def __ratingtask(self, data):
        #formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=data)

    def graphBrokenBarh(self, title=None, tools=None):
        if not title:
            title = 'IOA of {} - Observer 1 vs. Observer 2'.format(self.sample)
        if not tools:
            tools = 'wheel_zoom, pan, save, reset,'
        p = figure(title=title, tools=tools, y_range=Range1d(bounds=(0, 1)), x_range=(0, 60), sizing_mode='stretch_both')

        # Draw all events
        for i, (k, v) in enumerate(self.data.items()):
            for j, e in enumerate(v):
                start, end, label = e
                diff = abs(end - start)
                observer, color, rail = self.observermap[k], self.colormap[label], self.railmap[label]
                #data = {'x': [start, start + diff], 'y': [observer + rail, observer + rail], 'start': [start, start], 'end': [end, end], 'label': [label, label]}
                data = {'x': [start], 'y': [observer + rail], 'start': [start], 'end': [end], 'label': [label]}
                source = ColumnDataSource(data=data)
                if j == 0: # only for draw observer label
                    observerLabel = Label(x=start, y=observer, text=k, x_offset=-30, render_mode='canvas')
                    p.add_layout(observerLabel)
                #p.line(x='x', y='y', name=label, line_color=color, line_width=6, source=source)
                p.hbar(y='y', height=0.007, left='start', right='end', name=label, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7, source=source)

        # Only for draw legend colors
        for k, v in self.colormap.items():
            p.line(0, 0, line_color=v, legend_label=k, line_width=6)

        result = {'agreement': [], 'noAgreement': []}
        lastStart, lastEnd = 0, 0
        z1, z2 = 0, 0
        for i, (v1, v2) in enumerate(zip(*self.agreements.values())):
            start1, end1, label1 = v1
            start2, end2, label2 = v2
            newStart, newEnd = start2 if start1 > start2 else start1, end2 if end1 < end2 else end1
            if lastStart - newStart < 0:
                result['agreement'].append((z1, z2))
                result['noAgreement'].append((z2, newStart))
                z1, z2 = newStart, newEnd
            else:
                z2 = newEnd
            lastStart = newEnd
        else:
            result['agreement'].append((z1, z2))
            result['noAgreement'].append((z2, self.limit))

        # draw temp agreement bars
        '''railmap = {'ZZ': 0.21, 'XX': 0.19}
        for k, v in self.agreements.items():
            for e in v:
                start, end, label = e
                diff = abs(end - start)
                p.line([start, start + diff], [railmap[k], railmap[k]], line_color='green', line_alpha=0.8, line_width=6)'''

        # draw agreement bar and annotation
        for k, v in result.items():
            for (start, end) in v:
                color, rail = self.ioacolormap.get(k), self.ioarailmap.get(k)
                if k == 'noAgreement':
                    p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color=color))
                #p.line([start, start + abs(end - start)], [y, y], line_color=color, line_alpha=0.8, line_width=6)
                p.hbar(y=rail, height=0.007, left=start, right=end, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7)

        # add observers names
        '''citation = Label(x=70, y=500, x_units='screen', y_units='screen',
                 text=self.__kappa(0.87), render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)
        p.add_layout(citation)'''

        # Notation
        p.line([0, self.limit], [0.33, 0.33], line_color='gray', line_width=1, line_alpha=0.2)
        p.line([0, self.limit], [0.28, 0.28], line_color='gray', line_width=1, line_alpha=0.2)

        ticks = [i for i in range(0, int(self.limit) + 1) if i % 2 == 0]
        node_hover_tool = HoverTool(names=['VF', 'R', 'N', 'M', 'AM'], tooltips=[('label', '@label'), ('start', '@start'), ('end', '@end')])

        p.add_tools(node_hover_tool)
        p.legend.title = 'Etiquetas'
        p.xaxis.axis_label = 'Timeline'
        p.yaxis.axis_label = 'Observer'
        #p.legend.click_policy = 'hide'
        p.xaxis.ticker = ticks
        p.ygrid.grid_line_dash = [6, 4]
        p.xaxis.bounds = (0, 90)
        p.x_range.min_interval = 7
        #show(p)

    def __kappa(self):
        if not self.ratingtask:
            return None
        kappa = self.ratingtask.kappa()
        return 'Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4))

    def saveMetrics(self):
        filename = '{0}/output/metrics.txt'.format(self.src)
        with open(filename, 'a') as out:
            out.write('Observer {0}\n'.format(self.observer + 1))
            out.write('{0}, attemps: {1}\n'.format(self.oName, self.attemps))
            #out.write('Cohen\'s Kappa: {0}%\n'.format(round(self.kappa(printRes=False) * 100, 4)))
