from contextlib import ExitStack
from os import listdir
from os.path import abspath

from src.constants import DIRNAME
from src.validation import validate

def getListdir():
    return listdir(DIRNAME)

def getAbsdir(file):
    return abspath(DIRNAME + '/' + file)

def openStack():
    result = []
    filespath = [getAbsdir(x) for x in getListdir()]
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filespath]
        for file in files:
            result += [validate(file)]
    return result