import base64
import numpy as np
import re
import math
from os import listdir
from os.path import abspath
from config import config
from logger import log


np.set_printoptions(suppress=True)
data_type = np.dtype([('start', np.float32), ('end', np.float32), ('label', np.dtype('U255'))])
consensus_type = np.dtype([('start', np.float32), ('end', np.float32), ('kind', np.dtype('U255'))])
agreement_const = 'agreement'
disagreement_const = 'disagreement'

def create_time_continuous_array(data, debug=False):
    i = 0
    max_data = len(data) - 1

    while i < max_data:
        simmetric_differences, len_sd = symmetric_difference(data[i], data[i+1])
        if debug: log.debug('<---d: %s', data[i], data[i+1])
        if debug: log.debug('<---sd: %s', simmetric_differences, len_sd)
        if len_sd > 0:
            data = np.delete(data, [i, i+1])
            data = np.append(data, simmetric_differences)
            data = np.sort(data, order=['start', 'end'])
        if len_sd != 0:
            i = 0
            max_data = len(data) - 1
            if debug: log.debug('reset!')
        else:
            i += 1

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
        l = a_label + config.general.id_separator + b_label
        l = config.general.id_separator.join(l.split(config.general.id_separator))
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
            diff_start_is_close = np.isclose([max_time_diff], [diff_start], rtol=config.general.float_tol)[0]
            diff_end_is_close = np.isclose([max_time_diff], [diff_end], rtol=config.general.float_tol)[0]
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

def validate_segmentions(buffer, valid_labels):
    segments = []

    for i, line in enumerate(buffer.readlines()):
        try:
            if config.general.id_separator in line:
                log.warning(f'Found prohibid char in {line!a}, omitting line {i + 1}.')
                continue

            parts = line.strip().split('\t')
            if len(parts) != 3 or parts[0] == '\\':
                log.warning(f'Found invalid value {line!a}, omitting line {i + 1}.')
                continue

            label = parts[2].strip()
            if config.audacity.only_alphabetic_label and bool(re.search(r'[^A-Za-z]', label)):
                log.warning(f'Found not formatted label {line!a}, formatting...')
                label = re.sub(r'[^A-Za-z]', '', label)

            if label not in valid_labels:
                log.warning(f'Found not definited label {line!a}, omitting line {i + 1}.')
                continue

            start = float(parts[0].replace(config.audacity.num_separator, '.'))
            end = float(parts[1].replace(config.audacity.num_separator, '.'))

            if config.audacity.non_negative and (start < 0 or end < 0):
                log.warning(f'Found negative value {parts}, omitting line {i + 1}.')
                continue

            segments.append((start, end, label))
        except Exception as e:
            if config.audacity.omit_exceptions == False:
                raise e
            log.warning(f'Found invalid value {line!a}, omitting line {i + 1}, detail: {e}.')

    return np.array(segments, dtype=data_type)

def load_labels():
    from contextlib import ExitStack

    label_rev = config.sample.rev
    label_path = config.sample.path
    label_ext = config.sample.ext
    labels = config.sample.labels
    file_paths = sorted([abspath(f'{label_path}/{x}') for x in listdir(label_path) if x.split('.')[-1] == label_ext and label_rev in x.split('.')])

    sample_data = dict()

    with ExitStack() as stack:
        files_data = [stack.enter_context(open(filename)) for filename in file_paths]
        unpacked_files_data = { file_buffer.name.split('/')[-1][:2]:file_buffer for file_buffer in files_data }
        sample_data = { key:validate_segmentions(buffer, labels) for key, buffer in unpacked_files_data.items() }
    return sample_data

