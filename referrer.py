from urllib import unquote
from urlparse import urlparse
import logging
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import jinja2

LOGGER = logging.getLogger(__name__)

JINJA_ENV = jinja2.Environment(loader = \
                        jinja2.FileSystemLoader(os.path.dirname(__file__)))

# ------------------ MODELS -----------------

class TargetModel(db.Model):
    target = db.StringProperty(required=True)
    shorthand = db.StringProperty(required=True, indexed=True)
    timestamp = db.DateTimeProperty(auto_now=True)


# ------------------ REQUEST HANDLERS --------------------

class LookupAndRedirect(webapp.RequestHandler):
    def get(self, *args):
        '''
        Redirect to shortened url with the given shorthand

        @param shorthand: the TargetModel shorthand entry for the url
        @type shorthand: str
        '''
        try:
            shorthand = args[0] if len(args) > 0 else None
            entity = get_most_recent_target(shorthand)

            if entity:
                self.redirect(entity.target)
        except ValueError as valerr:
            LOGGER.error("Got invalid/unparsable target shorthand (%s): %s", 
                         shorthand, valerr)
            self.error(500)  # redirect to "Internal Server Error" page
            return  # shouldn't be needed, but doesn't hurt

    def post(self):
        '''
        lookupurl - the target url to lookup 
        '''
        url = self.request.get('lookupurl')
        if url:
            self.get(url)
        else:
            self.error(500)


class GenerateURL(webapp.RequestHandler):
    def get(self, *args):
        baseurl = self.request.host_url + "/"
        newurl = baseurl + args[0].shorthand if len(args) > 0 else None

        template = JINJA_ENV.get_template('generateurl.html')
        values = {
                 'newurl': newurl, 
                 }
        self.response.out.write(template.render(values))

    def post(self):
        '''
        target_url - the target url to encode
        target_alias - the shorthand to associate with target_url 
        '''
        url = self.request.get('target_url')
        alias = self.request.get('target_alias')
        if url:
            target_id = store_target(url, alias)
            self.get(target_id)
        else:
            self.error(500)


# ------------- FUNCTIONS -------------

def store_target(target, alias):
    '''
    Stores the target url into the datastore, and returns the new TargetModel
    instance that was added

    @param target: the target url to store
    @type target: str

    @param alias: the shorthand to map to
    @type alias: str

    @return: the TargetModel instance that was inserted
    @type: TargetModel
    '''
    retval = None
    if target:
        # decode any percent encoding (ex: http:%3A//www.something.com)
        target = unquote(target)

        protocol = urlparse(target.lower()).scheme
        
        # if no protocol specified, assume http
        if not protocol:
            target = "http://" + target

        # store it        
        targetmodel = TargetModel(
            target = target,
            shorthand = alias,
        )
        targetmodel.put()
        retval = targetmodel

    return retval

def get_most_recent_target(shorthand):
    '''
    Gets the most recent (by date) target entry with the given shorthand
    value.  
    
    @param shorthand: limit results to only those entries with this 
    shorthand
    @type shorthand: str
    
    @return: the TargetModel instance that has the given shorthand, and the
    most recent timestamp value
    @rtype: TargetModel
    
    @raise ValueError: if shorthand is not a valid shorthand value (ie 
    there is no target with that value)
    '''
    query = TargetModel.all()

    query.filter("shorthand = ", shorthand)  # lookup by shorthand
    query.order("-timestamp")   # sort by time desc (newest 1st)
    result = query.get()

    if result:
        return result
    else:
        raise ValueError("Invalid shorthand '%s'" % shorthand)        



# Register the URL with the responsible classes
APPLICATION = webapp.WSGIApplication([
        (r'\A/lookup', LookupAndRedirect),
        (r'\A/(\w+)', LookupAndRedirect),
        (r'\A/', GenerateURL),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(APPLICATION)
