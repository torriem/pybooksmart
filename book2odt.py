import os
import sys
import ezodf
from ezodf.const import ALL_NSMAP
from lxml.etree import QName, Element
import bookxml

def ns(combined_name):
    prefix,name = combined_name.split(':')
    return "{%s}%s" % (ALL_NSMAP[prefix], name)

bookfile = sys.argv[1]
bookpath = os.path.dirname(os.path.abspath(bookfile))
odffile = os.path.splitext(bookfile)[0] + '.odt'

print (odffile)

bs = bookxml.BookXML(bookfile)
bodf = ezodf.newdoc('odt', odffile)

# set up metadata
e = Element(ns('dc:creator'))
e.text = bs.info['authorname']
bodf.meta.meta.append(e)
e = Element(ns('dc:title'))
e.text = bs.info['booktitle']
bodf.meta.meta.append(e)

# set up page styles
print (bs.width, bs.height)
for page_style in bs.get_page_styles():
    print (page_style)
    sp_l = Element(ns('style:page-layout'))
    sp_l.attrib[ns('style:name')] = 'M%s' % page_style['name']

    sp_l_p = Element(ns('style:page-layout-properties'))
    sp_l_p.attrib[ns('fo:margin-bottom')] = '54pt'
    sp_l_p.attrib[ns('fo:margin-top')] = '54pt'
    sp_l_p.attrib[ns('fo:margin-left')] = '54pt'
    sp_l_p.attrib[ns('fo:margin-right')] = '54pt'
    sp_l_p.attrib[ns('fo:page-height')] = '%fpt' % bs.height
    sp_l_p.attrib[ns('fo:page-width')] = '%fpt' % bs.width
    #sp_l_p.attrib[ns('style:footnote-max-height')] = '0pt'
    sp_l_p.attrib[ns('style:num-format')] = '1' # locale specific?

    if (bs.width > bs.height):
        sp_l_p.attrib[ns('style:print-orientation')] = 'landscape'
    else:
        sp_l_p.attrib[ns('style:print-orientation')] = 'portrait'
    sp_l_p.attrib[ns('style:writing-mode')] = 'lr-tb' # probably all Booksmart supported

    if page_style['bgcolor'] != '#ffffff':
        sp_l_p.attrib[ns('draw:fill')] = 'solid'
        sp_l_p.attrib[ns('draw:fill-color')] = page_style['bgcolor']
        sp_l_p.attrib[ns('fo:background-color')] = page_style['bgcolor']

    sp_l.append(sp_l_p)
    bodf.styles.automatic_styles.xmlnode.append(sp_l)

    sm_p = Element(ns('style:master-page'))

    sm_p.attrib[ns('style:name')] = page_style['name']
    sm_p.attrib[ns('style:page-layout-name')] = 'M%s' % page_style['name']

    bodf.styles.master_styles.xmlnode.append(sm_p)

# set up default page style standard
sm_p = Element(ns('style:master-page'))
sm_p.attrib[ns('style:name')] = 'Standard'
sm_p.attrib[ns('style:page-layout-name')] = "M%s" % bs.page_info[bs.pages[0]]['page_style']
bodf.styles.master_styles.xmlnode.append(sm_p)

bodf.save()








