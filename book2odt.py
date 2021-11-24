import os
import sys
import ezodf
from ezodf.const import ALL_NSMAP
from lxml.etree import QName, Element
import bookxml

def ns(combined_name):
    prefix,name = combined_name.split(':')
    return "{%s}%s" % (ALL_NSMAP[prefix], name)

def create_frame(pageno, frameno, x,y, width, height, zindex):
    draw_frame = Element(ns('draw:frame'))
    draw_frame.attrib[ns('draw:name')] = 'Frame%d' % (frameno)
    draw_frame.attrib[ns('draw:style-name')] = 'OuterFrameStyle'
    draw_frame.attrib[ns('svg:width')] = '%dpt' % width
    draw_frame.attrib[ns('svg:height')] = '%dpt' % height
    draw_frame.attrib[ns('svg:x')] = '%dpt' % x
    draw_frame.attrib[ns('svg:y')] = '%dpt' % y
    draw_frame.attrib[ns('text:anchor-type')] = 'page'
    draw_frame.attrib[ns('text:anchor-page-number')] = '%d' % (pageno + 1)
    draw_frame.attrib[ns('draw:z-index')] = '%d' % (zindex + 1)

    return draw_frame

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

    # create a page break paragraph style that switches to this page style
    ss = Element(ns('style:style'))
    ss.attrib[ns('style:family')] = 'paragraph'
    ss.attrib[ns('style:name')] = '%sbreak' % page_style['name']
    ss.attrib[ns('style:master-page-name')] = '%s' % page_style['name']

    sp_p = Element(ns('style:paragraph-properties'))
    sp_p.attrib[ns('fo:break-before')] = 'page'

    ss.append(sp_p)

    bodf.content.automatic_styles.xmlnode.append(ss)

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
    if ps['underline']:
        st_p.attrib[ns('style:text-underline-color')] = 'font-color'
        st_p.attrib[ns('style:text-underline-style')] = 'solid'
        st_p.attrib[ns('style:text-underline-width')] = 'auto'

    st_p.attrib[ns('fo:font-size')] = '%spt' % ps['size']
    st_p.attrib[ns('style:font-name')] = ps['font']
    if ps['color']:
        st_p.attrib[ns('fo:color')] = ps['color']

    ss.append(st_p)

    bodf.content.automatic_styles.xmlnode.append(ss)




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
    if ts['underline']:
        st_p.attrib[ns('style:text-underline-color')] = 'font-color'
        st_p.attrib[ns('style:text-underline-style')] = 'solid'
        st_p.attrib[ns('style:text-underline-width')] = 'auto'

    if ts['size'] is not None:
        st_p.attrib[ns('fo:font-size')] = '%spt' % ts['size']
    if ts['font']:
        st_p.attrib[ns('style:font-name')] = ts['font']
    if ts['color']:
        st_p.attrib[ns('fo:color')] = ts['color']


    ss.append(st_p)

    bodf.content.automatic_styles.xmlnode.append(ss)

# LibreOffice Default Frame style
style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'graphic'
style_style.attrib[ns('style:name')] = 'Frame'

graphic_properties = Element(ns('style:graphic-properties'))
graphic_properties.attrib[ns('fo:border')] = '0.06pt solid #000000'
graphic_properties.attrib[ns('fo:margin-bottom')] = '0.0791in'
graphic_properties.attrib[ns('fo:margin-top')] = '0.0791in'
graphic_properties.attrib[ns('fo:margin-left')] = '0.0591in'
graphic_properties.attrib[ns('fo:margin-right')] = '0.0591in'
graphic_properties.attrib[ns('fo:padding')] = '0.0591n'
graphic_properties.attrib[ns('style:horizontal-pos')] = 'center'
graphic_properties.attrib[ns('style:vertical-pos')] = 'top'
graphic_properties.attrib[ns('style:vertical-rel')] = 'paragraph-content'
graphic_properties.attrib[ns('style:horizontal-rel')] = 'paragaph-content'
graphic_properties.attrib[ns('style:wrap')] = 'parallel'


# Outer frame style
style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'graphic'
style_style.attrib[ns('style:name')] = 'OuterFrameStyle'
style_style.attrib[ns('style:parent-style-name')] = 'Frame'

graphic_properties = Element(ns('style:graphic-properties'))
graphic_properties.attrib[ns('fo:border')] = 'none'
graphic_properties.attrib[ns('fo:margin-bottom')] = '0in'
#graphic_properties.attrib[ns('fo:margin-top')] = '0in'
#graphic_properties.attrib[ns('fo:margin-left')] = '0in'
#graphic_properties.attrib[ns('fo:margin-right')] = '0in'
graphic_properties.attrib[ns('fo:padding')] = '0in'
graphic_properties.attrib[ns('style:horizontal-pos')] = 'from-left'
graphic_properties.attrib[ns('style:vertical-pos')] = 'from-top'
graphic_properties.attrib[ns('style:vertical-rel')] = 'page'
graphic_properties.attrib[ns('style:horizontal-rel')] = 'page'
graphic_properties.attrib[ns('style:wrap')] = 'run-through'

style_style.append(graphic_properties)
bodf.content.automatic_styles.xmlnode.append(style_style)

#process pages
print ("Converting pages...")

frame_no = 0

for page_no, page in enumerate(bs.pages):
    page_item_count = 0

    print ("Page %d... " % (page_no+1),end='')
    print (bs.page_info[page])

    if page_no > 0:
        # emit a page break
        p = Element(ns('text:p'))

        if 'pagination' in bs.page_info[page] and \
           bs.page_info[page]['pagination'] == 'START_PAGE_NUMBERS':
            # create a paragraph style that breaks the page and sets the page number to 1
            ss = Element(ns('style:style'))
            ss.attrib[ns('style:family')] = 'paragraph'
            ss.attrib[ns('style:name')] = '%sbreakresetpageno' % bs.page_info[page]['page_style']
            ss.attrib[ns('style:master-page-name')] = '%s' % bs.page_info[page]['page_style']

            sp_p = Element(ns('style:paragraph-properties'))
            sp_p.attrib[ns('fo:break-before')] = 'page'
            sp_p.attrib[ns('style:page-number')] = '1'

            ss.append(sp_p)

            bodf.content.automatic_styles.xmlnode.append(ss)

            p.attrib[ns('text:style-name')] = '%sbreakresetpageno' % bs.page_info[page]['page_style']
        else:
            p.attrib[ns('text:style-name')] = '%sbreak' % bs.page_info[page]['page_style']
    else:
        p = Element(ns('text:p'))
    bodf.body.xmlnode.append(p)

    # Text boxes

    for tb in bs.text_boxes[page]:
        outer_frame = create_frame(page_no, frame_no, tb.x, tb.y, tb.width, tb.height, page_item_count)
        bodf.body.xmlnode.insert(2,outer_frame)

        dtb = Element(ns('draw:text-box'))
        dtb.attrib[ns('fo:max-height')] = '%dpt' % tb.height

        outer_frame.append(dtb)

        for p in tb.paragraphs:
            paragraph = Element(ns('text:p'))
            if p.style:
                paragraph.attrib[ns('text:style-name')] = p.style

            for s in p.spans:
                #TODO variables
                span = Element(ns('text:span'))
                if s.style:
                    span.attrib[ns('text:style-name')] = s.style
                span.text = s.text
                print (s.style, s.text)
                paragraph.append(span)
            dtb.append(paragraph)

        page_item_count +=1
        frame_no +=1





bodf.save()










