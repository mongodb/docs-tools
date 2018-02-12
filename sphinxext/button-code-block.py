import logging
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.directives.code import CodeBlock
import inspect
import copy

logger = logging.getLogger('fasthtml')

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
        start_tag = self.starttag(node, 'a', CLASS='code-button', href=x, target="_blank")
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




def createButton(buttonType, link):
    button = code_button('')
    button['text'] = [buttonType]
    if link:
        button['href'] = [link]
    return button


class ButtonCodeBlock(CodeBlock):
    """
    Add copy, show in stitch, and github buttons to code block.
    """
    # has_content = True
    # required_arguments = 0
    optional_arguments = 3
    option_spec = CodeBlock.option_spec.copy()
    option_spec.update({
        'button-github': directives.unchanged_required,
        'button-stitch': directives.unchanged_required,
        'copyable': directives.flag,
    })

    def run(self):
        options = self.options

        container = code_container('')
        codeblock = CodeBlock.run(self)
        br = code_button_row('')
        
        if options.get('copyable', False) == None:
            copyButton = createButton('copy', False)
            codeblock[0]['classes'] += ['bcb-copyable']
            br += copyButton
            
        if options.get('button-github'):
            br += createButton('github', options['button-github'])
        if options.get('button-stitch'):
            br += createButton('stitch', options['button-stitch'])
        
        container += br
        container += codeblock
        return [container]


def setup(app):
    # app.add_node(bcbnode, html=(visit_bcbnode_node, depart_bcbnode_node))
    app.add_node(code_button_row, html=(
        visit_code_button_row, depart_code_button_row
    ))
    app.add_node(code_button, html=(
        visit_code_button, depart_code_button
    ))
    app.add_node(code_container, html=(
        visit_code_container, depart_code_container
    ))
    app.add_directive('button-code-block', ButtonCodeBlock)
    directives.register_directive('button-code-block', ButtonCodeBlock)
    

    return {
        'parallel_read_safe': False,
        'parallel_write_safe': True,
    }
