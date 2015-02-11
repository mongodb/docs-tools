"""
Given a a specification of an image, and an ``svg`` in the configured image
directory, build desired image artifacts (using ``inkscape``) as well as an
``rst`` file that includes all of content to include the image in the
output.

With images generated from SVG, we separate the generation of build artifacts
(images) from their source, which means the documentation can use
output-specific images and potentially translate the text in the diagrams. By
generating all of the ``rst`` to inclde the images, its possible display and
maintain the presentation of images systematically and centrally.

The format of the image specification is: ::

  {
    "name": <imgBaseName>,
    "alt": <text>,
    "output": [
      {
        "type": <string>,
        "tag": <string>,
        "dpi": <int>,
        "width": <int>
      },
    ]
  }

The ``tag`` field is optional and appends a string to the generated file name,
to facilitate multiple output targets without having conflicting file names.

The ``<imgBaseName>`` is the name of the ``.svg`` file without the
extension. The main image-generation operation is in
:func:`giza.content.images.image_tasks()`, while definition of the `rst`` content
is in :func:`giza.content.images.generate_image_pages()`.
"""
