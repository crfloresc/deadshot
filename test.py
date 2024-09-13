import numpy as np
from os import listdir
from os.path import abspath


# np.set_printoptions(suppress=True)
float_tol = 0.00000024
data_type = np.dtype([('start', np.float32), ('end', np.float32), ('label', np.dtype('U255'))])

def create_time_continuous_array(data, debug=False):
    i = 0
    max_data = len(data) - 1

    while i < max_data:
        simmetric_differences, len_sd = symmetric_difference(data[i], data[i+1])
        if debug: print('<---d', data[i], data[i+1])
        if debug: print('<---sd', simmetric_differences, len_sd)
        if len_sd > 0:
            data = np.delete(data, [i, i+1])
            data = np.append(data, simmetric_differences)
            data = np.sort(data, order=['start', 'end'])
        if len_sd != 0:
            i = 0
            max_data = len(data) - 1
            if debug: print('reset!')
        else:
            i += 1
        if debug: print()

    return data

def symmetric_difference(a: tuple, b: tuple):
    ''' SYMMETRIC DIFFERENCE BETWEEN A FROM B
        e.g, A =    ------
             B = -----------
        result = --- ---- --
        Returns tuples of new range(s)'''
    if b[0] <= a[0]:
        (a_start, a_end, a_label), (b_start, b_end, b_label) = a, b
    else:
        (a_start, a_end, a_label), (b_start, b_end, b_label) = b, a

    if a_start > b_end or b_start > a_end: # All of B visible
        return np.array([b, a], dtype=data_type), 0

    a_result = np.array([], dtype=data_type)
    b_result = np.array([], dtype=data_type)
    intersected = np.array([], dtype=data_type)
    if a_start > b_start: # Beginning of B visible
        b_result = np.append(b_result, np.array([(b_start, a_start, b_label)], dtype=data_type))
    if a_end < b_end: # End of B visible
        b_result = np.append(b_result, np.array([(a_end, b_end, b_label)], dtype=data_type))
    elif b_end != a_end:
        a_result = np.append(a_result, np.array([(b_end, a_end, a_label)], dtype=data_type))
    if a_start != b_end:
        l = a_label + b_label if a_start >= b_start else b_label + a_label
        if b_end < a_end:
            intersected = np.append(intersected, np.array([(a_start, b_end, l)], dtype=data_type))
        else:
            intersected = np.append(intersected, np.array([(a_start, a_end, l)], dtype=data_type))

    return np.hstack((a_result, b_result, intersected), dtype=data_type).ravel(), len(intersected)

def get_min_max_start_end(a, b) -> tuple:
    combined_data = np.concatenate((a, b))
    all_values = np.concatenate((combined_data['start'], combined_data['end']))
    return np.min(all_values), np.max(all_values)

def get_max_end(a, b) -> float:
    # if len(a) == 0 and len(b) == 0:
    #     return 0
    # if len(a) == 0 and len(b) != 0:
    #     return b[-1][1]
    # if len(a) != 0 and len(b) == 0:
    #     return a[-1][1]
    # return a[-1][1] if a[-1][1] > b[-1][1] else b[-1][1]
    combined_data = np.concatenate((a, b))
    return np.max(combined_data['end'])

def matches_timelines(timeline1, timeline2, max_time_diff=0.1):
    similar_segments = []

    i, j = 0, 0

    while i < len(timeline1) and j < len(timeline2):
        start1, end1, label1 = timeline1[i]
        start2, end2, label2 = timeline2[j]

        # Find overlap between the two intervals
        overlap_start = min(start1, start2)
        overlap_end = max(end1, end2)

        if overlap_start < overlap_end:
            diff_start, diff_end = abs(start1 - start2), abs(end1 - end2)
            diff_start_is_close = np.isclose([max_time_diff], [diff_start], rtol=float_tol)[0]
            diff_end_is_close = np.isclose([max_time_diff], [diff_end], rtol=float_tol)[0]
            if (diff_end <= max_time_diff or diff_end_is_close) and (diff_start <= max_time_diff or diff_start_is_close) and label1 == label2:
                similar_segments.append((overlap_start, overlap_end, label1))

        # Move to the next interval in the timeline that ends first
        if end1 < end2:
            i += 1
        else:
            j += 1

    return similar_segments

