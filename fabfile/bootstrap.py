from fabric.api import task, local

from docs_meta import output_yaml

@task
def meta(filename):
    output_yaml(filename)
    
