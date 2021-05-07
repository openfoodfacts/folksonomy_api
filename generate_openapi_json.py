#! /usr/env python3

import json
import sys
from folksonomy.api import app

json.dump(app.openapi(),sys.stdout)
