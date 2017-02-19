import logging
from Thumbnail import Thumbnail

from google.appengine.ext import ndb

class Sponsor(ndb.Model):
    name = ndb.TextProperty(required=True)
    url = ndb.TextProperty()
    thumb = ndb.TextProperty(required=True)
    sort = ndb.IntegerProperty(default=100)

    def add_thumbnail(self, image):
        filename = "sponsors/%s" % self.name.replace(" ", "")
        self.thumb = Thumbnail.add_image(filename, image, 45, clobber=True)

    def remove_thumbnail(self):
        filename = "sponsors/%s" % self.name.replace(" ", "")
        Thumbnail.remove_image(filename)

# vim: set ts=4 sw=4 hlsearch expandtab :
