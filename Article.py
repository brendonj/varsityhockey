import hashlib
import User
from Thumbnail import Thumbnail
from google.appengine.ext import ndb

class Article(ndb.Model):
    #author = ndb.KeyProperty(kind=User.User)
    author = ndb.StringProperty(required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.TextProperty(required=True)
    teaser = ndb.TextProperty(required=True)
    body = ndb.TextProperty()
    thumb = ndb.TextProperty()
    visible = ndb.BooleanProperty(default=True)

    def add_thumbnail(self, image):
        sha256 = hashlib.sha256()
        sha256.update(image)
        filename = "article/thumbs/%s" % sha256.hexdigest()
        self.thumb = Thumbnail.add_image(filename, image, 90)

    @staticmethod
    def get_thumbnails():
        return Thumbnail.get_images("article/thumbs/", 90)

# vim: set ts=4 sw=4 hlsearch expandtab :
