import logging
import cgi
import datetime
import wsgiref.handlers
import re

import png

import hypernodes

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import images

logging.getLogger().setLevel(logging.DEBUG)

class PNG (webapp.RequestHandler):
    # ATTENTION c'est n'importe qule blob sui sera retourn? avec le type png, m?me si c'est un jpeg ou autre
    # ?a ne ramene pas le format a autre chose in jpeg reste un jpeg...
    def get(self,path):
        try:
            node = getHypernodeFromPath(path)
        except hypernodes.InvalidPath:
            node = None

        if node!= None:
            self.response.headers['Content-Type'] = "image/png"
            image = images.Image(node._hn_blobContent) # Normalise au format PNG
            #do nothing, flip twice.
            image.vertical_flip()
            image.execute_transforms(output_encoding=images.PNG)
            image.vertical_flip()
            self.response.out.write(image.execute_transforms(output_encoding=images.PNG))
        else:
            self.error(404)

