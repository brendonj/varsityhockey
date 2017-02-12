import logging
import cloudstorage as gcs
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.api import app_identity
from google.appengine.api import images

class Sponsor(ndb.Model):
    name = ndb.TextProperty(required=True)
    url = ndb.TextProperty()
    thumb = ndb.TextProperty(required=True)
    sort = ndb.IntegerProperty(default=100)

    def add_thumbnail(self, image):
        bucket_name = app_identity.get_default_gcs_bucket_name()
        filename = "/%s/sponsors/%s.png" % (bucket_name,
                self.name.replace(" ", ""))
        gcs_file = gcs.open(filename, "w", content_type="image/png")
        gcs_file.write(image)
        gcs_file.close()

        # Get a URL for it from the cloud storage
        blobstore_filename = "/gs%s" % filename
        blob_key = blobstore.create_gs_key(blobstore_filename)
        self.thumb = images.get_serving_url(blob_key, size=45, secure_url=True)

    def remove_thumbnail(self):
        bucket_name = app_identity.get_default_gcs_bucket_name()
        filename = "/%s/sponsors/%s.png" % (bucket_name,
                self.name.replace(" ", ""))
        blobstore_filename = "/gs%s" % filename
        blob_key = blobstore.create_gs_key(blobstore_filename)
        try:
            images.delete_serving_url(blob_key)
        except images.Error as e:
            logging.error(filename)
            logging.error(e)
        try:
            gcs.delete(filename)
        except gcs.errors.NotFoundError as e:
            logging.error(filename)
            logging.error(e)

# vim: set ts=4 sw=4 hlsearch expandtab :
