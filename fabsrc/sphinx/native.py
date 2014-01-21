def sphinx_native_worker(sphinx_cmd):
    # Calls sphinx directly rather than in a subprocess/shell. Not used
    # currently because of the effect on subsequent multiprocessing pools.

    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    sp_cmd = __import__('sphinx.cmdline')

    sphinx_argv = sphinx_cmd.split()

    with swap_streams(StringIO()) as _out:
        r = sp_cmd.main(argv=sphinx_argv)
        out = _out.getvalue()

    if r != 0:
        exit(r)
    else:
        return r
