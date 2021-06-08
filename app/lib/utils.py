from os.path import abspath

def containsNumber(string):
    return any(char.isdigit() for char in string)

def getAbsdir(path, file):
    return abspath(f'{path}/{file}')

def formatLine(line):
    cleanLinebreak = line.split('\n')[0:1]
    return cleanLinebreak[0].split('\t')
