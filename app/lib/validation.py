from app.lib.utils import containsNumber

def formatLine(line):
    cleanLinebreak = line.split('\n')[0:1]
    return cleanLinebreak[0].split('\t')

def bufferValidate(buffer, customValidLabels, limit):
    currOwner, temp = None, []
    for line in buffer.readlines():
        lineFormated = formatLine(line)
        if len(lineFormated) != 3 or lineFormated[0] == '\\':
            continue
        if not currOwner:
            currOwner = buffer.name.split('/')[-1][0:2]
        label = lineFormated[2].replace(' ','')
        label = label[0] if containsNumber(label) else label
        if label in customValidLabels:
            start = float(lineFormated[0].replace(',','.'))
            if start >= limit:
                continue
            end = float(lineFormated[1].replace(',','.'))
            temp.append((start, end, label))
    return dict({currOwner: temp})
