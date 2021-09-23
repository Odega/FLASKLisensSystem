#!/usr/bin/python
#Activate VENV
activate_this = '/cyberbook/data/site/hjem.kunnskap.no/portal/yteach/web/api/lisens/virtualenv/bin/activate_this.py'
print("ACTIVATING VENV")
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

print("VENV ACTIVATED")

import sys
sys.path.insert(0, "/cyberbook/data/site/hjem.kunnskap.no/portal/yteach/web/api/lisens")
from app import app as application