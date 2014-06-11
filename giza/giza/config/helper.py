from giza.config.main import Configuration

def configuration(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    return c
