===================================
MongoDB Documentation World Builder
===================================

This directory contains the MongoDB Documentation World Builder. The World
Builder provides a centralized way of building all MongoDB documentation
projects.

Quick Start
-----------

* Install `ninja <http://ninja-build.org/>`_ and giza.
* Run ``ninja`` to build all MongoDB documentation projects.

Building Specific Targets
-------------------------

The World Builder can also fetch and build specific projects. Run
``ninja -t targets`` for a list of all available targets.

For example, if you only want to build mms projects, then you might run
the following:

.. code::

   ninja build/mms-docs/master \
         build/mms-docs/v2.0 \
         build/mms-docs/v1.8 \
         build/mms-docs/v1.6 \
         build/mms-docs/v1.4 \
         build/mms-docs/v1.2 \
         build/mms-docs/v1.1

Special Targets
---------------

* ``ninja update``: Run ``git fetch`` in all ``source/`` directories.
