import hashlib
import os
import shutil
import tarfile
import logging

logger = logging.getLogger(os.path.basename(__file__))

def tarball(name, path, sourcep=None, newp=None, cdir=None):
    tarball_path = os.path.dirname(name)
    if not os.path.exists(tarball_path):
        os.makedirs(tarball_path)

    with tarfile.open(name, 'w:gz') as t:
        if newp is not None:
            arcname = os.path.join(newp, os.path.basename(path))
        else:
            arcname = None

        if cdir is not None:
            path = os.path.join(cdir, path)

        t.add(name=path, arcname=arcname)

    logger.info('created tarball: {0}'.format(name))

def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink(name, target)
        except ImportError:
            logger.error("platform does not contain support for symlinks. Windows users need to pywin32.")
            exit(1)

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

class FileOperationError(Exception): pass

def copy_always(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False:
        msg = "{0}: Input file '{1}' does not exist.".format(name, source_file)
        logger.critical(msg)
        raise FileOperationError(msg)
    else:
        if not os.path.exists(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

    logger.debug('{0}: copied {1} to {2}'.format(name, source_file, target_file))

def copy_if_needed(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False or os.path.isdir(source_file):
        msg = "{0}: Input file '{1}' does not exist.".format(name, source_file)
        logger.critical(msg)
        raise FileOperationError(msg)
    elif os.path.isfile(target_file) is False:
        if not os.path.exists(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

        if name is not None:
            logger.debug('{0}: created "{1}" which did not exist.'.format(name, target_file))
    else:
        if md5_file(source_file) == md5_file(target_file):
            if name is not None:
                logger.debug('{0}: "{1}" not changed.'.format(name, source_file))
        else:
            shutil.copyfile(source_file, target_file)

            if name is not None:
                logger.debug('{0}: "{1}" changed. Updated: {2}'.format(name, source_file, target_file))

def create_link(input_fn, output_fn):
    out_dirname = os.path.dirname(output_fn)
    if out_dirname != '' and not os.path.exists(out_dirname):
        os.makedirs(out_dirname)

    if os.path.islink(output_fn):
        os.remove(output_fn)
    elif os.path.isdir(output_fn):
        msg = "link: {1} exists and is a directory".format(output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    elif os.path.exists(output_fn):
        msg = 'could not create a symlink at {1}.'.format('link', output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    out_base = os.path.basename(output_fn)
    if out_base == "":
        msg = 'could not create a symlink at {1}.'.format('link', output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    else:
        symlink(out_base, input_fn)
        os.rename(out_base, output_fn)
        logger.debug('{0} created symbolic link pointing to "{1}" named "{2}"'.format('symlink', input_fn, out_base))

def decode_lines_from_file(fn):
    with open(fn, 'r') as f:
        return [ line.decode('utf-8').strip() for line in f.readlines() ]

def encode_lines_to_file(fn, lines):
    with open(fn, 'w') as f:
        f.write('\n'.join(lines).encode('utf-8'))
