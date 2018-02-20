from docutils import nodes
from docutils.parsers.rst import directives
import sphinx.directives.code


class code_button_row(nodes.Element):
    pass


def visit_code_button_row(self, node):
    start_tag = self.starttag(node, 'div', CLASS='button-row')
    self.body.append(start_tag)


def depart_code_button_row(self, node):
    self.body.append('</div>\n')


class code_button(nodes.Element):
    pass


def visit_code_button(self, node):
    x = node.get('href', False)
    if x:
        start_tag = self.starttag(node, 'a', CLASS='code-button',
                                  href=x, target="_blank")
    else:
        start_tag = self.starttag(node, 'a', CLASS='code-button')

    self.body.append(start_tag)


def depart_code_button(self, node):
    self.body.append(node['text'][0] + '</a>\n')


class code_container(nodes.Element):
    pass


def visit_code_container(self, node):
    start_tag = self.starttag(node, 'div', CLASS='button-code-block')
    self.body.append(start_tag)


def depart_code_container(self, node):
    self.body.append('</div>\n')


def create_button(button_type, link):
    """Create a button inside of a code block with the given label and link."""
    button = code_button('')
    button['text'] = [button_type]

    if link:
        button['href'] = [link]

    return button


class CodeBlock(sphinx.directives.code.CodeBlock):
    """
    Add copy, show in stitch, and github buttons to code block.
    """
    option_spec = sphinx.directives.code.CodeBlock.option_spec.copy()
    option_spec.update({
        'button-github': directives.uri,
        'button-stitch': directives.uri,
        'copyable': lambda argument: directives.choice(argument,
                                                       ('yes', 'no', None)),
    })

    def run(self):
        options = self.options

        container = code_container('')
        codeblock = sphinx.directives.code.CodeBlock.run(self)
        br = code_button_row('')

        if options.get('copyable', 'yes') != 'no':
            codeblock[0]['classes'] += ['copyable-code']
            br += create_button('copy', False)

        if options.get('button-github'):
            br += create_button('github', options['button-github'])

        if options.get('button-stitch'):
            br += create_button('stitch', options['button-stitch'])

        container += br
        container += codeblock
        return [container]


def setup(app):
    app.add_node(code_button_row, html=(
        visit_code_button_row, depart_code_button_row
    ))
    app.add_node(code_button, html=(
        visit_code_button, depart_code_button
    ))
    app.add_node(code_container, html=(
        visit_code_container, depart_code_container
    ))
    directives.register_directive('code-block', CodeBlock)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
