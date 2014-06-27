import os.path
import datetime

def concat(*args):
    return ''.join(args)

def dot_concat(*args):
    return '.'.join(args)

def hyph_concat(*args):
    return '-'.join(args)

def slash_concat(*args):
    return '/'.join(args)

def path_concat(*args):
    return os.path.sep.join(args)

def timestamp(form='filename'):
    if form == 'filename':
        return datetime.datetime.now().strftime("%Y-%m-%d.%H-%M")
    else:
        return datetime.datetime.now().strftime("%Y-%m-%d, %H:%M %p")
