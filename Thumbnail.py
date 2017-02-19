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
    def add_image(filename, image, size, clobber=False):
        # Write the file to cloud storage
        bucket_name = app_identity.get_default_gcs_bucket_name()
        filename = "/%s/%s.png" % (bucket_name, filename)

        try:
            stat = gcs.stat(filename)
        except gcs.errors.NotFoundError as e:
            stat = None

        if stat is None or clobber is True:
            gcs_file = gcs.open(filename, "w", content_type="image/png")
            gcs_file.write(image)
            gcs_file.close()
            blobstore_filename = "/gs%s" % filename
        else:
            blobstore_filename = "/gs%s" % stat.filename

        # Get a URL for it from the cloud storage
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
