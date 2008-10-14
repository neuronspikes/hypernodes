import logging
import cgi
import datetime
import wsgiref.handlers
import re


from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import images

import nodetypes.text.handlers
import nodetypes.image.handlers
import nodetypes.application.handlers

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
    def put(self):
        logging.debug('PUT')

    def head(self):
        logging.debug('HEAD')

    def options(self):
        logging.debug('OPTIONS')

    def delete(self):
        logging.debug('DELETE')

    def trace(self):
        logging.debug('TRACE')
        
class test(webapp.RequestHandler):
    def get(self):
        if self.request.get('root') == "source":
            self.response.out.write('[{"text": "Hypernodes","expanded": true,"classes": "important","children":['+','.join(map(hypernodes.Hypernodes.toJson,hypernodes.rootHypernodes().itervalues()))+"]}]")
        else:
            self.response.out.write("["+','.join(map(hypernodes.Hypernodes.toJson,hypernodes.Hypernodes.get(self.request.get('root')).childs(hypernodes.Hypernodes).itervalues()))+"]")


application = webapp.WSGIApplication([
    ('/test', test),
    ('/([^~]*)\.html', nodetypes.text.handlers.HTML),
    ('/([^~]*)\.xml', nodetypes.text.handlers.XML),
    ('/([^~]*)\.js', nodetypes.application.handlers.JS),
    ('/([^~]*)\.json', nodetypes.application.handlers.JSON),
    ('/([^~]*)\.png', nodetypes.image.handlers.PNG),
    ('/([^~]*)\.py', nodetypes.application.handlers.PY),
    ('/[^~]*', MainPage),
], debug=True)


def main():
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
   main()
