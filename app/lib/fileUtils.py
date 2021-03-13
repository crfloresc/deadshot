from contextlib import ExitStack
from os import listdir
from os.path import abspath

from app.constants import DIRNAME
from app.lib.validation import validate

def getAbsdir(path, file):
    return abspath(f'{path}/{file}')

def openStack(path):
    result = []
    filespath = [getAbsdir(path, x) for x in listdir(path)]
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filespath]
        for file in files:
            result += [validate(file)]
    return result