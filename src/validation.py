from src.constants import VALID_LABELS

def formatLine(line):
    cleanLinebreak = line.split('\n')[0:1]
    return cleanLinebreak[0].split('\t')

def validate(file):
    result = {
        'owner': file.name.split('/')[-1][0:2],
        'data': [],
    }
    for line in file.readlines():
        lineFormated = formatLine(line)
        if len(lineFormated) != 3:
            continue
        label = lineFormated[2]
        if label in VALID_LABELS:
            start = float(lineFormated[0].replace(',','.'))
            end = float(lineFormated[1].replace(',','.'))
            result['data'] += [[start, end, label]]
    return result