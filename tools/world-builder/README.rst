========================================================
MongoDB Documentation World Builder for Legacy Toolchain
========================================================

This directory contains the MongoDB Documentation World Builder. The
World Builder provides a centralized way of building **and deploying**
all MongoDB documentation projects that build with the legacy toolchain
(i.e. giza/sphinx).

Quick Start
-----------

Run ``./build.py`` to build and deploy all MongoDB documentation projects.

Build and Deploy Specific Targets
---------------------------------

The World Builder can also fetch and build specific projects using
shell-style glob expressions on git repository names.

For example, if you only want to build mms projects, then you might run
the following:

.. code::

   ./build.py 'mms-docs*'
