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
from webapp2_extras import jinja2
from google.appengine.ext import ndb
from time import sleep
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.runtime.apiproxy_errors import RequestTooLargeError



class User(ndb.Model):
    name = ndb.StringProperty(required = True)
    surname = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    mail = ndb.StringProperty(required=True)

    @staticmethod
    def select_all():
        return User.query()


class Image(ndb.Model):
    i_name = ndb.StringProperty(required=True)
    i_description = ndb.StringProperty(required=False)
    image_bin = ndb.BlobProperty(required=True)
    i_date = ndb.TimeProperty(auto_now_add=True)
    i_owner = ndb.StringProperty(required=True)
    i_owner2 = ndb.StringProperty(required=True)

    @staticmethod
    def select_all():
        return Image.query().order(-Image.i_date)#Todo mirar el orden de salida


class Comment(ndb.Model):
    content = ndb.StringProperty(required=True)
    c_image = ndb.StringProperty(required=True)
    c_owner = ndb.StringProperty(required=True)
    c_time = ndb.TimeProperty(auto_now_add=True)

    @staticmethod
    def select_all():
        return Comment.query().order(-Comment.c_time)


class HomeHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            connected = True
            nik = "Welcome " + user.nickname() + "!"
            sign = None
            logout = users.create_logout_url("/")
        else:
            connected = False
            nik = "Please sign in"
            sign = users.create_login_url("/")
            logout = None

        all_images = Image.select_all()
        to_show = {}
        # resize all images content
        for i in all_images:
            img = images.Image(i.image_bin)
            img.resize(width=140, height=140, allow_stretch=True)
            # img.im_feeling_lucky()
            to_show[i.key] = img.execute_transforms(output_encoding=images.PNG)
            # if images.Image(all_images[i]).height > 40 or images.Image(all_images[i]).width > 40:
            # im = images.resize(images.Image(i.image_bin), width=40, height=40)
        template_values = {"connected": connected, "user": nik, "sign": sign, "logout": logout, "img": to_show}
        jinja = jinja2.get_jinja2(app=self.app)
        sleep(1)
        self.response.write(jinja.render_template("home.html", **template_values))

    def post(self):
        # Store the added image
        image_file = self.request.get("fileImage", None)
        name = self.request.get("iName", "")
        if len(name) > 1 and image_file is not None:
            i = Image()
            i.i_name = name
            i.i_description = self.request.get("iDescription", "Any description added.")
            i.image_bin = image_file
            i.i_owner = users.get_current_user().nickname()
            i.i_owner2 = str(users.get_current_user().user_id())
            try:
                i.put()
                # Retrieve images
                # there i the need to encode the image data as base64:
                # person.image_bin.encode("base64").
                # It's done here in the JINJA2's template
                sleep(1)
                self.redirect("home")

            except RequestTooLargeError:
                self.redirect("error.html")
        else:
            self.response.write("<script type='text/javascript'> "
                                "window.alert('Invalid selected image or empty name'); "
                                "window.location = './home.html'; </script>")


class PostImagesHandler(webapp2.RequestHandler):
    def get(self):
        jinja = jinja2.get_jinja2(app=self.app)
        sleep(0.5)
        self.response.write(jinja.render_template("postImages.html"))

    def post(self):
        None


class CommentHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            connected = True
        else:
            connected = False

        k = ndb.Key(urlsafe=self.request.get("id"))
        im = k.get()

        if connected and im.i_owner2 == str(users.get_current_user().user_id()):
            mine = True
        else:
            mine = False

        comments = Comment.query(Comment.c_image == self.request.get("id"))
        template_values = {"img": im, "ik": self.request.get("id"), "connected": connected, "ismine": mine, "Comments": comments}
        jinja = jinja2.get_jinja2(app=self.app)
        self.response.write(jinja.render_template('commentImage.html', **template_values))

    def post(self):
        #comments = Comment.select_all()
        c = Comment()
        c.content=self.request.get("comment")
        c.c_owner = users.get_current_user().nickname()
        c.c_image = self.request.get("id")
        c.put()
        jinja = jinja2.get_jinja2(app=self.app)
        #template_values = {"Comments": comments}
        sleep(0.25)
        to_url = "/commentImage?id="+c.c_image
        self.redirect(to_url)


class MyImagesHandler(webapp2.RequestHandler):
    def get(self):
        my_images = Image.query(Image.i_owner2 == str(users.get_current_user().user_id()))
        to_show = {}
        # resize all images content
        for i in my_images:
            img = images.Image(i.image_bin)
            img.resize(width=140, height=140, allow_stretch=True)
            # img.im_feeling_lucky()
            to_show[i.key] = img.execute_transforms(output_encoding=images.PNG)
            # if images.Image(all_images[i]).height > 40 or images.Image(all_images[i]).width > 40:
            # im = images.resize(images.Image(i.image_bin), width=40, height=40)
        template_values = {"img": to_show}
        jinja = jinja2.get_jinja2(app=self.app)
        sleep(0.25)
        self.response.write(jinja.render_template("myImages.html", **template_values))

    def post(self):
        delete = ndb.Key(urlsafe=self.request.get("remove"))
        com_to_delete = Comment.query(Comment.c_image == self.request.get("remove"))
        for j in com_to_delete:
            j.key.delete()
        delete.delete()
        sleep(0.25)
        self.redirect("./myImages")

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/postImages', PostImagesHandler),
    ('/home', HomeHandler),
    ('/commentImage', CommentHandler),
    ('/myImages', MyImagesHandler)
], debug=True)
