import logging
import cloudstorage as gcs
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import app_identity

class Thumbnail(ndb.Model):
    date = ndb.DateTimeProperty(auto_now=True)
    image = ndb.BlobProperty()
    exclusive = ndb.BooleanProperty(default=False)

    @staticmethod
    def preprocess(pre):
        if pre is None:
            return None
        return images.resize(pre, 90, 90)

    @staticmethod
    def add_image(filename, image, size):
        # Write the file to cloud storage
        bucket_name = app_identity.get_default_gcs_bucket_name()
        filename = "/%s/%s.png" % (bucket_name, filename)
        gcs_file = gcs.open(filename, "w", content_type="image/png")
        gcs_file.write(image)
        gcs_file.close()

        # Get a URL for it from the cloud storage
        blobstore_filename = "/gs%s" % filename
        blob_key = blobstore.create_gs_key(blobstore_filename)
        return images.get_serving_url(blob_key, size=size, secure_url=True)

    @staticmethod
    def remove_image(filename):
        bucket_name = app_identity.get_default_gcs_bucket_name()
        filename = "/%s/%s.png" % (bucket_name, filename)
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
