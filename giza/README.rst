=================================
Giza -- Documentation Build Tools
=================================

Giza is a collection of tools built around `Sphinx
<http://sphinx-doc.org/>`_, that coordinates assembling, building, and
deploying documentation. Giza primarily addresses the MongoDB
documentation project; however, its design is sufficiently generic to
be able to facilitate the builds of multiple documentation resources
produced at MongoDB.

Resources
---------

`Giza on PyPi <https://pypi.python.org/pypi/giza/0.2.3>`_

`Giza on Github <https://github.com/mongodb/docs-tools/tree/master/giza>`_

File issues in the `MongoDB DOCS Jira Project
<https://jira.mongodb.org/browse/DOCS>`_.

Installation
------------

Giza is available in PyPi, and all dependencies and the package
handles all dependencies and version management. For most use, you
will want to install Giza using the specification in the
``requirements.txt`` file in the repository and branch you want to
build. Use the following command: ::

   pip install -r requirements.txt

While most branches will use the latest version of the software, at
some point in the future, it may only be possible to build some older
branches with a specific version of Giza. Using ``requirements.txt``
ensure that you will always install the correct version of Giza.

At any time, you can install the latest version with the following
``pip`` command: ::

   pip install giza

To install the optional ``github`` and ``jira`` integration, use the
following command: ::

   pip install giza [jira,github]

Additional Components
---------------------

Beyond the ``giza`` command, the Giza package includes several
additional utilities that address various needs of the documentation
project:

``scrumpy`` provides reports that help us manage our SCRUM and sprint,
as well as help with Jira triage and backlog management.

``mdbpr`` is a tool that integrates with Github to identify pull
requests that appropriate for merging.

These components are simple but contain additional dependencies and
do *not* share the same root configuration structure with regards to
the main ``giza`` application. Furthermore, their functionality is not
likely to be relevant for a majority of Giza users.
