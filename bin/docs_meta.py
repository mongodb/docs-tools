"""
This file used to have all of the build configuration mangling and the project
specific build tools. That content is now all in the utils package, in:

- utils.config

  All project-agnostic configuration file mangling and handling.

- utils.project

  All project-specific configuration management.

The current files is just a shim to provide compatibility.
"""

from utils.serialization import write_yaml, ingest_yaml
from utils.shell import shell_value
from utils.git import get_commit, get_branch
from utils.structures import BuildConfiguration, AttributeDict, get_conf_file
from utils.config import load_conf, lazy_conf, get_conf
from utils.project import is_processed, get_manual_path, get_path, get_versions, edition_setup
