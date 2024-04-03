from bokeh.plotting import figure, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, Range1d, HoverTool
from nltk import agreement
from time import process_time
from timeit import timeit
from decimal import getcontext, ROUND_HALF_UP, Decimal


getcontext().prec = 5
getcontext().rounding = ROUND_HALF_UP

class Deadshot(object):
    '''
    '''
    def __init__(self, sample_name, sample_data, valid_labels, output, label_colors,
                 padding='R', framing=10, offset=0.150, t=60.00, debug=False):
        super(Deadshot, self).__init__()
        self.sampleName = sample_name
        self.validLabels = valid_labels
        self.output = output
        self.labelColors = label_colors
        self.padding = padding
        self.framing = framing
        self.offset = offset
        self.t = t
        self.debug = debug
        # For processing
        self.data = {}
        self.agreements = {}
        # For chart
        self.colormap = {}
        self.observermap = {}
        self.railmap = {}
        self.ioacolormap = {}
        self.ioarailmap = {}
        # For agreement
        self.ratingtask = None

        self.__fill_label_maps()
        self.__fill_ioa_maps()
        self.__fill_observer_maps(sample_data)
        items1, items2 = self.__process_items(sample_data)
        self.__process_agreement(items1, items2)

    def __fill_label_maps(self):
        incrementInEventRail = 0.0013
        eventRailPos = 0
        for label, color in zip(self.validLabels, self.labelColors):
            self.colormap[label] = color
            self.railmap[label] = eventRailPos
            eventRailPos += incrementInEventRail

    def __fill_ioa_maps(self, observer_rail=0.55, keys=['agreement', 'noAgreement'],
                        colors=['green', 'red'], rail_pos=[0.14, 0.15]):
        for key, color, rail in zip(keys, colors, rail_pos):
            self.ioacolormap[key] = color
            self.ioarailmap[key] = observer_rail - rail

    def __fill_observer_maps(self, sample_data, observer_rail=0.55):
        for k in sample_data.keys():
            observer_rail = observer_rail - 0.05
            self.data[k] = []
            self.agreements[k] = []
            self.observermap[k] = observer_rail

    def __check_integrity(self):
        o1, o2 = (len(v) for v in self.agreements.values())
        return True if o1 == o2 else False

    def __compare(self, v1, v2, observer1, observer2):
        cv1, cv2 = v1.copy(), v2.copy()
        for event1 in cv1:
            start1, end1, label1 = event1
            self.data[observer1].append(event1)
            for j, event2 in enumerate(cv2):
                start2, end2, label2 = event2
                diffStart, diffEnd = abs(start1 - start2), abs(end1 - end2)
                if diffStart <= self.offset and diffEnd <= self.offset and label1 == label2:
                    self.agreements[observer2].append(cv2[j])
                    cv2.remove(event2)
                    break

    def __items_symmetric_difference(self, A, B):
        ''' SUBTRACTS A FROM B
            e.g, A =    ------
                 B =  -----------
            result =  --      ---
            Returns tuples of new range(s)'''
        if B[0] <= A[0]:
            (As, Ae, Al), (Bs, Be, Bl) = A, B
        else:
            (As, Ae, Al), (Bs, Be, Bl) = B, A

        if As > Be or Bs > Ae: # All of B visible
            return tuple([(Bs, Be, Bl)]), tuple([(As, Ae, Al)]), tuple([])
        Br = []
        Ar = []
        M = []
        if As > Bs: # Beginning of B visible
            Br.append((Bs, As, Bl))
        if Ae < Be: # End of B visible
            Br.append((Ae, Be, Bl))
        elif Be != Ae:
            Ar.append((Be, Ae, Al))
        if As != Be:
            l = Al + Bl if A[0] >= B[0] else Bl + Al
            if Be < Ae:
                M.append((As, Be, l))
            else:
                M.append((As, Ae, l))
        return tuple(Br), tuple(Ar), tuple(M)

    def __omh(self, vec):
        v = vec.copy()
        i = 0
        vl = len(v)
        while i < vl:
            if i + 1 < vl:
                A, B = v[i], v[i + 1]
                ranges = self.__items_symmetric_difference(A, B)
                if ranges[-1]:
                    del v[i]
                    del v[i + 1]
                    i = -1
                    vals = [e for _ in ranges for e in _ if _]
                    v = vals + v
                    vl = len(v)
            i += 1
        return v

    def __upsample_items(self, v, L, pad, d):
        '''__upsample(self, v) -> list
        e.g. #pv = [(0, 0.144560, 'RVF'), (0.201564, 0.856712, 'N')] # procesed vector

        Keyword arguments:
        v   -- the vector
        L   -- the length of audio (default is 60.00 ms)
        pad -- the padding to add to new vector (default is R)
        d   -- the framing in ms (default is 10 ms)
        '''
        td = 1000 / d # 1000 is ms
        track = [pad for _ in range(0, int(L * td))]
        for (st, et, label) in v:
            tst, tet = int(Decimal(st * td).to_integral_value()), int(Decimal(et * td).to_integral_value())
            for j in range(tst, tet - 1):
                track[j] = label
        return track

    def __process_items(self, sample_data):
        data1, data2 = ((k, v) for k, v in sample_data.items())
        coder1, items1 = data1
        coder2, items2 = data2
        if not items1 or not items2:
            raise Exception('items1 or items2 not presented')
        self.__compare(items1, items2, coder1, coder2)
        self.__compare(items2, items1, coder2, coder1)

        if not self.__check_integrity():
            raise Exception('There are difference between two observers')
        return (items1, items2)

    def __process_agreement(self, items1, items2):
        itemsTimeContinuous1 = self.__omh(items1)
        itemsTimeContinuous2 = self.__omh(items2)
        itemsUpsampled1 = self.__upsample_items(itemsTimeContinuous1, L=self.t, pad=self.padding, d=self.framing)
        itemsUpsampled2 = self.__upsample_items(itemsTimeContinuous2, L=self.t, pad=self.padding, d=self.framing)
        self.__metric_interannotator_agreement_coefficients(itemsUpsampled1, itemsUpsampled2)

    def __metric_interannotator_agreement_coefficients(self, v1, v2):
        formatted = [[1, i, v] for i, v in enumerate(v1)] + [[2, i, v] for i, v in enumerate(v2)]
        self.ratingtask = agreement.AnnotationTask(data=formatted)
        print(f'[INFO] Cohen\'s Kappa: {self.ratingtask.kappa() * 100:.2f}%')

    def cohen_kappa(self):
        if not self.ratingtask:
            return None
        return f'Cohen\'s Kappa: {round(self.ratingtask.kappa() * 100, 4)}%'

    def graph(self, title=None, tools=None):
        if not title:
            title = f'IOA of {self.sampleName} - Observer 1 vs. Observer 2'
        if not tools:
            tools = 'wheel_zoom, pan, save, reset,'
        filename = f'{self.output}{self.sampleName}.html'
        output_file(filename=filename, title=title)
        p = figure(
            title=title,
            tools=tools,
            y_range=Range1d(bounds=(0, 1)),
            x_range=(0, 60),
            sizing_mode='stretch_both',
            output_backend='webgl')

        # Draw all events
        print('[GRAPH] drawing all events ...')
        for i, (k, v) in enumerate(self.data.items()):
            for j, (start, end, label) in enumerate(v):
                diff = abs(end - start)
                observer, color, rail = self.observermap[k], self.colormap[label], self.railmap[label]
                data = {'x': [start], 'y': [observer + rail], 'start': [start], 'end': [end], 'label': [label]}
                source = ColumnDataSource(data=data)
                if j == 0: # only for draw observer label
                    observerLabel = Label(x=start, y=observer, text=k, x_offset=-30, render_mode='canvas')
                    p.add_layout(observerLabel)
                p.hbar(y='y', height=0.007, left='start', right='end', name=label, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7, source=source)

        # Only for draw legend colors
        print('[GRAPH] drawing legends ...')
        for k, v in self.colormap.items():
            p.line(0, 0, line_color=v, legend_label=k, line_width=2)

        # Create agreement bars
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
            result['noAgreement'].append((z2, self.t))

        # draw agreement bar and annotation
        print('[GRAPH] drawing agreement bars ...')
        for k, v in result.items():
            for (start, end) in v:
                color, rail = self.ioacolormap.get(k), self.ioarailmap.get(k)
                if k == 'noAgreement':
                    p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color=color))
                p.hbar(y=rail, height=0.007, left=start, right=end, line_color=color, line_alpha=0.8, fill_color=color, fill_alpha=0.7)

        # add ioa percent
        print('[GRAPH] drawing ioa percent ...')
        ioaPercent = Label(x=70, y=500, x_units='screen', y_units='screen',
                 text=self.cohen_kappa(), render_mode='css',
                 border_line_color='black', border_line_alpha=0.9,
                 background_fill_color='white', background_fill_alpha=1.0)
        p.add_layout(ioaPercent)

        print('[GRAPH] setting up stuffs ...')
        p.add_tools(
            HoverTool(
                names=self.validLabels,
                tooltips=[('label', '@label'), ('start', '@start'), ('end', '@end')]
                ))
        p.legend.title = 'Labels'
        p.legend.title_text_font_style = 'bold'
        p.legend.title_text_font_size = '20px'
        p.xaxis.axis_label = 'Timeline (seg)'
        p.xaxis.ticker = [i for i in range(0, int(self.t) + 1) if i % 2 == 0]
        p.xaxis.bounds = (0, int(self.t))
        p.yaxis.axis_label = 'Observer'
        p.yaxis.major_label_text_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None
        p.ygrid.grid_line_dash = [6, 4]
        p.x_range.min_interval = 7
        print('[GRAPH] Finished!')
        save(p)
