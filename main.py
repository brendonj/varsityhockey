#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Using pytz locally has required a minor hack to sandbox.py as google have
# yet to update dev_appserver.py to work with pytz
# https://code.google.com/p/googleappengine/issues/detail?id=498&colspec=ID%20Type%20Component%20Status%20Stars%20Summary%20Language%20Priority%20Owner%20Log
# D:\apps\Google\Cloud SDK\google-cloud-sdk\platform\google_appengine\google\appengine\tools\devappserver2\python

# Cloud storage docs:
# https://cloud.google.com/appengine/docs/python/refdocs/google.appengine.api.images#google.appengine.api.images.delete_serving_url
# https://cloud.google.com/appengine/docs/python/googlecloudstorageclient/app-engine-cloud-storage-sample
# https://cloud.google.com/appengine/docs/python/googlecloudstorageclient/setting-up-cloud-storage
# https://cloud.google.com/appengine/docs/python/googlecloudstorageclient/read-write-to-cloud-storage


import os
import webapp2
import jinja2
import time
import datetime
import pytz

from User import User
from Article import Article
from Thumbnail import Thumbnail
from Committee import Committee 
from Sponsor import Sponsor

#from google.cloud import storage
from google.appengine.ext import ndb
from google.appengine.api import users

jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class ThumbHandler(webapp2.RequestHandler):
    def get(self, thumb_id=None):
        thumb = ndb.Key(urlsafe=thumb_id).get()
        if thumb:
            self.response.headers["Content-Type"] = "image/png"
            self.response.out.write(thumb.image)
        else:
            self.response.out.write("missing image")


