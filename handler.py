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

JINJA_ENV = jinja2.Environment(loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))

# ------------------ MODELS ------------------ 

class TargetModel(db.Model):
    '''
    The datastore model to contain info about shortened URL's (targets).
    '''
    target = db.StringProperty(required=True)
    shorthand = db.StringProperty(required=True, indexed=True)
    timestamp = db.DateTimeProperty(auto_now=True)
    user = db.UserProperty(auto_current_user=True, auto_current_user_add=True)


# ------------------ REQUEST HANDLERS --------------------

class LookupAndRedirect(webapp.RequestHandler):
    def get(self, *args):
        '''
        Redirect to shortened url with the given shorthand

        @param shorthand: the TargetModel shorthand entry for the url
        @type shorthand: str
        '''
        user = users.get_current_user()
        if user:
            try:
                shorthand = args[0] if len(args) > 0 else None
                entity = lookup_url(shorthand)

                if entity:
                    self.redirect(entity.target)
            except ValueError as valerr:
                LOGGER.error("Got invalid/unparsable target shorthand (%s): %s", 
                             shorthand, valerr)
                self.error(500)  # redirect to "Internal Server Error" page
                return  # shouldn't be needed, but doesn't hurt
        else:
            # redirect to unauthorized user page
            self.redirect(users.create_login_url(self.request.uri))

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
        user = users.get_current_user()
        if user:
            logouturl = users.create_logout_url(self.request.uri)
            baseurl = self.request.host_url + "/"
            newurl = baseurl + args[0].shorthand if len(args) > 0 else None

            template = JINJA_ENV.get_template('generateurl.html')
            values = {
                     'newurl': newurl, 
                     'logouturl': logouturl,
                     'user' : user.nickname(),
                     }
            self.response.out.write(template.render(values))
        else:
            # redirect to unauthorized user page
            self.redirect(users.create_login_url(self.request.uri))

    def post(self):
        '''
        target_url - the target url to encode
        target_alias - the shorthand to associate with target_url 
        '''
        url = self.request.get('target_url')
        alias = self.request.get('target_alias')
        if url:
            target = store_target(url, alias)
            self.get(target)
        else:
            self.error(500)


# ------------------ FUNCTIONS ------------------ 

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
    return targetmodel


def lookup_url(shorthand, user=None):
    '''
    Lookup the given url associated with the given shorthand for the specified 
    user.
    
    @param shorthand: the url shorthand (ie hashed name) 
    @type shorthand: str

    @param user: the user to limit results to, if None, then the currently
    logged in user is used.
    @type user: users.User 
    
    @return: the TargetModel instance that has the given shorthand, with the
    most recent timestamp value, and that was added by user.
    @rtype: TargetModel
    
    @raise ValueError: if shorthand is not a valid shorthand value (ie 
    there is no target with that value, or it was created by a different user)
    '''
    if not user:
        user = users.get_current_user()
    query = TargetModel.all()

    query.filter("shorthand = ", shorthand)  # lookup by shorthand
    query.filter("user = ", user) # limit to specified user
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
