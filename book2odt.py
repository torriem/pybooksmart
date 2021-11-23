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

print ("Converting %s to %s..." % (bookfile, odffile))

print (bs.info['booktitle'])
print (bs.info['subtitle'])
print (bs.info['authorname'])
print ('Width: %d, Height: %d' % (bs.width, bs.height))
print ('Pages: %d' % len(bs.pages))

# set up metadata
e = Element(ns('dc:creator'))
e.text = bs.info['authorname']
bodf.meta.meta.append(e)
e = Element(ns('dc:title'))
e.text = bs.info['booktitle']
bodf.meta.meta.append(e)

# set up page styles
#print (bs.width, bs.height)
print ("Writing page styles.")
for page_style in bs.get_page_styles():
    #print (page_style)
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

# Fonts entries
for font in bs.fonts:
    ss_f = Element(ns('style:font-face'))
    ss_f.attrib[ns('style:name')] = font
    ss_f.attrib[ns('svg:font-family')] = font
    
    bodf.styles.fonts.xmlnode.append(ss_f)

    ss_f = Element(ns('style:font-face'))
    ss_f.attrib[ns('style:name')] = font
    ss_f.attrib[ns('svg:font-family')] = font
    bodf.content.fonts.xmlnode.append(ss_f)
    
# Paragraph Styles
print ("Writing paragraph styles.")

for ps in bs.get_paragraph_styles():
    ss = Element(ns('style:style'))
    ss.attrib[ns('style:family')] = 'paragraph'
    ss.attrib[ns('style:name')] = ps['name']

    sp_p = Element(ns('style:paragraph-properties'))
    sp_p.attrib[ns('fo:text-align')] = bookxml.ParagraphStyle.ALIGN[ps['alignment']]
    sp_p.attrib[ns('style:justify-single-word')] = 'false'
    #print ((ps['line_spacing']+1) * 100 )
    sp_p.attrib[ns('fo:line-height')] = '%d%%' % ((ps['line_spacing'] + 1) * 100)
    sp_p.attrib[ns('fo:margin-left')] = '%dpt' % ps['left_indent']

    ss.append(sp_p)

    st_p = Element(ns('style:text-properties'))
    if ps['bold']:
        st_p.attrib[ns('fo:font-weight')] = 'bold'
    if ps['italic']:
        st_p.attrib[ns('fo:font-style')] = 'italic'
    if ps['underlined']:
        st_p.attrib[ns('style:text-underline-color')] = 'font-color'
        st_p.attrib[ns('style:text-underline-style')] = 'solid'
        st_p.attrib[ns('style:text-underline-width')] = 'auto'

    st_p.attrib[ns('fo:font-size')] = '%spt' % ps['size']
    st_p.attrib[ns('style:font-name')] = ps['font']

    ss.append(st_p)

    bodf.content.automatic_styles.xmlnode.append(ss)

    # create a break version of that style
    ss = Element(ns('style:style'))
    ss.attrib[ns('style:family')] = 'paragraph'
    ss.attrib[ns('style:name')] = '%sbreak' % ps['name']
    ss.attrib[ns('style:master-page-name')] = '%sbreak' % ps['name']



# Span Styles
print ("Writing text styles.")
for ts in bs.get_span_styles():
    #print (ts)
    ss = Element(ns('style:style'))
    ss.attrib[ns('style:family')] = 'text'
    ss.attrib[ns('style:name')] = ts['name']

    st_p = Element(ns('style:text-properties'))
    if ts['bold']:
        st_p.attrib[ns('fo:font-weight')] = 'bold'
    if ts['italic']:
        st_p.attrib[ns('fo:font-style')] = 'italic'
    if ts['underlined']:
        st_p.attrib[ns('style:text-underline-color')] = 'font-color'
        st_p.attrib[ns('style:text-underline-style')] = 'solid'
        st_p.attrib[ns('style:text-underline-width')] = 'auto'

    if ts['size'] is not None:
        st_p.attrib[ns('fo:font-size')] = '%spt' % ts['size']
    if ts['font']:
        st_p.attrib[ns('style:font-name')] = ts['font']

    ss.append(st_p)

    bodf.content.automatic_styles.xmlnode.append(ss)
bodf.save()

#process pages
print ("Converting pages...")

for page_no, page in enumerate(bs.pages):
    print ("Page %d... " % (page_no+1),end='')

    if page_no > 0:
        # emit a page break