class EditArticleHandler(webapp2.RequestHandler):
    def get(self, article_id=None):
        template = jinja_environment.get_template("templates/edit_article.html")
        if article_id:
            article = ndb.Key(urlsafe=article_id).get()
        else:
            article = None
        user = users.get_current_user()

        self.response.out.write(template.render({
            "article": article,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "thumbs": Article.get_thumbnails(),
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))

    def post(self, article_id=None):
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        # fetch the existing article if this is an update, otherwise create one
        if article_id:
            article = ndb.Key(urlsafe=article_id).get()
        else:
            article = Article()

        article.author = user.nickname()
        article.title = self.request.get("title")
        article.teaser = self.request.get("teaser")
        article.body = self.request.get("body")
        article.visible = True
        # upload the new thumbnail if there is one
        if len(self.request.get("thumb-upload")) > 0:
            article.add_thumbnail(self.request.get("thumb-upload"))
        else:
            # add url to an existing thumbnail
            article.thumb = self.request.get("thumb-select")

        if self.request.get("preview"):
            # redisplay the edit page with the (temporary) changes
            if not article.date:
                article.date = datetime.datetime.now()
            template = jinja_environment.get_template("templates/edit_article.html")
            self.response.out.write(template.render({
                "article": article,
                "admin": True,
                "logout_url": users.create_logout_url("/"),
                "request": self.request,
                "thumbs": Article.get_thumbnails(),
                "sponsors": Sponsor.query().order(Sponsor.sort),
            }))
        else:
            # commit the changes that have just been made
            article_id = article.put()
            self.redirect("/article/%s" % article_id.urlsafe())

    def delete(self, article_id):
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        # for now just hide the article, don't actually delete it. We can
        # still edit it if we know the article id but noone else can view it
        article = ndb.Key(urlsafe=article_id).get()
        article.visible = False
        article.put()
        #self.redirect("/")


class ArticleHandler(webapp2.RequestHandler):
    def get(self, article_id=None):
        template = jinja_environment.get_template("templates/article.html")
        article = ndb.Key(urlsafe=article_id).get()
        if article.visible is False:
            self.redirect("/")

        article.date = article.date.replace(tzinfo=pytz.utc).astimezone(
                pytz.timezone("Pacific/Auckland"))

        user = users.get_current_user()
        self.response.out.write(template.render({
            "article": article,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class MainHandler(webapp2.RequestHandler):
    def get(self, page_number=1):
        page_number = int(page_number)
        template = jinja_environment.get_template("templates/news.html")
        #articles = Article.query().order(-Article.date).fetch(
        #        offset=int(page_number)*4, limit=4)
        # use a cursor query so we can get the "more" flag
        # TODO could we do an infinite scroll thing and store the cursor
        # in a cookie that gets deleted as soon as the user leaves the site?
        articles, _, more = Article.query().filter(ndb.BooleanProperty("visible") == True).order(-Article.date).fetch_page(
                10, start_cursor=None, offset=(page_number - 1) * 10,
                keys_only=True)
        articles = ndb.get_multi(articles)
        user = users.get_current_user()

        for article in articles:
            article.date = article.date.replace(tzinfo=pytz.utc).astimezone(
                    pytz.timezone("Pacific/Auckland"))

        self.response.out.write(template.render({
            "articles": articles,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "newer": (page_number - 1) if page_number > 1 else None,
            "older": (page_number + 1) if more else None,
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class CommitteeHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("templates/committee.html")
        user = users.get_current_user()
        self.response.out.write(template.render({
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "committee": Committee.query().order(Committee.sort),
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class EditCommitteeHandler(webapp2.RequestHandler):
    def get(self):
        """ Display the edit form for committee members """
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            self.redirect("/committee")

        template = jinja_environment.get_template(
                "templates/edit_committee.html")

        self.response.out.write(template.render({
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "committee": Committee.query().order(Committee.sort),
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))

    def post(self, member_id=None):
        """ Create or update a committee member """
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        # fetch the existing member if this is an update, otherwise create one
        if member_id:
            member = ndb.Key(urlsafe=member_id).get()
            # Delete existing thumbnail for this member if there is a new one
            if len(self.request.get("thumb-upload")) > 0:
                member.remove_thumbnail()
        else:
            member = Committee()

        # set/update the committee member and put them into the datastore
        member.name = self.request.get("name")
        member.title = self.request.get("title")
        member.email = self.request.get("email")
        member.blurb = self.request.get("blurb")
        member.sort = int(self.request.get("sort"))
        # upload the new thumbnail if there is one
        if len(self.request.get("thumb-upload")) > 0:
            member.add_thumbnail(self.request.get("thumb-upload"))
        member_id = member.put()

        self.redirect("/committee/edit")


class ContactHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("templates/contact.html")
        user = users.get_current_user()
        self.response.out.write(template.render({
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "mens": Committee.query().filter(ndb.StringProperty("title") == "Mens Club Captain").get(),
            "womens": Committee.query().filter(ndb.StringProperty("title") == "Womens Club Captain").get(),
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class AboutHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("templates/about.html")
        user = users.get_current_user()
        self.response.out.write(template.render({
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class HonoursHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("templates/honours.html")
        user = users.get_current_user()
        self.response.out.write(template.render({
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "life_members": [],
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))


class EditSponsorsHandler(webapp2.RequestHandler):
    def get(self):
        """ Display the edit form for sponsors """
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            self.redirect("/")

        template = jinja_environment.get_template(
                "templates/edit_sponsors.html")

        self.response.out.write(template.render({
            "admin": True,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "sponsors": Sponsor.query().order(Sponsor.sort),
        }))

    def post(self, sponsor_id=None):
        """ Create or update a sponsor """
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        # fetch the existing sponsor if this is an update, otherwise create one
        if sponsor_id:
            sponsor = ndb.Key(urlsafe=sponsor_id).get()
            # Delete existing thumbnail for this sponsor if there is a new one
            if len(self.request.get("thumb-upload")) > 0:
                sponsor.remove_thumbnail()
        else:
            sponsor = Sponsor()

        # set/update the sponsor and put them into the datastore
        sponsor.name = self.request.get("name")
        sponsor.url = self.request.get("link")
        sponsor.sort = int(self.request.get("sort"))
        # upload the new thumbnail if there is one
        if len(self.request.get("thumb-upload")) > 0:
            sponsor.add_thumbnail(self.request.get("thumb-upload"))
        sponsor_id = sponsor.put()

        self.redirect("/sponsors/edit")

    def delete(self, sponsor_id):
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        sponsor = ndb.Key(urlsafe=sponsor_id).get()
        if sponsor is not None:
            sponsor.remove_thumbnail()
            sponsor.key.delete()


class AdminHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            text = "Welcome %s (admin=%s), (<a href='%s'>sign out</a>)" % (
                    user.email(), users.is_current_user_admin(),
                    users.create_logout_url("/"))
        else:
            text = "<a href='%s'>sign in</a>" % users.create_login_url()
        self.response.write(text)


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/edit', EditArticleHandler),
    webapp2.Route('/admin', AdminHandler),
    webapp2.Route('/committee', CommitteeHandler),
    webapp2.Route('/committee/edit', EditCommitteeHandler),
    webapp2.Route('/committee/<member_id>/edit', EditCommitteeHandler),
    webapp2.Route('/contact', ContactHandler),
    webapp2.Route('/about', AboutHandler),
    webapp2.Route('/honours', HonoursHandler),
    webapp2.Route('/article/edit', EditArticleHandler),
    webapp2.Route('/article/<article_id>', ArticleHandler),
    webapp2.Route('/article/<article_id>/edit', EditArticleHandler),
    webapp2.Route('/sponsors/edit', EditSponsorsHandler),
    webapp2.Route('/sponsors/<sponsor_id>/edit', EditSponsorsHandler),
    webapp2.Route('/<page_number:\d+>', MainHandler),
], debug=True)

# vim: set ts=4 sw=4 hlsearch expandtab :
