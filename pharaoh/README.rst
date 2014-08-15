====================
Translation Pipeline
====================

Commands
--------

* **Verifier**

  * ``pharaoh verifier``
  * This command starts a verifier server with the configuration found in the config file.
  * It uses gunicorn for running the application.
  * Use the verifier to have contributors edit and verify machine translations or translations that other contributors produced
  * You first put the translations into the backend MongoDB database. The app then looks through the database and allows users to choose a file to edit
  * Every sentence they can either approve or edit.
  * Two users can't edit the same file at the same time so that they don't accidentally clash.
  * Use the admin page to upload or download docs to the database isntead of using the following two commands 

* **po-to-mongo**

  * ``pharaoh po-to-mongo --po ~/docs --username Judah --status approved --source_language en --target_language es --host localhost --port 28000 --dbname verifier``
  * This command takes po files and puts them into Mongodb
  * You can do the same functionality by navigating to the admin page of the verifier and uploading po files
  * A new set of po files should be uploaded for every different translator as the editor will be tagged with whatever username is provided.
  * If the translations are trusted the status can be uploaded as approved and then they won't be edited again.

* **mongo-to-po**

  * ``pharaoh mongo-to-po --po ~/docs --source_language en--target_language es --host localhost --port 28000 --dbname verifier --all``
  * This command takes the translations in the mongodb database and puts them into po files
  * It injects the translations into the po files that are provided
  * It only overwrites the untranslated entries in those files
  * It is good practice to copy the po files first to have a backup

Setup
-----

* Use  ``pip install -e .`` to install all dependencies.
* You will also need to install `MongoDB <http://www.mongodb.org/downloads>`
* Start a Mongod instance on any host and port and fix the host and port in the included config to match.
* Make sure you put any users in the database before having them make edits or uploading po files for them.
* This system is made to work well with `Giza <https://pypi.python.org/pypi/giza/0.2.2>`

Workflow
--------

1. Translate your docs

  1. Use Giza, which can be found in Pypi, to translate your po files.
  2. First copy the files so you have a parallel directory tree, one for every distinct translator (consider machine translation to be one translator, unless you have multiple systems). 

2. Put your docs in MongoDB

  1. Use ``po-to-mongo`` to move the data into MongoDB.
  2. Run this once for every "type" of translation you have. (i.e. Moses, Person1, Person2....), this will make the status and the username correct in each case.
  3. You may need to put some users into your database first. Open up a shell and run the following for any users: ``db.users.insert({"username": "Moses", "num_reviewed": 0, "num_user_approved": 0, "num_got_approved":0, "trust_level": "basic"})``
  4. Alternatively use the admin page to do the same thing. Upload the docs you want. You will need to put them in a ``.tar.gz`` file before uplaoding them. You can't just upload a directory of docs.

3. Run the verifier

  1. Run the verifier web app and have people contribute to it.
  2. Make sure to add new users to the database before they begin translating.

4. Take the approved data (or all) from the verifier

  1. Copy doc directory tree to back it up.
  2. Use ``mongo_to_po`` to copy approved translations into the new doc directory tree.
  3. This will inject the approved translations into all of the untranslated sentences.
  4. Alternatively use the admin page to do the same thing. It will download a new copy of the translations rather than overwriting an old copy as the pharaoh command does.

Work to be Done
---------------

1. Authentication- This is key to it every being production ready. As part of adding authentication make adding users a more seemless process. Currently they have to be manually added into the database to be able to be used. Making it so that users can be created would be good. Also more improtantly adding better handling for users not in the system is a must. This could use JIRA or ideally would be more general so you can plug in different authentication systems.
2. Upload Docs Fixes- If the documentation ever gets edited (as it always will) currently the system can't handle it well. Having the upload and download scripts handle these better would be great. Uploading shouldn't overwrite sentences that haven't changed and it should remove sentences that don't exist anymore and add in ones that do now in the proper order (requires fixing sentence numbers for everything). 
3. Translations from Scratch- Currently you need a set of docs on top of which you can do translations. It would be good to make it so that you can just start from a blank slate for a new language or for a language already in there. If the language already exists we shouldn't get multiple blank slate sets popping up, rather just one set of blank slate docs and one set of machine translation verifications. 
4. Docs Pages Priorities- The infrustructure exists for prioritizing pages for translations, however there is no method for actually putting in these priorities well. Having a method in the upload script for adding in priorities could fix this. Google Analytics page views could be a good metric.
5. Edit Approved Translations- If someone makes a mistake but it accidentally gets approved there should be a way for trusted or admin users to unapprove them and allow others or themselves to edit them.
6. Gamification- Make it more like a game with awards, badges, and points for translating more things. Getting a higher reputation score should get you some improvements similar to how Stack Overflow works.