def chart(sample, agreement, labels, min_time, max_time, measure, color_map):
    from bokeh.plotting import figure, save, output_file
    from bokeh.models import Range1d, Label, HoverTool, ColumnDataSource, BoxAnnotation, HBar

    start_on = 0 if config.chart.always_start_on_zero == True else min_time
    p = figure(
        title='IOA',
        tools='wheel_zoom, pan, save, reset',
        y_range=Range1d(bounds=(0, 1)),
        x_range=(start_on-2, start_on+60),
        sizing_mode='stretch_both',
        output_backend='webgl'
    )

    log.info('Rendering main')
    label_render_pos_map = { label:(i+1)/500 for i, label in enumerate(labels) }
    observer_render_pos = 0.55
    for observer_key, events in sample.items():
        observer_render_pos -= 0.05
        p.add_layout(Label(x=start_on, y=observer_render_pos,
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
                   name='main_renderer', line_color=color,
                   line_alpha=0.7, fill_color=color,
                   fill_alpha=0.7, source=source)

    log.info('Rendering legends')
    for label in labels:
        p.line(x=[1], y=[1], line_color=color_map.get(label),
               legend_label=label, line_width=2)

    log.info('Rendering agreement bars')
    consensus = np.array([], dtype=consensus_type)
    last_end = min_time

    for start, end, _ in agreement:
        # Check for gaps before the current agreement
        if start > last_end:
            consensus = np.append(consensus, np.array([(last_end, start, disagreement_const)], dtype=consensus_type))
        
        # Merge contiguous agreements
        if consensus.size > 0 and consensus[-1]['kind'] == agreement_const:
            consensus[-1]['end'] = max(consensus[-1]['end'], end)  # Update the last agreement end
        else:
            consensus = np.append(consensus, np.array([(start, end, agreement_const)], dtype=consensus_type))
        
        last_end = consensus[-1]['end']  # Update the last end

    # Check if there is time left after the last agreement until max_time
    if last_end < max_time:
        consensus = np.append(consensus, np.array([(last_end, max_time, disagreement_const)], dtype=consensus_type))

    for start, end, kind in consensus:
        color = color_map.get(kind)
        rail = 0.4
        if kind == disagreement_const:
            p.quad(name=disagreement_const, left=start, right=end, top=1, bottom=0, alpha=0.08, color=color)
        p.hbar(y=rail, height=0.007,
               left=start, right=end,
               line_color=color, line_alpha=1,
               fill_color=color, fill_alpha=1, name='consensus_renderer')

    log.info('Rendering IOA percentage')
    ioa_percent = Label(x=70, y=500,
                        x_units='screen', y_units='screen',
                        text=f'Cohen\'s Kappa: {measure}%', #render_mode='css',
                        border_line_color='black', border_line_alpha=0.9,
                        background_fill_color='white', background_fill_alpha=1.0)
    p.add_layout(ioa_percent)

    log.info('Adding chart tools')
    hover = HoverTool(tooltips=[
        ('label', '@label'),
        ('start', '@start'),
        ('end', '@end'),
    ], renderers=[*p.select(name='main_renderer')])
    p.add_tools(hover)

    log.info('Changing general layout')
    p.legend.title = 'Labels'
    p.legend.title_text_font_style = 'bold'
    p.legend.title_text_font_size = '20px'
    p.xaxis.axis_label = 'Timeline (seconds)'
    p.xaxis.ticker = np.arange(start_on, int(max_time), 2)
    p.xaxis.bounds = (start_on, max_time)
    p.yaxis.axis_label = 'Observer'
    p.yaxis.major_label_text_color = None
    p.yaxis.major_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    p.ygrid.grid_line_dash = [6, 4]
    p.x_range.min_interval = 7

    log.info('Saving chart')
    output_file(filename=config.sample.save_path+'test.html')
    save(p)
    log.info('Saved chart')

def create_deterministic_id(*inputs):
    combined_input = config.general.id_separator.join(sorted(inputs))
    encoded_id = base64.urlsafe_b64encode(combined_input.encode()).decode('utf-8')
    return encoded_id

def reverse_deterministic_id(encoded_id):
    decoded_string = base64.urlsafe_b64decode(encoded_id.encode()).decode('utf-8')
    inputs = decoded_string.split(config.general.id_separator)
    return inputs

if __name__ == '__main__':
    # O1 = np.array([
    #     (0.000001, 0.654573, 'R'),
    #     (0.100000, 0.554573, 'M'),
    #     (0.654573, 1.000000, 'Z'),
    #     (0.654573, 1.000000, 'A'),
    #     (0.654573, 1.000000, 'R'),
    #     (1.000000, 1.500000, 'R'),
    # ], dtype=data_type)
    # rO1 = np.array([
    #     (0.000000, 0.100000, 'R'),
    #     (0.100000, 0.554573, 'M|R'),
    #     (0.554573, 0.654573, 'A'),
    #     (0.654573, 1.000000, 'A|R|Z'),
    #     (1.010000, 1.500000, 'R'),
    # ], dtype=data_type)
    # O2 = np.array([
    #     (0.000001, 0.100000, 'R'),
    #     (0.090000, 0.654573, 'R'),
    #     (0.654573, 1.047317, 'T'),
    #     (1.000000, 1.600000, 'R'),
    # ], dtype=data_type)
    sample = load_labels()
    O1 = sample.get('O1')
    O2 = sample.get('O2')

    pO1 = create_time_continuous_array(O1)
    log.debug('R1: %s', pO1)
    # assert np.array_equal(pO1, rO1)

    pO2 = create_time_continuous_array(O2)
    log.debug('R2: %s', pO2)

    min_time, max_end = get_min_max_start_end(O1, O2)
    log.info('max: %s', get_max_end(O1, O2))
    log.info('min/max: %s %s', min_time, max_end)

    matching = matches_timelines(pO1, pO2)
    log.debug('S:', matching)

    track_O1 = to_track_like(pO1, max_end)
    track_O2 = to_track_like(pO2, max_end)
    assert track_O1.size == track_O2.size

    kappa = metric_interannotator_agreement_coefficients(track_O1, track_O2)
    log.info(f'Cohen\'s Kappa: {kappa}%')

    color_map = {
        'R': '#7e7e7e', # cab2d6 black
        'BV': '#b3de69', # green
        'M': '#8565c4', # b19cd9 violet
        'C': '#e6e600', # yellow
        'T': '#1e7dff', # 1e90ff blue
        'agreement': '#00b300', # green
        'disagreement': '#ff8989' # red
    }
    chart(sample, matching, config.sample.labels, min_time, max_end, kappa, color_map)

    # id1 = create_deterministic_id('R', 'T', 'R', 'R')
    # print(id1)
    # print(reverse_deterministic_id(id1))

    # id2 = create_deterministic_id('R', 'R', 'R', 'T')
    # print(id2)
    # print(reverse_deterministic_id(id2))
