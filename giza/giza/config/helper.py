from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig

def fetch_config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    return c

def new_config():
    args = RuntimeStateConfig()

    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    return c