def to_track_like(vec, max_end, pad='ZVOID', frame_lim=1000, debug=False):
    '''
    Keyword arguments:
    vec         -- the vector
    max_end     -- the length of audio
    pad         -- the padding to add to new vector (default is ZVOID)
    frame_lim   -- the frames limit per sec (default is 1000 frames per sec)
    '''
    vec_copied = np.copy(vec)
    vec_copied['start'] *= frame_lim
    vec_copied['end'] *= frame_lim

    track = np.full(int(max_end * frame_lim), pad)

    starts = np.round(vec_copied['start']).astype(int)
    ends = np.round(vec_copied['end']).astype(int)

    for i in range(len(vec_copied)):
        track[starts[i]:ends[i]] = vec_copied['label'][i]

    if debug: print(track, len(track))
    return track

def metric_interannotator_agreement_coefficients(vec1, vec2, ndigits=2):
    from nltk import agreement
    formatted = [[1, i, v] for i, v in enumerate(vec1)] + [[2, i, v] for i, v in enumerate(vec2)]
    ratingtask = agreement.AnnotationTask(data=formatted)
    return round(ratingtask.kappa() * 100, ndigits)

def validate_segmentions(buffer, valid_labels, audio_duration, remove_number_from_labels):
    segments = []

    for line in buffer.readlines():
        parts = line.strip().split('\t')
        if len(parts) != 3 or parts[0] == '\\':
            continue

        label = parts[2].strip()
        if remove_number_from_labels and any(char.isdigit() for char in label):
            label = label[0]

        if label not in valid_labels:
            continue

        start = float(parts[0].replace(',', '.'))
        end = float(parts[1].replace(',', '.'))

        if start >= audio_duration:
            continue

        segments.append((start, end, label))

    return np.array(segments, dtype=data_type)

def load_labels(
    file_paths,
    labels
):
    from contextlib import ExitStack

    sample_data = dict()

    with ExitStack() as stack:
        files_data = [stack.enter_context(open(filename)) for filename in file_paths]
        unpacked_files_data = { file_buffer.name.split('/')[-1][:2]:file_buffer for file_buffer in files_data }
        sample_data = { key:validate_segmentions(buffer, labels, 999, False) for key, buffer in unpacked_files_data.items() }
    return sample_data

def chart(sample, agreement, labels, max_end, measure, color_map):
    from bokeh.plotting import figure, save, output_file
    from bokeh.models import Range1d, Label, HoverTool, ColumnDataSource

    output_file(filename='./out/test.html', title='IOA')

    p = figure(
        title='IOA',
        tools='wheel_zoom, pan, save, reset',
        y_range=Range1d(bounds=(0, 1)),
        x_range=(0, 60),
        sizing_mode='stretch_both',
        output_backend='webgl'
    )

    label_render_pos_map = { label:(i+1)/500 for i, label in enumerate(labels) }
    observer_render_pos = 0.55
    for observer_key, events in sample.items():
        observer_render_pos -= 0.05
        p.add_layout(Label(x=0, y=observer_render_pos,
                                   text=observer_key, x_offset=-30)) # render_mode='canvas'

        for j, (start, end, label) in enumerate(events):
            rail = label_render_pos_map.get(label)
            color = color_map.get(label)

            data = np.array([(start, end, label)], dtype=data_type)
            source = ColumnDataSource(data=dict(
                x=data['start'],
                y=[observer_render_pos + rail],
                start=data['start'],
                end=data['end'],
                label=data['label']
            ))

            p.hbar(y='y', height=0.007,
                   left='start', right='end',
                   name=label, line_color=color,
                   line_alpha=0.8, fill_color=color,
                   fill_alpha=0.7, source=source)
    
    for label in labels:
        p.line(x=[], y=[], line_color=color_map.get(label),
               legend_label=label, line_width=2)
    
    # print('[GRAPH] drawing agreement bars ...')
    # agreements = np.array(list(zip(*self.agreements.values())), dtype=[('start', np.float32), ('end', np.float32), ('label', 'U10')])
    # result = {'agreement': [], 'noAgreement': []}

    # z1, z2 = 0, 0
    # last_start, last_end = 0, 0

    # for (start1, end1, _), (start2, end2, _) in agreements:
    #     new_start = min(start1, start2)
    #     new_end = max(end1, end2)
        
    #     if last_start < new_start:
    #         result['agreement'].append((z1, z2))
    #         result['noAgreement'].append((z2, new_start))
    #         z1, z2 = new_start, new_end
    #     else:
    #         z2 = new_end
    #     last_start = new_end

    # # Append the final agreement/noAgreement
    # result['agreement'].append((z1, z2))
    # result['noAgreement'].append((z2, self.t))

    # # Draw agreement bars and annotations
    # for agreement_type, segments in result.items():
    #     for start, end in segments:
    #         color = self.ioacolormap[agreement_type]
    #         rail = self.ioarailmap[agreement_type]
            
    #         if agreement_type == 'noAgreement':
    #             p.add_layout(BoxAnnotation(left=start, right=end, fill_alpha=0.1, fill_color=color))
            
    #         p.hbar(y=rail, height=0.007, left=start, right=end, line_color=color, 
    #                line_alpha=0.8, fill_color=color, fill_alpha=0.7)

    ioa_percent = Label(x=70, y=500, x_units='screen', y_units='screen',
                        text=f'Cohen\'s Kappa: {measure}%', #render_mode='css',
                        border_line_color='black', border_line_alpha=0.9,
                        background_fill_color='white', background_fill_alpha=1.0)
    p.add_layout(ioa_percent)

    p.add_tools(
        HoverTool(
            #names=labels,
            tooltips=[('label', '@label'), ('start', '@start'), ('end', '@end')]
        )
    )

    p.legend.title = 'Labels'
    p.legend.title_text_font_style = 'bold'
    p.legend.title_text_font_size = '20px'
    p.xaxis.axis_label = 'Timeline (seconds)'
    p.xaxis.ticker = np.arange(0, int(max_end) + 1, 2)
    p.xaxis.bounds = (0, int(max_end) + 1)
    p.yaxis.axis_label = 'Observer'
    p.yaxis.major_label_text_color = None
    p.yaxis.major_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.ygrid.grid_line_dash = [6, 4]
    p.x_range.min_interval = 7
    
    save(p)

