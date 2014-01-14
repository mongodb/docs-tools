import os.path

def concat(*args):
    return ''.join(args)

def dot_concat(*args):
    return '.'.join(args)

def hyph_concat(*args):
    return '-'.join(args)

def path_concat(*args):
    return os.path.sep.join(args)

