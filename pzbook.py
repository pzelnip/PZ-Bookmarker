'''
The "main" script for the PZ Bookmarker project

@author: pzelnip 
'''
# --------------------------------- IMPORTS -------------------------------- 
# Stdlib imports
import logging
import os

# 3rd party imports
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import jinja2

# ------------------------ MODULE LEVEL DECLARATIONS ------------------------ 

# init logger
LOGGER = logging.getLogger(__name__)                        

# Set up template loading
JINJA_ENV = jinja2.Environment(loader = 
                        jinja2.FileSystemLoader(os.path.dirname(__file__)))

# ------------------------------- DATA MODELS -------------------------------

class BookmarkAlias(db.Model):
    # pylint: disable-msg=R0904
    # "too many public methods", but db.Model defines a ton of them
    '''
    Datastore model for defining an individual bookmark.
    '''
    url = db.StringProperty(required = True)
    dateadded = db.DateTimeProperty(auto_now = True)

# ----------------------------- REQUEST HANDLERS ---------------------------- 

class DefaultBMInterface(webapp.RequestHandler):
    '''
    The default bookmark interface, on a GET produces the "define a new 
    bookmark" and "lookup a bookmark" page.  On a POST, either stores a new
    bookmark or does a redirect to an existing one.
    '''
    def get(self, *args):
        # @TODO: implement
        pass

    def post(self, *args):
        # @TODO: implement
        pass

class RestInterface(webapp.RequestHandler):
    '''
    RESTful interface to the datastore
    '''
    def get(self, *args):
        # @TODO: implement
        pass

# ------------------------ URL MAPPINGS ------------------------ 

WEBAPP = webapp.WSGIApplication([
        ('/', DefaultBMInterface),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(WEBAPP)
