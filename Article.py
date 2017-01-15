import User
import Thumbnail
from google.appengine.ext import ndb


class Article(ndb.Model):
    #author = ndb.KeyProperty(kind=User.User)
    author = ndb.StringProperty(required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.TextProperty(required=True)
    teaser = ndb.TextProperty(required=True)
    body = ndb.TextProperty()
    thumb = ndb.KeyProperty()
    visible = ndb.BooleanProperty(default=True)
    #thumb = ndb.BlobProperty()
    #thumb = ndb.TextProperty()

# vim: set ts=4 sw=4 hlsearch expandtab :
