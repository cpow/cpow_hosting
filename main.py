#!/usr/bin/env python2.5
import cgi
import datetime
import logging
import os

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from django.core.paginator import ObjectPaginator, InvalidPage

logging.getLogger().setLevel(logging.DEBUG)


class Upload(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    image = db.BlobProperty()
    image_thumb=db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class IndexPage(webapp.RequestHandler):
    def get(self):
        self.redirect('/page1')

class MainPage(webapp.RequestHandler):
    def get(self,page):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                try:
                    page = int(page) - 1
                except:
                    page = 0
                uploads = Upload.all()
                paginator = ObjectPaginator(uploads,10)
                if page>=paginator.pages:
                    page = paginator.pages - 1
        
                pages = range(1,paginator.pages+1)
                page_max = len(pages)
            
                template_values = {
			    'images': paginator.get_page(page),
			    'user': user,
			    'pages': pages,
			    'page_max': page_max,
			    'page': page+1
		        }
		
                path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
                self.response.out.write(template.render(path, template_values))
            else:
                template_values = {}
                
                path = os.path.join(os.path.dirname(__file__), 'templates/404.html')
                self.response.out.write(template.render(path, template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class ImageThumb (webapp.RequestHandler):
    def get(self):
        upload = db.get(self.request.get("img_id"))
        if upload.image_thumb:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(upload.image_thumb)
        else:
            self.response.out.write("No image thumb")
            
class Image (webapp.RequestHandler):
    def get(self):
        upload = db.get(self.request.get("img_id"))
        if upload.image:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(upload.image)
        else:
            self.response.out.write("No Image")

class UploadHandler(webapp.RequestHandler):
    def post(self):
        upload = Upload()
        user = users.get_current_user()
        if users.get_current_user():
            if users.is_current_user_admin():
                upload.author = users.get_current_user()
                upload.content = self.request.get("content")
                image = self.request.get("img")
                page = self.request.get("page")
                image_thumb = images.resize(self.request.get("img"), 150, 250)
                upload.image = db.Blob(image)
                upload.image_thumb = db.Blob(image_thumb)
                upload.put()
                self.redirect('/page1')
            else:
                self.response.out.write("NOT ADMIN")
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
class DeleteHandler(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            if users.is_current_user_admin():
                upload = db.get(self.request.get("del_id"))
                page = self.request.get("page_num")
                if upload.is_saved():
                    upload.delete()
                    self.redirect('/page1')
                else:
                    self.response.out.write("Wrong ID")
            else:
                self.response.out.write("NOT ADMIN")
        else:
            self.redirect(users.create_login_url(self.request.uri))


application = webapp.WSGIApplication([
    ('/', IndexPage),
    ('/page(.*)', MainPage),
    ('/img_thumb', ImageThumb),
    ('/img', Image),
    ('/upload', UploadHandler),
    ('/delete', DeleteHandler)
], debug=True)


def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
