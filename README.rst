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

This document explains the components and operations of the build
system, and serves as a guide for anyone who wants to maintain a
MongoDB Documentation-like project. 

Installation
------------

To install giza, refer to the `installation guide 
<https://docs.mongodb.com/meta/tutorials/install/>`_ on the MongoDB meta site
to help you get started.

Components
----------

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

``giza``
~~~~~~~~

MongoDB's legacy toolchain that extends Sphinx.

