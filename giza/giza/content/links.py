import os.path
from giza.files import create_link
from giza.serialization import ingest_yaml_doc

def _link_path(path, conf):
    return os.path.join(conf.paths.projectroot,
                        conf.paths.public,
                        path)

def get_top_level_links(links, conf):
    ret = []

    def process_target_list(lst):
        for name, target in lst.items():
            if target == '{{current_branch}}':
                target = conf.git.branches.current

            yield ( _link_path(name, conf), target )

    if isinstance(links, list):
        for link in links:
            ret.extend(process_target_list(link))
    else:
        ret.extend(process_target_list(links))

    return ret


def create_manual_symlink(conf):
    fpath = os.path.join(conf.paths.projectroot,
                         conf.paths.builddata, 'integration.yaml')
    if os.path.exists(fpath):
        iconf = ingest_yaml_doc(fpath)
    else:
        return False

    if 'base' not in iconf:
        return True
    else:
        if 'links' not in iconf['base']:
            return True
        else:
            links = get_top_level_links(iconf['base']['links'], conf)

            if links:
                for name, target in links:
                    create_link(target, name)
