def munge_page(fn, regex, out_fn=None,  tag='build'):
    with open(fn, 'r') as f:
        page = f.read()

    page = munge_content(page, regex)

    if out_fn is None:
        out_fn = fn

    with open(out_fn, 'w') as f:
        f.write(page)

    print('[{0}]: processed {1}'.format(tag, fn))

def munge_content(content, regex):
    if isinstance(regex, list):
        for cregex, subst in regex:
            content = cregex.sub(subst, content)
        return content
    else:
        return regex[0].sub(regex[1], content)