if __name__ == '__main__':
    # O1 = np.array([
    #     (0.000001, 0.654573, 'R'),
    #     (0.100000, 0.554573, 'M'),
    #     (0.654573, 1.000000, 'R'),
    #     (0.654573, 1.000000, 'T'),
    #     (1.000000, 1.500000, 'R'),
    # ], dtype=data_type)
    # rO1 = np.array([
    #     (0.000000, 0.100000, 'R'),
    #     (0.100000, 0.554573, 'MR'),
    #     (0.554573, 0.654573, 'R'),
    #     (0.654573, 1.000000, 'RT'),
    #     (1.010000, 1.500000, 'R'),
    # ], dtype=data_type)
    # O2 = np.array([
    #     (0.000001, 0.100000, 'R'),
    #     (0.090000, 0.654573, 'R'),
    #     (0.654573, 1.047317, 'T'),
    #     (1.000000, 1.600000, 'R'),
    # ], dtype=data_type)
    label_rev = 'Rev01'
    label_path = './labels/'
    label_ext = 'txt'
    labels = ["R", "BV", "M", "N", "T"]
    file_paths = sorted([abspath(f'{label_path}/{x}') for x in listdir(label_path) if x.split('.')[-1] == label_ext and label_rev in x.split('.')])
    sample = load_labels(file_paths, labels)
    O1 = sample.get('O1')
    O2 = sample.get('O2')

    pO1 = create_time_continuous_array(O1)
    # print('R1:', pO1)
    # assert np.array_equal(pO1, rO1)

    pO2 = create_time_continuous_array(O2)
    # print('R2:', pO2)

    max_end = get_max_end(O1, O2)
    print('max:', max_end)
    print('min/max:', get_min_max_start_end(O1, O2))

    matching = matches_timelines(pO1, pO2)
    print('S:', matching)

    track_O1 = to_track_like(pO1, max_end)
    track_O2 = to_track_like(pO2, max_end)
    assert track_O1.size == track_O2.size

    kappa = metric_interannotator_agreement_coefficients(track_O1, track_O2)
    print(f'[INFO] Cohen\'s Kappa: {kappa}%')

    color_map = {
        'R': '#CAB2D6',
        'BV': 'green',
        'M': 'purple',
        'N': 'yellow',
        'T': 'blue',
        'agreement': 'green',
        'disagreement': 'red'
    }
    chart(sample, matching, labels, max_end, kappa, color_map)
