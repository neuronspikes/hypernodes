#!/usr/bin/python
#******************************************************************************\
#* $Source: /cvsroot/pyexif/pyexif/bin/exifinfo.py,v $
#* $Id: exifinfo.py,v 1.1 2001/09/04 18:52:27 blais Exp $
#*
#* Copyright (C) 2001, Martin Blais <blais@iro.umontreal.ca>
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 2 of the License, or
#* (at your option) any later version.
#*
#* This program is distributed in the hope that it will be useful,
#* but WITHOUT ANY WARRANTY; without even the implied warranty of
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#* GNU General Public License for more details.
#*
#* You should have received a copy of the GNU General Public License
#* along with this program; if not, write to the Free Software
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#*
#*****************************************************************************/

"""Output EXIF tags information for an image file."""

__version__ = "$Revision: 1.1 $"

#===============================================================================
# EXTERNAL DECLARATIONS
#===============================================================================

from distutils.fancy_getopt \
     import FancyGetopt, OptionDummy, translate_longopt, wrap_text

import os, os.path, sys
import string, re
#from stat import *

import curator.exif as exif
import curator.formatexif
import imghdr

#===============================================================================
# LOCAL DECLARATIONS
#===============================================================================

#-------------------------------------------------------------------------------
#
def test_jpeg_exif(h, f):
    """imghdr test for JPEG data in EXIF format"""
    if h[6:10].lower() == 'exif':
        return 'jpeg'

imghdr.tests.append(test_jpeg_exif)

#-------------------------------------------------------------------------------
#
fast_imgexts = [ 'jpeg', 'jpg', 'gif', 'png', 'rgb', 'pbm', 'pgm', 'ppm', \
                 'tiff', 'tif', 'rast', 'xbm', 'bmp' ]

def imgwhat( fn, fast = None ):

    """Faster, sloppier, imgwhat, that doesn't require opening the file if we
    specified that it should be fast."""

    if fast == 1:
        ( base, ext ) = os.path.splitext( fn )
        if ext[1:].lower() in fast_imgexts:
            return ext.lower()
        else:
            return None
    else:
        # slow method, requires opening the file
        try:
            return imghdr.what( fn )
        except IOError:
            return None



#-------------------------------------------------------------------------------
#
def read_file( path ):
    try:
	file = open(path, "rb")
	data = file.read()
	file.close()
    except IOError:
    	print "ERROR: could not read file '%s'!" % path
	sys.exit(-1)
    return data

#-------------------------------------------------------------------------------
#
def date_fr(date_str):

    """This function formats the date/time like we prefer them."""

    return date_str[:4] +'-'+ date_str[5:7] +'-'+ date_str[8:10] +' '+\
           date_str[11:13] +':'+ date_str[14:16] +':'+ date_str[17:19]

#===============================================================================
# MAIN
#===============================================================================

#-------------------------------------------------------------------------------
#
def main():
    #
    # options parsing
    #
    
    # Options declaration
    optmap = [
        ( 'help', 'h', "show detailed help message." ),
        ( 'version', 'V', "prints version." ),
        ( 'verbose', 'v', "verbose." ),
        ( 'debug', None, "debug." )
        ]
    
    def opt_translate(opt):
        o = opt[0]
        if o[-1] == '=': # option takes an argument?
            o = o[:-1]
        return translate_longopt( o )
    
    global wsre
    wsre = re.compile( '\s+', re.MULTILINE )
    def del_ws( t ):
        return re.sub( wsre, ' ', t )
    
    optmapb = []
    for o in optmap:
        optmapb.append( ( o[0], o[1], del_ws(o[2]) ) )
    
    optmap = optmapb
    
    global opts
    opts = OptionDummy( map( opt_translate, optmap ) )
    parser = FancyGetopt( optmap )
    
    try:
        args = parser.getopt( args=sys.argv[1:], object=opts )
    except:
        print >> sys.stderr, "Error: argument error. Use --help for more info."
        sys.exit(1)
    
    for fn in args:
        if not os.path.exists( fn ):
            print >> sys.stderr, \
                  "Error: can't open", fn
            continue

        ver = 0
        if opts.verbose:
            ver = 1
        if opts.debug:
            ver = 255
        tags = exif.parse( fn, ver, mode=exif.ASCII )
        if tags == {}:
            print >> sys.stderr, \
                  "Error: no exif header in", fn
            continue
        tags['PhotoName'] = os.path.basename( fn )

        print_tags = curator.formatexif.PrintMap(tags)
        print curator.formatexif.formatText( tags, print_tags )
        
# Run main if loaded as a script
if __name__ == "__main__":
    main()

