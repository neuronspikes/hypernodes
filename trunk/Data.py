import logging
import cgi
import datetime
import wsgiref.handlers
#import json
import re
import png
import hexdump

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import images

logging.getLogger().setLevel(logging.DEBUG)

class Hypernodes(db.Model):
    """
    TODO:
    - initialisation des child lists
    - initialisation ? partir de bd
    - cr?ation dynamique sur req web
    - methode pour r?cup?rer un enfant
    - application de templates upload: static/images/(.*) partir des noeuds presentation
    - sanitize key_name on creation (http://code.google.com/appengine/docs/datastore/keysandentitygroups.html)
    - Optimization thru depth maps
        _hn_content_childs=()
        _hn_security_childs=()
        _hn_presentation_childs=()

    """
    _hn_prototype = db.SelfReferenceProperty()
    _hn_author = db.UserProperty()
    _hn_textContent = db.StringProperty(multiline=True)
    _hn_blobContent = db.BlobProperty()
    _hn_creationDate = db.DateTimeProperty(auto_now_add=True)

    def _hn_name(self):
        return self.key().id_or_name()

    def _hn_path(self):
        if self.key().parent()==None :
            return "/%s"%self.key().id_or_name()
        else:
            return "%s/%s"%(Hypernodes.get(self.key().parent())._hn_path(),self.key().id_or_name())

    #def getChild(name):

    def addChild(name=None,prototype=None):
        n= Hypernodes(parent=this,key_name=name)
        n.hn_prototype=prototype
        return n

    def childs(self,classtype):
        # 1000 is a hardcoded limit for google db, paging is necessary after that

        # TODO - support paging query to allow more than 1000 descendants

        nodes = db.Query(classtype).ancestor(self).fetch(1000)
        # then clean
        nodeList = []
        for n in nodes:
            if n.key().parent() == self.key():
                nodeList.append(n)
        return dict([(node.name(),node) for node in nodeList])

    def toJson(self):
        return '{\n"text": "node %s",\n"id": "%s",\n"hasChildren" : %s,\n"_hn_hn_key":"%s",\n"_hn_id":"%s",\n"_hn_name":"%s",\n"_hn_parent":"%s"\n,\n"_hn_path":"%s",\n"_hn_prototype":"%s"}'%(self.key().id_or_name(),self.key(),"true" if len(self.childs(Hypernodes))>0 else "false",self.key(),self.key().id(),self.key().name(),self.key().parent(),self._hn_path(),self._hn_prototype)

    def name(self):
        if self.key().name() != None:
            return self.key().name()
        return '%d'%self.key().id()

class InvalidPath(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)
     
def rootHypernodes():
    # return root nodes ... the hard way
    nodes = db.Query(Hypernodes).fetch(1000)    # fetch all
    # then clean
    nodeList = []
    for n in nodes:
        if n.key().parent() == None:
            nodeList.append(n)
    return dict([(node.name(),node) for node in nodeList])

def getHypernodeFromPath(path,parent=None):
    # TODO make generic, first argument : type=Hypernodes
    elements = path.partition('/')
    parentName = elements[0]
    childName = elements[2]

    if parent == None:
        if parentName =='':
            raise InvalidPath('Root is not an HyperNode')
        else:
            childs = rootHypernodes()
    else:
        childs=parent.childs(Hypernodes)

    logging.debug(childs)
    try:
        node = childs[parentName]
    except KeyError:
        node = None

    if node == None :
        if parent == None:
            raise InvalidPath('Invalid path : %s is not known'%path)
        else :
            raise InvalidPath('Invalid path after %s/ : %s is not known'%(parent._hn_path() ,path))

    if childName == '':
        return node
    else:
        return getHypernodeFromPath(childName,parent=node)


class MainPage(webapp.RequestHandler):
    def get(self):
        self.redirect('.html')


class HTML(webapp.RequestHandler):
    def post(self,path):
        if path != '':
            node = getHypernodeFromPath(path)
        else:
            node = None

        k = self.request.get('key')
        if k != '':
            hypernode = Hypernodes(parent=node,key_name=k)
        else:
            hypernode = Hypernodes(parent=node)

        if users.get_current_user():
           hypernode._hn_author = users.get_current_user()

        hypernode._hn_textContent = self.request.get('content')

        blob = self.request.get("blob")
        hypernode._hn_blobContent = db.Blob(blob)

        hypernode.put()
        self.get(path)

    def get(self,path):
        try:
            node = getHypernodeFromPath(path)
        except InvalidPath:
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
            childs = rootHypernodes()
        else:
            childs = node.childs(Hypernodes)
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

class PNG (webapp.RequestHandler):
    # ATTENTION c'est n'importe qule blob sui sera retourn? avec le type png, m?me si c'est un jpeg ou autre
    # ?a ne ramene pas le format a autre chose in jpeg reste un jpeg...
    def get(self,path):
        try:
            node = getHypernodeFromPath(path)
        except InvalidPath:
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

class test(webapp.RequestHandler):
    def get(self):
        if self.request.get('root') == "source":
            self.response.out.write('[{"text": "Hypernodes","expanded": true,"classes": "important","children":['+','.join(map(Hypernodes.toJson,rootHypernodes().itervalues()))+"]}]")
        else:
            self.response.out.write("["+','.join(map(Hypernodes.toJson,Hypernodes.get(self.request.get('root')).childs(Hypernodes).itervalues()))+"]")


application = webapp.WSGIApplication([
    ('/test', test),
    ('/([^~]*)\.html', HTML),
    ('/([^~]*)\.xml', XML),
    ('/([^~]*)\.js', JS),
    ('/([^~]*)\.json', JSON),
    ('/([^~]*)\.png', PNG),
    ('/([^~]*)\.py', PY),
    ('/[^~]*', MainPage),
], debug=True)


def main():
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
   main()
