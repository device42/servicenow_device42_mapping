[Device42](http://www.device42.com/) is a comprehensive data center inventory management and IP Address management software
that integrates centralized password management, impact charts and applications mappings with IT asset management.

This repository contains sample script that link ServiceNow and Device42 back and forth.

## Assumptions
-----------------------------
    * This script works with Device42 10.5.0.1473709546 and above


### Requirements
-----------------------------
    * python 2.7.x
    * requests (you can install it with pip install requests or apt-get install python-requests)


### Usage
-----------------------------
	* For proper run script you need to add mapping.xml, then put fields as in sample.
	* (!IMPORTANT) For each ServiceNow table that in mapping.xml you should add 'u_device42_id' custom field.

Run the script and enjoy! (`python sync.py`)
If you have any questions - feel free to reach out to us at support at device42.com


### Compatibility
-----------------------------
    * Script runs on Linux and Windows


### Gotchas
-----------------------------
    * mapping.xml - file from where we get fields relations between D42 and ServiceNow
    * lib.py - file with integration description, we describe how fields should be migrated
    * sync.py - initialization and processing file, where we prepare API calls


### To Do
-----------------------------

    * add customers integration
