import Thumbnail
from google.appengine.ext import ndb

class Committee(ndb.Model):
    title = ndb.StringProperty(required=True)
    name = ndb.TextProperty(required=True)
    email = ndb.TextProperty()
    blurb = ndb.TextProperty()
    thumb = ndb.KeyProperty()
    sort = ndb.IntegerProperty(default=100)

# vim: set ts=4 sw=4 hlsearch expandtab :
