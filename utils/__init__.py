try:
    from files import symlink, expand_tree, md5_file
    from git import get_commit, get_branch
    from output import build_platform_notification, log_command_output, swap_streams
    from serialization import (ingest_yaml_list, ingest_yaml_doc, ingest_yaml,
                               write_yaml, ingest_json, ingest_json_list)
    from shell import shell_value
    from strings import concat, dot_concat, hyph_concat, path_concat
    from structures import AttributeDict, BuildConfiguration, get_conf_file, conf_from_list
    from transformations import munge_page, munge_content
except ImportError:
    print('[utils]: skipping compatibility imports during bootstrap. '
          'If you see this and you are **not** bootstrapping, investigate before continuing.')
