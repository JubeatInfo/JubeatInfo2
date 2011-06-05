
from flask import Flask
app = Flask(__name__)

from jubeatinfo.lib.Gzipper import Gzipper
app.wsgi_app = Gzipper(app.wsgi_app)

import jubeatinfo.views
from jubeatinfo.views.knit import knit

import jubeatinfo.database

app.register_module(knit, url_prefix='/knit')

