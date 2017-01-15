from google.appengine.ext import ndb

class User(ndb.Model):
	name = ndb.StringProperty()
	email = ndb.StringProperty()
	level = ndb.IntegerProperty()

# vim: set ts=4 sw=4 hlsearch expandtab :
