import hashlib
import os

def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink(name, target)
        except ImportError:
            exit('ERROR: platform does not contain support for symlinks. Windows users need to pywin32.')

def expand_tree(path, input_extension='yaml'):
    file_list = []

    for root, sub_folders, files in os.walk(path):
        for file in files:
            if file.startswith('.#'):
                continue
            elif file.endswith('swp'):
                continue
            else:
                f = os.path.join(root, file)
                if input_extension != None:
                    if isinstance(input_extension, list):
                        if os.path.splitext(f)[1][1:] not in input_extension:
                            continue
                    else:
                        if not f.endswith(input_extension):
                            continue

                file_list.append(f)

    return file_list

def md5_file(file, block_size=2**20):
    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()
