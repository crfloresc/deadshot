from contextlib import ExitStack
from typing import List, Union
from os.path import abspath, basename, normpath
import re


def validate_segmentions(buffer, validLabels, audioDuration, removeNumberFromLabels):
    '''
    @deprecated
    '''
    currOwner, temp = None, []
    for line in buffer.readlines():
        lineFormated = format_line(line)
        if len(lineFormated) != 3 or lineFormated[0] == '\\':
            continue
        if not currOwner:
            currOwner = buffer.name.split('/')[-1][0:2]
        label = lineFormated[2].replace(' ','')
        if removeNumberFromLabels:
            label = label[0] if is_number(label) else label
        if label in validLabels:
            start = float(lineFormated[0].replace(',','.'))
            if start >= audioDuration:
                continue
            end = float(lineFormated[1].replace(',','.'))
            temp.append((start, end, label))
    return temp

def __test_validate_segmentions(
    buffer,
    valid_labels,
    audio_duration,
    remove_numbers_from_labels
) -> List[tuple]:
    segmentions = []

    for line in buffer:
        formatted_line = format_line(line).replace(' ', '')
        if len(formatted_line) != 3 or formatted_line[0] == '\\':
            continue

        label = formatted_line[2]
        if remove_numbers_from_labels and is_number(label):
            label = label[0]

        if label not in valid_labels:
            continue

        start = float(formatted_line[0].replace(',', '.'))
        end = float(formatted_line[1].replace(',', '.'))

        if start >= audio_duration:
            continue

        segmentions.append((start, end, label))

    return segmentions

def load_labels(
    file_paths: List[str],
    labels: List[str],
    __path: str,
    __rev: str,
) -> Union[dict, str]:
    sample_data = dict()
    sample_name = basename(normpath(abspath(__path)))
    max_duration = find_greatest_number(file_paths)
    print(f'[INFO] load_labels: max_duration: {max_duration}, name: {sample_name}')

    with ExitStack() as stack:
        files_data = [stack.enter_context(open(filename)) for filename in file_paths]
        for file_buffer in files_data:
            observer = file_buffer.name.split('/')[-1][:2]
            segmentions = validate_segmentions(file_buffer, labels, max_duration, False)
            sample_data.update({ observer: segmentions })
    return sample_data, f'{sample_name}-{__rev}'

def find_greatest_number(file_paths):
    greatest_number = float('-inf')
    pattern = re.compile(r"(\d+[\.,]\d+)\t(\d+[\.,]\d+)?\t?([a-zA-Z_]?)\n?")

    for file_path in file_paths:
        with open(file_path, 'r') as file:
            for line in file:
                match = pattern.match(line)
                if match:
                    numbers = [float(match.group(1).replace(',', '.'))]
                    if match.group(2):
                        numbers.append(float(match.group(2).replace(',', '.')))
                    greatest_number = max(greatest_number, max(numbers))

    if greatest_number == float('-inf'):
        raise Exception('No numbers found in the files')

    return greatest_number

def format_line(line):
    cleanLinebreak = line.split('\n')[0:1]
    return cleanLinebreak[0].split('\t')

def is_number(string: str) -> bool:
    return any(char.isdigit() for char in string)
