# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The :mod:`giza.config` stores the models and helpers for all configuration
data. The classes that describe these objects validate input from configuration
files, compute dynamic values, and provide a stable interface for the
configuration data. Important aspects of this code:

:class:`ConfigurationBase` (:mod:`giza.libgiza.config`)
   The base class from which all configuration classes descend. Implements
   :meth:`~ConfigurationBase.ingest()`, which runs after initialization to load
   configuration data from a ``yaml`` file or from a dictionary structure, as
   well as a :meth:`~ConfigurationBase.dict()` method that renders the
   configuration object as a dictionary with some redaction for protected and
   internal fields. Additionally provides customized attribute setting and
   retrieving for these objects.

:class:`RecursiveConfigurationBase` (:mod:`giza.libgiza.base`)
   A base configuration object that contains a reference to the global config
   object in the :attr:`RecursiveConfigurationBase` attribute to facilitate
   resolving values in reference to other values.

:class:`RuntimeStateConfig` (:mod:`giza.config.runtime`)
   By convention, this class defines the ``conf.runstate`` portion of the config
   object, which is populated by the command line argument parsing system. Add
   methods to get and set values, or, add values to the
   :attr:`RuntimeStateConfig._option_registry` to use default setting and
   getting.

:function:`~giza.config.helper.fetch_config()` (:mod:`giza.config.helper`)
   Pass a :class:`RuntimeStateConfig` object to this function, which returns a
   fully constituted configuration object.

:mod:`giza.config.jeerah`
   This module contains all of the configuration classes for the Jira and Github
   (i.e. :mod:`giza.scrumpy` and :mod:`giza.github`) integration.
"""
