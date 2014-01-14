def should_migrate(builder, conf):
    if builder.endswith('-saas') and conf.git.branches.current != 'master':
        return False
    else:
        return True
