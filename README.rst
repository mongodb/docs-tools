===========================================================================
``docs-tools`` -- Buildsystem Components for MongoDB Documentation Projects
===========================================================================

``docs-tools`` holds all common build system components for MongoDB
documenting projects (e.g. the MongoDB Manual, MongoDB Ecosystem
Documentation, etc.) These tools include: Sphinx extensions, the
meta-build system, themes, deployment and orchestration scripts, and
scripts that generate common restructured text elements.

The goal of ``docs-tools`` is to totally remove all programs from the
documentation source trees to facilitate maintenance of these
components in the context of a multi-branch and multi-repository
documentation project.

This document explains the componets and operations of the build
system, and serves as a guide for anyone who wants to maintain a
MongoDB Documentation-like project. 

Components
----------

``fabfile`` (orchestration and scripts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`fabric <http://fabfile.org/>`_ is a deployment orchestration system
that provides simple and convenient Python interfaces for shell
scripting and task running. ``docs-tools`` uses fabric tasks for two
purposes: 

#. to deploy build products to testing and production environments.
  
#. to bundle groups of related operations in a consistent and simple
   interface. 
   
Historically, these operations were a mixture of multi-step makefile
targets, shell scripts, and Python programs. Combining all of these
operations into a single interface increases portability, consistency,
and overall reliability of the build systems.

``makecloth`` (meta-build system)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Makecloth <https://pypi.python.org/pypi/buildcloth/>`_ is a
meta-build tool that generates build specifications
(e.g. ``Makefiles`` and ``ninja.build`` files.) Makecloth makes it
possible to take advantage of the dependency resolution and
concurrency features of a robust and stable buildsystem while mostly
writing Python rather than a build tool specific specification.

In the ``docs-tools`` implementation, Makecloth scripts generate
buildscripts based on project-specific data supplied with the source
data, so that many projects can use common logic. See the `build data
for the MongoDB Manual <https://github.com/mongodb/docs/tree/master/bin/builddata>`_ 
for an example.

``rstcloth`` (rst generation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`rstcloth <https://pypi.python.org/pypi/rstcloth>`_ use the model of
*makecloth* but generates reStructuredText: In some situations, it
makes sense to generate ``rst`` programatically rather than maintains
that content manually. 

For example: 

- to make tables, it often makes more sense to generate the table
  based on more generic data than to build the table directly in
  restructured text, given the flexibility of the table syntax.

- to keep multiple related pieces of content in sync, it often makes
  sense to generate when two pieces of content derive from the same
  source but need different reStructuredText forms.
  
- to enforce common formatting requirements centrally for forms that
  appear throughout the documentation.

This approach allows minimally invasive generation of output for
multiple formats and reduces the amount of custom template logic.

``sphinxext`` (Sphinx)
~~~~~~~~~~~~~~~~~~~~~~

This directory contains conventional `Sphinx <http://sphinx-doc.org>`_
extensions, required for producing and referencing MongoDB
documentation projects. This includes the extensions for the MongoDB
Domain to cross reference MongoDB objects (database commands, shell
methods, database output, etc.) as well as custom admonition and
directive types. 

``themes`` (Sphinx)
~~~~~~~~~~~~~~~~~~~

These are standard Sphinx themes customized for MongoDB documentation
projects, centralized here for ease of use across projects.

``dtf`` (testing)
~~~~~~~~~~~~~~~~~

`dtf <https://pypi.python.org/pypi/dtf/>`_ is a consistency testing
framework for documentation projects to provide ways of enforcing
conventions in documentation. The content of these scripts just
include the test logic, and not the testing running architecture, or
data used to define testable situations.

``bin`` (utilities)
~~~~~~~~~~~~~~~~~~~

The scripts in the ``bin`` directory include common components and
logic shared between bootstrapping operations, fabric scripts, and
meta-build scripts.

Bootstrapping
-------------

`bootstrap.py
<https://github.com/mongodb/docs-tools/blob/master/bin/bootstrap.py>`_
is an example bootstrapping script that intializes a ``docs-tools``
based repository. 

Integration and Getting Started
-------------------------------

See `the mongodb manual repository <https://github.com/mongodb/docs>`_
for an example of an integrated repository using
``docs-tools``. In particular, note the `docs_meta.yaml
<https://github.com/mongodb/docs/blob/master/bin/docs_meta.yaml>`
file: this is the only strict requirement for ``docs-tools``.

Copy the `bootstrap.py
<https://github.com/mongodb/docs-tools/blob/master/bin/bootstrap.py>`_
script in the top level of your repository and create a
``docs_meta.py`` file in the ``bin/`` directory of your
repository. You can now run the following command to bootstrap your
build system: :: 

   python bootstrap.py

To begin using the meta-build system, specify a generated makefile in
the ``build.system.files`` list in the ``docs_meta.py`` file. This
will correspond to one of the scripts in the ``makecloth/`` directory
of ``docs-tools``. Then in your ``makefile``, include the following
bootstrapping content: :: 

   output = build
   tools = $(output)/docs-tools

   .PHONY:$(output)/makefile.meta
   -include $(output)/makefile.meta

   build/makefile.meta:$(tools)/makecloth/meta.py
        @mkdir -p $(output)
        @python $< $@

Modify the ``tools`` variable if you downloaded ``docs-tools`` to an
alternate location. You may also include the following bootstrapping
helper target: ::

   bootstrap fabfile build/docs-tools:
        @python bootstrap.py
        @echo "[bootstrap]: configured build environment."

Some of the makecloth files require a corresponding ``yaml`` file in
the directory specified in the ``build.paths.builddata`` field of
``docs_meta.yaml``. 

To generate the run ``make`` without any arguments.

Extension and Development
-------------------------

There are several ways to add functionality to the build system:

- add additional tasks to the ``fabfile`` modules according to
  standard fabric development practices.

- add additional rstcloth generated files. These scripts typically
  take inputs via arguments on the command line or a file passed in on
  the command line. For integration, add corresponding makecloth
  scripts to generate build instructions.

- add additional makecloth files for additional processing and build
  products. Add generated makecloth files to the
  ``build.system.files`` in ``docs_meta.yaml`` to generate a new
  makefile.

Forthcoming/TODO
----------------

- improve documentation of each makecloth's purpose and use.

- expand documentation of makecloth data forms and schema.

- improve symlink handling throughout makecloth (for windows
  compatibility.)

- stabilize makecloth and rstcloth and move them out of the tree. 
  
- build helpers for working with development virtualenvs. 
  
- make build system fully Python 3 compatible.
