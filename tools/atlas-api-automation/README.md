
Atlas API Automation Scripts
=================
The `differ.py` script outputs the differences between the endpoints currently in the Atlas source code vs. what currently exists in cloud-docs.


How to use
---------------

This script takes in as a parameter the path to your local cloud-docs directory and it also requires that `mms.api.json` exists which is a JSON file of current Atlas endpoints. Ask for this file :)

### Example
```
python3 differ.py /Users/Daniel/Documents/Sites/cloud-docs
```