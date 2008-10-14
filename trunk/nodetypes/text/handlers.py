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
                try:
                    #show image properties
                    decoder=png.Reader(pixels=node._hn_blobContent)
                    decoder.read()
                    self.response.out.write('width:%s<br/>'%decoder.width)
                    self.response.out.write('height:%s<br/>'%decoder.height)
                    self.response.out.write('psize:%s<br/>'%decoder.psize)
                    self.response.out.write('row_bytes:%s<br/>'%decoder.row_bytes)
                    self.response.out.write('planes:%s<br/>'%decoder.planes)
                    self.response.out.write('pix:%s<br/>'%decoder.html())
                except png.Error:
                    self.response.out.write('Not a PNG!')
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
    
    #put(*args)
    #    Called to handle an HTTP PUT request. Overridden by handler subclasses.
    #
    #head(*args)
    #    Called to handle an HTTP HEAD request. Overridden by handler subclasses.
    #
    #options(*args)
    #    Called to handle an HTTP OPTIONS request. Overridden by handler subclasses.
    #
    #delete(*args)
    #    Called to handle an HTTP DELETE request. Overridden by handler subclasses.
    #
    #trace(*args)
    #    Called to handle an HTTP TRACE request. Overridden by handler subclasses.
    #
    #handle_exception(exception, debug_mode)
    #    Called when an exception is raised by a handler. By default,
    #   handle_exception sets an HTTP status code of 500 ("Server error").
    #   If debug_mode is True it prints a stack trace to the browser.
    #   Otherwise it just prints a plain error message. A RequestHandler class
    #   can override this method to provide custom behavior.
    #
    #error(code)
    #    A shortcut method for handlers to use to return an error response.
    #   Clears the response output stream and sets the HTTP error code to code.
    #   Equivalent to calling self.response.clear() and self.response.set_status(code).
    #
    #redirect(uri, permanent=False)
    #    A shortcut method for handlers to use to return a redirect response.
    #   Sets the HTTP error code and Location: header to redirect to uri, and
    #   clears the response output stream. If permanent is True, it uses the
    #   HTTP status code 301 for a permanent redirect. Otherwise, it uses the
    #   HTTP status code 302 for a temporary redirect.
    #
    #initialize(request, response)
    #
    #Initializes the handler instance with Request and Response objects.
    #   Typically, the WSGIApplication does this after instantiating the handler class.

    def put(self,path):
        logging.debug('PUT')
    
    def head(self,path):
        logging.debug('HEAD')

    def options(self,path):
        logging.debug('OPTIONS')

    def delete(self,path):
        logging.debug('DELETE')

    def trace(self,path):
        logging.debug('TRACE')

class XML(webapp.RequestHandler):
    def get(self,path):
        self.response.headers["Content-Type"] = "text/xml"
        self.response.out.write('<?xml version="1.0" encoding="utf-8"?>')
        self.response.out.write('<test>XML test</test>')
