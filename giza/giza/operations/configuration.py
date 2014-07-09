import json
import argh

from giza.config.main import Configuration

@argh.arg('--conf_path', '-c')
@argh.arg('--edition', '-e')
@argh.arg('--language', '-l')
@argh.named('config')
def render_config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    # the following values are rendered lazily. we list them here so that the
    # final object will be useful to inspect.

    dynamics = [ c.git.commit, c.paths.public, c.git.branches.current,
                 c.git.branches.manual, c.git.branches.published,
                 c.paths.branch_output, c.paths.buildarchive,
                 c.paths.branch_source, c.paths.branch_staging,
                 c.version.published, c.version.stable, c.version.upcoming,
                 c.project.edition, c.deploy, c.paths.global_config,
                 c.project.branched, c.system.dependency_cache,
                 c.paths.public_site_output, c.project.basepath,
                 c.runstate.runner, c.runstate.force, c.system.files,
                ]

    print('--- ' + "str of config object >>>")
    print(json.dumps(c.dict(), indent=3))
    print('---  <<<')
