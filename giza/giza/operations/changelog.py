import logging
import argh

logger = logging.getLogger('giza.jeerah.client')


@argh.expects_obj
@argh.arg("changelog_version", default=None)
@argh.named("cl")
def main(args):
    pass
