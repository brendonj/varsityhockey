from Thumbnail import Thumbnail
from google.appengine.ext import ndb

class Committee(ndb.Model):
    title = ndb.StringProperty(required=True)
    name = ndb.TextProperty(required=True)
    email = ndb.TextProperty()
    blurb = ndb.TextProperty()
    thumb = ndb.TextProperty()
    sort = ndb.IntegerProperty(default=100)

    def add_thumbnail(self, image):
        filename = "committee/%s" % self.name.replace(" ", "")
        self.thumb = Thumbnail.add_image(filename, image, clobber=True)

    def remove_thumbnail(self):
        filename = "committee/%s" % self.name.replace(" ", "")
        Thumbnail.remove_image(filename)

# vim: set ts=4 sw=4 hlsearch expandtab :
