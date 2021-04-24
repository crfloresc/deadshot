class Dex(object):
    def __init__(self, buffer, src=None, offset=0.150, limit=60.00, debug=False):
        self.files = buffer
        self.src = src
        self.offset = offset
        self.limit = limit
        self.debug = debug
        # For processing
        self.data = {}
        self.agreements = {}
        self.attemps = {}
        # For chart
        self.colormap = {}
        self.observermap = {}
        # For agree
        self.ratingtask = None

        self.__setupDicts()
        self.__process()

    def __setupDicts(self):
        val = 0.40
        self.colormap = {'VF': 'red', 'N': 'green', 'M': 'blue', 'AM': 'purple', 'R': 'black'}
        self.pcolormap = {'VF': 'firebrick', 'N': 'darkolivegreen', 'M': 'royalblue', 'AM': 'plum', 'R': 'darkslategray'}
        for k, v in self.files.items():
            val = val - 0.05
            self.data[k] = []
            self.agreements[k] = []
            self.attemps[k] = []
            self.observermap[k] = val

    def __locate(self, lsts, x1, x2, x3):
        from bisect import bisect_left
        #print('Start:', 'x1:', x1, 'x2:', x2, 'x3:', x3, 'diff:', abs(x2 - x1))
        offset, diff = self.offset, abs(x2 - x1)
        meta1, meta2 = [lst[0] for lst in lsts], [lst[1] for lst in lsts]
        i1, i2 = None, None
        if diff > 3.75:
            i1 = bisect_left(meta1, x1)
        else:
            i1 = bisect_left(meta1, x1 - offset)
        i2 = bisect_left(meta2, x2 - offset)

        if i1 != len(meta1):
            #print('1 -', lsts[i1])
            if abs(lsts[i1][0] - x1) <= offset and abs(lsts[i1][1] - x2) <= offset and lsts[i1][2] == x3:
                #print('AGREE!')
                return i1
        if i2 != len(meta2):
            #print('2 -', lsts[i2])
            if abs(lsts[i2][0] - x1) <= offset and abs(lsts[i2][1] - x2) <= offset and lsts[i2][2] == x3:
                #print('AGREE!')
                return i2
        return -1

    def __checkIntegrity(self):
        lens = [len(v) for k, v in self.agreements.items()]
        if lens[0] != lens[1]:
            print(self.agreements)
            print(lens)
            raise Exception('There are difference between two observers')
        else:
            print(lens)

    def __process(self):
        from time import process_time
        t = process_time()
        data1, data2 = ((k, v) for k, v in self.files.items())
        o1, v1 = data1
        o2, v2 = data2

        self.__compare(v1, v2, o1, o2)
        self.__compare(v2, v1, o2, o1)
        self.__checkIntegrity()
        elapsed_time = process_time() - t
        print(elapsed_time)

    def __compare(self, v1, v2, observer1, observer2, flag=0):
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
                        self.agreements[observer2].append(tuple(cv2[j]))
                        self.attemps[observer1].append(j)
                        cv2.remove(event2)
                        break
        else:
            for e in cv1:
                ix = self.__locate(cv2, e[0], e[1], e[2])
                self.data[observer1].append(e + [ix])
                if ix > -1:
                    self.agreements[observer2].append(tuple(cv2[ix]))
                    self.attemps[observer1].append(1)
                    del cv2[ix]
                else:
                    self.attemps[observer1].append(0)

    def __test(self, v1, v2):
        from nltk.agreement import AnnotationTask
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = AnnotationTask(data=formatted)

    def graphBrokenBarh(self, title = 'IOA - Observer 1 vs. Observer 2', tools = 'wheel_zoom, pan, save, reset,'):
        from bokeh.plotting import figure, output_file, show
        from bokeh.palettes import Spectral6
        from bokeh.models import BoxAnnotation, ColumnDataSource, Label, LabelSet, Range1d, HoverTool
        from bokeh.transform import factor_cmap
        p = figure(title=title, tools=tools, y_range=Range1d(bounds=(0, 1)), x_range=(0, 60), sizing_mode='stretch_both')
        p.xaxis.axis_label = 'Timeline'
        p.yaxis.axis_label = 'Observer'
        railmap = {'N': 0, 'M': 0.0013, 'R': 0.0026, 'VF': 0.0039, 'AM': 0.0052}
        colorm = {'XX': 'blue', 'ZZ': 'pink'}

        for i, (k, v) in enumerate(self.data.items()):
            for j, e in enumerate(v):
                start, end, label, iAgree = e[0], e[1], e[2], e[3]
                diff = abs(end - start)
                observer, color = self.observermap[k], self.colormap[label]
                rail = railmap[label]
                #data = {'x': [start, start + diff], 'y': [observer + rail, observer + rail], 'start': [start, start], 'end': [end, end], 'label': [label, label]}
                data = {'x': [start], 'y': [observer + rail], 'start': [start], 'end': [end], 'label': [label]}
                source = ColumnDataSource(data=data)
                if j == 0:
                    observerLabel = Label(x=start, y=observer, text=k, x_offset=-30, render_mode='canvas')
                    p.add_layout(observerLabel)
                #p.line(x='x', y='y', name=label, line_color=color, line_width=6, source=source)
                p.hbar(y='y', height=0.007, left='start', right='end', name=label, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7, source=source)

        for k, v in self.colormap.items():
            p.line(0, 0, line_color=v, legend_label=k, line_width=6)

        '''data = {'x': [], 'y': [], 'line_color': [], 'label': [], 'start': []}
        for k, v in self.data.items():
            for i, e in enumerate(v):
                start, end, label = e[0], e[1], e[2]
                if label != 'R':
                    continue
                diff = abs(end - start)
                observer, color, rail = self.observermap[k], self.colormap[label], railmap[label]
                data['x'].append(start)
                data['x'].append(start + diff)
                data['y'].append(observer + rail)
                data['y'].append(observer + rail)
                data['line_color'].append(color)
                data['line_color'].append(color)
                data['label'].append(label)
                data['label'].append(label)
                data['start'].append(start)
                data['start'].append(start)
                p.line(x='x', y='y', line_color='black', line_width=6, legend_group='label', source=data)
                data = {'x': [], 'y': [], 'line_color': [], 'label': [], 'start': []}
            break'''

        railmap = {'ZZ': 0.25, 'XX': 0.23, '--': 0.21}
        for k, v in self.agreements.items():
            for e in v:
                start, end, label = e
                diff = abs(end - start)
                p.line([start, start + diff], [railmap[k], railmap[k]], line_color='green', line_alpha=0.8, line_width=6)

        agreement = []
        noAgreement = []
        result = {'agreement': [], 'noAgreement': []}
        lastStart, lastEnd = 0, 0
        partialStart = 0
        z1, z2 = 0, 0
        for i, (v1, v2) in enumerate(zip(*self.agreements.values())):
            start1, end1, label1 = v1
            start2, end2, label2 = v2
            newStart, newEnd = start2 if start1 > start2 else start1, end2 if end1 < end2 else end1
            #print([newStart, newEnd], [partialStart, lastStart], '-', [z1, z2], lastStart - newStart)
            if lastStart - newStart < 0:
                agreement.append((z1, z2))
                noAgreement.append((z2, newStart))
                result['agreement'].append((z1, z2))
                result['noAgreement'].append((z2, newStart))
                z1, z2 = newStart, newEnd
            else:
                z2 = newEnd
            partialStart = newStart
            lastStart = newEnd
        else:
            agreement.append((z1, z2))
            noAgreement.append((z2, self.limit))
            result['agreement'].append((z1, z2))
            result['noAgreement'].append((z2, self.limit))

        # draw agreement bar and annotation
        agreementcolormap = {'agreement': 'green', 'noAgreement': 'red'}
        agreementrailmap = {'agreement': 0.21, 'noAgreement': 0.19}
        for k, v in result.items():
            for e in v:
                start, end = e
                y, color = agreementrailmap[k], agreementcolormap[k]
                if k == 'noAgreement':
                    p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color=color))
                #p.line([start, start + abs(end - start)], [y, y], line_color=color, line_alpha=0.8, line_width=6)
                p.hbar(y=y, height=0.007, left=start, right=end, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7)

        # draw agreement bar and annotation
        '''for e in agreement:
            start, end = e
            p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color='green'))
            p.line([start, start + abs(end - start)], [0.21, 0.21], line_color='green', line_alpha=0.8, line_width=6)

        # draw no agreement bar and annotation
        for e in noAgreement:
            start, end = e
            p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color='red'))
            p.line([start, start + abs(end - start)], [0.19, 0.19], line_color='red', line_alpha=0.8, line_width=6)
        '''

        # add observers names
        citation = Label(x=70, y=500, x_units='screen', y_units='screen',
                 text=self.__kappa(0.87), render_mode='css',
                 border_line_color='black', border_line_alpha=1.0,
                 background_fill_color='white', background_fill_alpha=1.0)
        p.add_layout(citation)

        # Notation
        p.line([0, self.limit], [0.33, 0.33], line_color='gray', line_width=1, line_alpha=0.2)
        p.line([0, self.limit], [0.28, 0.28], line_color='gray', line_width=1, line_alpha=0.2)

        ticks = [i for i in range(0, int(self.limit) + 1) if i % 2 == 0]
        node_hover_tool = HoverTool(names=['VF', 'R', 'N', 'M', 'AM'], tooltips=[('label', '@label'), ('start', '@start'), ('end', '@end')])

        p.add_tools(node_hover_tool)
        p.legend.title = 'Etiquetas'
        #p.legend.click_policy = 'hide'
        p.xaxis.ticker = ticks
        p.ygrid.grid_line_dash = [6, 4]
        p.xaxis.bounds = (0, 90)
        p.x_range.min_interval = 7
        show(p)

    def __kappa(self, kappa):
        #kappa = self.ratingtask.kappa()
        return 'Cohen\'s Kappa: {}%'.format(round(kappa * 100, 4))

    def saveMetrics(self):
        filename = '{0}/output/metrics.txt'.format(self.src)
        with open(filename, 'a') as out:
            out.write('Observer {0}\n'.format(self.observer + 1))
            out.write('{0}, attemps: {1}\n'.format(self.oName, self.attemps))
            #out.write('Cohen\'s Kappa: {0}%\n'.format(round(self.kappa(printRes=False) * 100, 4)))
