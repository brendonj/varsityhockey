from google.appengine.ext import ndb
from google.appengine.api import images

class Thumbnail(ndb.Model):
    date = ndb.DateTimeProperty(auto_now=True)
    image = ndb.BlobProperty()
    exclusive = ndb.BooleanProperty(default=False)

    @staticmethod
    def preprocess(pre):
        if pre is None:
            return None
        return images.resize(pre, 90, 90)
