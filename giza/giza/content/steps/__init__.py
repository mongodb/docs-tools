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
Steps schema is: ::

   {
     "title": <str>,
     "stepnum": <int>,
     "pre": <str>,
     "post": <str>,
     "ref": <str>,
     "action": {
                  "heading": <str>,
                  "code": <str>,
                  "copyable": <boolean>,
                  "language": <str>,
                  "content": <str>,
                  "pre": <str>,
                  "post": <str>
                }
   }

Notes:

- stepnum is optional. If not specified, we assume that the sequence starts at
  one. If you specify your own ``stepnum`` in one step you have to specify your
  own step number in all steps in this sequence. The script enforces order, so
  that if you specify stepnum, you don't need to specify steps in the source file in order.

- "title" and "heading" fields can optionally hold a document that contains
  both a "text" field *and* a "character" field if you need to adjust the level
  of the heading. For example: ::

    {
      "title":
        {
          "text": "name of step",
          "character": "-"
        }
    }

  Therefore "name of step" is, by MongoDB docs convention an "h2". By default,
  heading within actions are h4s and titles of steps are h3s.

- pre/post are optional. and allow you to add prefix or postfix text to a step
  or code example/action.

- Action should be either a doc or a list of docs. Their fields are optional,
  with the following notable points:

  - "language" refers to the syntax highlighting of "code," and is unused
    otherwise.

  - "content" is a paragraph, for steps that don't have code examples.

- the spec/agg format would be at least: ::

    {
       "source":
         {
           "file": <str>
           "ref":
         }
    }

  callers may specify ``description`` and ``title`` to override the source
  location. (ref needs to be modified in calling location.)

There are several situations where we raise errors because a step document is
invalid:

1. A step has both a "source" (i.e. is an included step), and an "action" field.

2. A code block contains both "content" and "code" fields.

"""
