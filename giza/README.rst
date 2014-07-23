=================================
Giza -- Documentation Build Tools
=================================

Giza is a collection of tools built around `Sphinx <>`_, that
coordinates assembling, building, and deploying documentation. Giza
primarily addresses the MongoDB documentation project; however, its
design is sufficiently generic to be able to facilitate the builds of
multiple documentation resources produced at MongoDB.

Features and Goals
------------------

Giza has the following objectives and primary features:

- Facilitate fully-local test builds. Contributors to the
  documentation should be able to generate the documentation using the
  exact same process used to produce the production version of the
  resources.

- Generate content from structured forms into reStructuredText that
  Sphinx can publish. In an effort to manage duplicated content, and
  facilitate sustainable content reuse, Giza translates structured
  content, procedures, including command line interfaces, tables of
  contents, and API interfaces.

- Run multiple Sphinx builds concurrently. Practically speaking,
  building the documentation requires running Sphinx multiple
  times. Building the documentation requires multiple invocations of
  Sphinx, to produce:

  - multiple versions of the manual (i.e. HTML, ``json``, PDF, ePub,
    etc.)

  - transitions of the content in different human languages.

  - different editions of a text to address different editions of a
    single resource. (e.g. a student and instructor version of a
    training resource.)

  Internally, Sphinx itself is not optimally parallelized, and
  it's considerably more efficient to run multiple Sphinx processes in
  parallel, particularly for larger resources and as the matrix of
  required build artifacts grows.

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
following command:

   pip install giza [jira,github]

Use
---

Make Interface
~~~~~~~~~~~~~~

Giza is fully integrated into the ``Makefile`` system present in all
MongoDB documentation repositories. Typically you will run builds
using ``make html``, for the html output, or ``make latex`` for the
PDF build. There are two major important targets: ``publish`` that
builds the full production build locally, and ``push`` that is
equivalent to ``publish`` but also uploads all artifacts the resource
to the production web servers.

During the transition to Giza from the legacy system, all Giza
targets have ``giza-`` prefixes, so to use Giza targets you would use
``make giza-html`` and ``make giza-publish``.

Direct Use
~~~~~~~~~~

While most common operations are wrapped in familiar ``make`` targets,
you can run Giza directly from the command line. This section provides
an overview of these operations. See the output of ``-help`` at all
levels for specific syntax.

Sphinx
``````

The following commands will build the ``html`` version of the
resource: ::

   giza sphinx --builder html
   giza sphinx -b html

Replace ``html`` with any Sphinx builder you wish to use. You can
specify a list, space separated, of builders to build multiple formats
at once. For example: ::

   giza sphinx --builder latex dirhtml json html singlehtml epub man

For the MongoDB Manual this is equivalent to the ``make publish``
operation. For projects that have multiple editions, you can specify
the edition as a section option, for example: ::

   giza sphinx --builder latex json html dirhtml singlehtml --edition saas hosted

This is the Giza command to build the full MMS documentation, and it
builds ``saas`` and ``hosted`` versions of the manual for 5 sphinx
output formats.

Diagnostics
```````````

You can use the ``giza config`` command to see a rendered version of
the configuration object used during builds. ``config`` allows you to
see how specifying a language or edition will affect the config
object. For example: ::

   giza config
   giza config --edition saas
   giza config --edition hosted
   giza config --edition saas --language es
   giza config --edition hosted --language fr
   giza config -e saas -l es
   giza config -e hosted -l fr

Deploying
`````````

There are two targets that deploy built documentation to the
production environment: ``deploy``, which only uploads the
resources; and ``push``, which builds and then deploys the
resources.

Each branch and repository defines its behavior of the deployment in a
*push* config file. These define a number of "push targets" that
describe how to upload the artifacts. When you run a deploy operation, you
specify one or more of these push targets and Giza will deploy the
artifacts specified in the configuration.

``push`` takes arguments that are the combination of the ``sphinx``
command and the ``deploy`` command. Consider the following commands:

   giza deploy --target push
   giza deploy --target stage
   giza deploy --target push-saas
   giza deploy --target stage-saas
   giza push --deploy push-saas push-hosted --builder latex json html dirhtml singlehtml --edition saas hosted --language es
   giza push --deploy push-saas push-hosted --builder latex json html dirhtml singlehtml --edition saas hosted

Add the ``--dry-run`` or ``-d`` option to any ``deploy`` command to
avoid actually uploading artifacts during testing.

Git
```

Giza provides wrappers for several common ``git`` operations. You can
use Giza to apply the patch from a github pull request or from a
single Github commit: ::

   giza git am -p <object>
   giza git am --patch <object>

Replace ``<object>`` with the ID of a pull request against the
repository that  repository. You can apply any object from github, by
passing a full github URI as the ``<object>``.

All ``giza git`` commands support a ``--branch`` argument that allows
them to perform their operation on a different branch. For example: ::

   giza git am --patch 1066 --branch v4.2
   giza git am -p 1066 -b v4.2

You can also cherry-pick commits from the local repository onto the
current branch: ::

   giza git cp --commits a5b8087
   giza git cp -c a5b8087

The ``git cp`` command allows you to cherry pick a list of commits,
but is most useful in combination with the ``--branch`` option to
apply commits to other branches, as in the following examples: ::

   giza git cp --commits a5b8087 8f9150a 2eb441b
   giza git cp -c a5b8087 8f9150a  2eb441b

   giza git cp --commits a5b8087 8f9150a 2eb441b --branch v0.2
   giza git cp -c a5b8087 8f9150a  2eb441b --branch v0.2

Additional Giza Operations
``````````````````````````

``generate``
''''''''''''

These operations generate content or fetch data used by the build
without generating the full artifacts. Useful for debugging and
testing. In normal operations the ``sphinx`` operations generate
require inputs, and these operations are not needed.

``generate`` provides the following operations to generate content.

- ``api``
- ``assets``
- ``images``
- ``intersphinx``
- ``options``
- ``primer``
- ``steps``
- ``tables``
- ``toc``

``includes``
''''''''''''

The ``includes`` operations introspect the resources' content reuse,
and allow writers to be able to see the dependency relationship
between source files. ``giza includes`` has the following additional
operations:

- ``recursive``: returns a list of all files that also include other
  files.

- ``changes``: returns a list of all files in the repository affected
  indirectly by uncommitted changes to the current repository. (Requires
  `PyGit2 <https://github.com/libgit2/pygit2>`_)

- ``once``: returns a list of all included files that are only used
  once.

- ``unused``: returns a list of all included files that are not used
  at all.

- ``graph``: return a document that maps include files to the
  dependent source files. Includes the ``--filter`` option, which
  allows you to specify a prefix of included files to limit the size
  or scope of the graph.

``package``
'''''''''''

Giza provides support for creating "packages" of build artifacts that
you can use to deploy a version of the resource produced on a
different system or at a different time. This makes it possible to
safely deploy a sequence of builds in quick succession. The
``package`` command provides the following options:

- ``create``: Given a *push target*, build ha package of the current
  build output and the current configuration object.

- ``fetch``: Given a URL, download the package to the
  local "build archive." Will refuse to download a package that
  already exists in the build archive.

- ``unwind``: Given a path or URL of a package, extract the package to
  the "public output" directory used for staging.

- ``deploy``: Given a *push target* and the path or URL of a package,
  extract the package and upload those artifacts.

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
