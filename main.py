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
import os
import webapp2
import jinja2
import time
import datetime

from User import User
from Article import Article
from Thumbnail import Thumbnail
from Committee import Committee 
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
        thumbs = Thumbnail.query().filter(ndb.BooleanProperty("exclusive") == False).order(-Thumbnail.date).fetch(keys_only=True)

        self.response.out.write(template.render({
            "article": article,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "thumbs": thumbs,
        }))

    def post(self, article_id=None):
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        if len(self.request.get("thumb-upload")) == 0:
            thumb = ndb.Key(urlsafe=self.request.get("thumb-select"))
        else:
            thumbnail = Thumbnail()
            thumbnail.image = Thumbnail.preprocess(
                    self.request.get("thumb-upload"))
            thumbnail.exclusive = False
            thumb = thumbnail.put()

        if article_id:
            article = ndb.Key(urlsafe=article_id).get()
        else:
            article = Article()

        article.author = user.nickname()
        article.title = self.request.get("title")
        article.teaser = self.request.get("teaser")
        article.body = self.request.get("body")
        article.thumb = thumb
        article.visible = True
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

        user = users.get_current_user()
        self.response.out.write(template.render({
            "article": article,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
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
                3, start_cursor=None, offset=(page_number - 1) * 3)
        user = users.get_current_user()
        self.response.out.write(template.render({
            "articles": articles,
            "admin": True if user and users.is_current_user_admin() else False,
            "logout_url": users.create_logout_url("/"),
            "request": self.request,
            "newer": (page_number - 1) if page_number > 1 else None,
            "older": (page_number + 1) if more else None,
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
        }))

    def post(self, member_id=None):
        """ Create or update a committee member """
        user = users.get_current_user()
        if user is None or users.is_current_user_admin() is False:
            return

        # fetch the existing member if this is an update, otherwise create one
        if member_id:
            member = ndb.Key(urlsafe=member_id).get()
        else:
            member = Committee()

        # deal with creating/replacing committee member thumbnails
        if len(self.request.get("thumb-upload")) > 0:
            if member_id:
                # delete the old thumbnail
                member.thumb.delete()
            # add the new thumbnail
            thumbnail = Thumbnail()
            thumbnail.image = Thumbnail.preprocess(
                    self.request.get("thumb-upload"))
            thumbnail.exclusive = True
            thumb = thumbnail.put()
        else:
            if member_id:
                # reuse the existing thumbnail
                thumb = member.thumb
            else:
                thumb = None

        # set/update the committee member and put them into the datastore
        member.name = self.request.get("name")
        member.title = self.request.get("title")
        member.email = self.request.get("email")
        member.blurb = self.request.get("blurb")
        member.sort = int(self.request.get("sort"))
        member.thumb = thumb
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
            "mens": Committee.query().get(), # XXX
            "womens": Committee.query().get() # XXX
        }))


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
    webapp2.Route('/thumbs/<thumb_id>', ThumbHandler),
    webapp2.Route('/article/edit', EditArticleHandler),
    webapp2.Route('/article/<article_id>', ArticleHandler),
    webapp2.Route('/article/<article_id>/edit', EditArticleHandler),
    webapp2.Route('/<page_number:\d+>', MainHandler),
], debug=True)

# vim: set ts=4 sw=4 hlsearch expandtab :
