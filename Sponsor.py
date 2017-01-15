from google.appengine.ext import ndb

class Sponsor(ndb.Model):
	name = ndb.TextProperty(required=True)
	url = ndb.TextProperty()
	thumb = ndb.BlobProperty(required=True)

# vim: set ts=4 sw=4 hlsearch expandtab :
