===================================
MongoDB Documentation World Builder
===================================

This directory contains the MongoDB Documentation World Builder. The World
Builder provides a centralized way of building all MongoDB documentation
projects.

Quick Start
-----------

Run ``./build.py`` to build all MongoDB documentation projects.

Building Specific Targets
-------------------------

The World Builder can also fetch and build specific projects using
shell-style glob expressions on git repository names.

For example, if you only want to build mms projects, then you might run
the following:

.. code::

   ./build.py 'mms-docs*'
