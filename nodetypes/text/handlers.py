import logging
import cgi
import datetime
import wsgiref.handlers

import re
import hypernodes
import hexdump
#import json

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import images
from nodetypes.image import png

logging.getLogger().setLevel(logging.DEBUG)
class HTML(webapp.RequestHandler):
    def post(self,path):
        if path != '':
            node = hypernodes.getHypernodeFromPath(path)
        else:
            node = None

        k = self.request.get('key')
        if k != '':
            hypernode = hypernodes.Hypernodes(parent=node,key_name=k)
        else:
            hypernode = hypernodes.Hypernodes(parent=node)

        if users.get_current_user():
           hypernode._hn_author = users.get_current_user()

        hypernode._hn_textContent = self.request.get('content')

        blob = self.request.get("blob")
        hypernode._hn_blobContent = db.Blob(blob)

        hypernode.put()
        self.get(path)

    def get(self,path):
        try:
            node = hypernodes.getHypernodeFromPath(path)
        except hypernodes.InvalidPath:
            node = None

        self.response.out.write('<html><head><title>HTML %s</title></head><body>'%path)
        if node == None:
            self.response.out.write('ROOT')
        else:
            self.response.out.write('name:%s<br/>'%node.name())
            self.response.out.write('prototype:%s<br/>'%node._hn_prototype)
            self.response.out.write('author:%s<br/>'%node._hn_author)
            self.response.out.write('creation date:%s<br/>'%node._hn_creationDate)
            
            if node._hn_blobContent != None:
                #show image properties
                decoder=png.Reader(pixels=node._hn_blobContent)
                decoder.read()
                self.response.out.write('width:%s<br/>'%decoder.width)
                self.response.out.write('height:%s<br/>'%decoder.height)
                self.response.out.write('psize:%s<br/>'%decoder.psize)
                self.response.out.write('row_bytes:%s<br/>'%decoder.row_bytes)
                self.response.out.write('planes:%s<br/>'%decoder.planes)
                self.response.out.write('pix:%s<br/>'%decoder.html())

                # Show binary as hex dump
                pseudofile = png._readable(node._hn_blobContent)
                self.response.out.write("<pre>%s</pre>"%hexdump.hexdump(pseudofile,20))



        self.response.out.write('<ul>')

        if node == None:
            childs = hypernodes.rootHypernodes()
        else:
            childs = node.childs(hypernodes.Hypernodes)
        for hypernode in childs.values():
    		self.response.out.write('<li>%s<form action="%s.html"  enctype="multipart/form-data" method="post">/<input type="text" name="key"/><input type="file" name="blob"/><input type="submit"></form></li>'%(hypernode._hn_path(),hypernode._hn_path()))

        self.response.out.write('<ul>')
        self.response.out.write('</body></html>')

class XML(webapp.RequestHandler):
    def get(self,path):
        self.response.headers["Content-Type"] = "text/xml"
        self.response.out.write('<?xml version="1.0" encoding="utf-8"?>')
        self.response.out.write('<test>XML test</test>')

class JS(webapp.RequestHandler):
    def get(self,path):
        self.response.headers["Content-Type"] = "application/javascript"
        self.response.out.write('alert("test")')

class JSON(webapp.RequestHandler):
    def get(self,path):
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write("""[{"test":"json test","afloatnumber":-122.3959},{"test2":"another object"}]""")

class PY(webapp.RequestHandler):
    def get(self,path):
        self.response.headers["Content-Type"] = "application/python"
        self.response.out.write('Pyton test')

class test(webapp.RequestHandler):
    def get(self):
        if self.request.get('root') == "source":
            self.response.out.write('[{"text": "Hypernodes","expanded": true,"classes": "important","children":['+','.join(map(hypernodes.Hypernodes.toJson,hypernodes.rootHypernodes().itervalues()))+"]}]")
        else:
            self.response.out.write("["+','.join(map(hypernodes.Hypernodes.toJson,hypernodes.Hypernodes.get(self.request.get('root')).childs(hypernodes.Hypernodes).itervalues()))+"]")
            