from bs4 import BeautifulSoup
from xml.sax import saxutils
import ezodf

import os
import sys
import PIL.Image
from ezodf.const import ALL_NSMAP
from lxml.etree import QName, Element

#from imagefile import ImageObject

ALIGNMENT = { 1: 'center',
              2: 'end',
              0: 'start',
              3: 'justify'}


def ns(combined_name):
    prefix,name = combined_name.split(':')
    return "{%s}%s" % (ALL_NSMAP[prefix], name)

def split_list( list_ ):
    for x in range(0, len(list_), 2):
        yield (list_[x], list_[x+1])

class ImageObject(ezodf.filemanager.FileObject):

    def __init__(self, name, filename):
        super(ImageObject, self).__init__(name, None)
        self.image_filename = filename

    def tobytes(self):
        imagefile = open(self.image_filename, 'rb')
        return imagefile.read()

class javaxml_exception(Exception):
    pass

def javaxml_to_python(object_):
    current_object = None
    if object_["class"] == "java.util.LinkedList":
        #print ("Creating a new list")
        current_object = []

        for operation in object_.contents: # list contents
            if operation == '\n': continue
            #print ("operation is: ", operation.name, operation["method"])
            if operation["method"] == "add": # object, method = add
                #print ("adding to list:")
                for to_add in operation.contents: # what will we add?
                    if to_add != '\n':
                        if to_add.name == "object":
                            current_object.append(javaxml_to_python(to_add))
                        elif to_add.name == "string":
                            #print ("added string")
                            current_object.append(to_add.contents[0])
                        elif to_add.name == "null":
                            #print ("added null")
                            current_object.append(None)
                        else:
                            print ("we got: ",to_add.name)
                            print (operation)
                            raise javaxml_exception("unrecognized list item")
            else:
                print ("we see:", operation["method"])
                raise javaxml_exception("unrecognized list operation")


    elif object_["class"] == "java.util.HashMap":
        #print ("Creating a new dict")
        current_object = {}
        for operation in object_.contents: # dict contents
            if operation == '\n': continue
            #print ("operation is: ", operation.name, operation["method"])
            if operation["method"] == "put": # object, method = put
                #print ("adding to dict:")

                # First will always be a string key, second will be a value
                key = None
                for to_add in operation.contents: # what will we add?
                    if to_add == '\n': continue

                    if not key: 
                        key = to_add.contents[0]
                        continue

                    if to_add.name == "object":

                        if to_add.has_attr("class"):
                            current_object[key] = javaxml_to_python(to_add)

                        elif to_add.has_attr("idref"):
                            current_object[key] = to_add["idref"]

                    elif to_add.name == "string":
                        current_object[key] = (to_add.contents[0])
                    elif to_add.name == "null":
                        current_object[key] = None
                    elif to_add.name == "int":
                        current_object[key] = int(to_add.contents[0])
                    elif to_add.name == "boolean":
                        current_object[key] = to_add.contents[0] #TODO convert to real boolean
                    else:
                        print ("we got: ",to_add.name)
                        print (operation)
                        raise javaxml_exception("unrecognized dict value")
                    break # we only expect two xml elements in a hashmap, and we now have both
            else:
                print ("we see:", operation["method"])
                raise javaxml_exception("unrecognized dict operation")

    elif object_["class"] == "java.awt.Color":
        current_object = {}
        current_object["color_id"] = object_['id']

        red = None
        green = None
        blue = None
        alpha = None

        for i in object_.contents:
            if i == '\n': continue

            if not red:
                red = int(i.contents[0])
            if not green:
                green = int(i.contents[0])
            if not blue:
                blue = int(i.contents[0])
            if not alpha:
                alpha = int(i.contents[0])

        current_object['color'] = (red, green, blue, alpha)
    else:
        print ("Unknown object: ", _object["class"])
        raise javaxml_exception("unimplemented object class %s" % _object["class"])


    return current_object


last_paragraph_style = 0
                            
def make_paragraph_style(odfdoc, style_dict, alignment=0):
    global last_paragraph_style

    last_paragraph_style += 1
    style_style = Element(ns('style:style'))
    style_style.attrib[ns('style:family')] = 'paragraph'
    style_style.attrib[ns('style:parent-style-name')] = 'Frame_20_contents'
    style_style.attrib[ns('style:name')] = 'P%d' % last_paragraph_style

    odfdoc.content.automatic_styles.xmlnode.append(style_style);
    
    style_paragraph_properties = Element(ns('style:paragraph-properties'))
    style_paragraph_properties.attrib[ns('fo:text-align')]=ALIGNMENT[alignment]
    style_paragraph_properties.attrib[ns('style:justify-single-word')]='false'

    style_style.append(style_paragraph_properties)

    style_text_properties = Element(ns('style:text-properties'))
    if 'font' in style_dict:
        style_text_properties.attrib[ns('style:font-name')] = style_dict['font']
        make_font_decl(odfdoc, style_dict['font'])
    if 'family' in style_dict:
        style_text_properties.attrib[ns('style:font-name')] = style_dict['family']
        make_font_decl(odfdoc, style_dict['family'])
    if 'size' in style_dict:
        if isinstance(style_dict['size'],str):
            style_text_properties.attrib[ns('fo:font-size')] = '%s' % style_dict['size']
        else:
            style_text_properties.attrib[ns('fo:font-size')] = '%d' % style_dict['size']
    if 'bold' in style_dict and style_dict['bold'] == 'true':
        style_text_properties.attrib[ns('fo:font-weight')] = 'bold'
        

    style_style.append(style_text_properties)

    return 'P%d' % last_paragraph_style

last_span_style = 0

def make_span_style(odfdoc, style_dict):
    global last_span_style

    last_span_style += 1
    style_style = Element(ns('style:style'))
    style_style.attrib[ns('style:family')] = 'text'
    style_style.attrib[ns('style:name')] = 'T%d' % last_span_style

    odfdoc.content.automatic_styles.xmlnode.append(style_style);
    
    style_text_properties = Element(ns('style:text-properties'))
    
    if 'family' in style_dict:
        style_text_properties.attrib[ns('style:font-name')] = style_dict['family']
        make_font_decl(odfdoc, style_dict['family'])
    if 'size' in style_dict:
        style_text_properties.attrib[ns('fo:font-size')] = '%d' % style_dict['size']
    if 'bold' in style_dict and style_dict['bold'] == 'true':
        style_text_properties.attrib[ns('fo:font-weight')] = 'bold'
 

    style_style.append(style_text_properties)

    return 'T%d' % last_span_style

seenfonts = []
def make_font_decl(odfdoc, fontname):
    global seenfonts

    if fontname in seenfonts: return

    style_font_face = Element(ns('style:font-face'))
    style_font_face.attrib[ns('style:name')] = fontname
    style_font_face.attrib[ns('svg:font-family')] = fontname

    odfdoc.content.fonts.xmlnode.append(style_font_face)
    seenfonts.append(fontname)
    

bsf = open(sys.argv[1],"r") #assume utf-8
library_path = os.path.dirname(os.path.abspath(sys.argv[1])) + '/library'


soup = BeautifulSoup(bsf.read(),"lxml-xml")

pagesList = None
for pl in soup.find_all("pagesList"):
    if pl.parent.name == "Book":
        pagesList = pl.find_all("pages")

if pagesList:
    pagesList = [page["id"] for page in pagesList]

width = int(soup.Book["width"])
height = int(soup.Book["height"])


print (width, height)

doc = ezodf.newdoc('odt','bookout.odt','blurb.ott')

bookVars = soup.find_all('bookVar')

for bookVar in bookVars:
    if bookVar['name'] == '$AuthorName':
        doc.meta.meta.find(ns('meta:initial-creator')).text = bookVar['value']
        doc.meta.meta.find(ns('dc:creator')).text = bookVar['value']
    elif bookVar['name'] == '$BookTitle':
        doc.meta.meta.find(ns('dc:title')).text = bookVar['value']


page_layout = doc.styles.automatic_styles.xmlnode.find(ns('style:page-layout'))
page_layout_properties = page_layout.find(ns('style:page-layout-properties'))
page_layout_properties.attrib[ns('fo:page-width')] = "%dpt" % width
page_layout_properties.attrib[ns('fo:page-height')] = "%dpt" % height

if width > height:
    page_layout_properties.attrib[ns('style:print-orientation')] = "landscape"
else:
    page_layout_properties.attrib[ns('style:print-orientation')] = "portrait"

# create a parent Frame style

style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'graphic'
style_style.attrib[ns('style:name')] = 'Frame'

style_graphic_properties = Element(ns('style:graphic-properties'))
style_graphic_properties.attrib[ns('text:anchor-type')] = 'paragraph'
style_graphic_properties.attrib[ns('svg:x')] = '0in'
style_graphic_properties.attrib[ns('svg:y')] = '0in'
style_graphic_properties.attrib[ns('fo:margin-left')] = '0.0791in'
style_graphic_properties.attrib[ns('fo:margin-right')] = '0.0791in'
style_graphic_properties.attrib[ns('fo:margin-top')] = '0.0791in'
style_graphic_properties.attrib[ns('fo:margin-bottom')] = '0.0791in'
style_graphic_properties.attrib[ns('style:wrap')] = 'parallel'
style_graphic_properties.attrib[ns('style:number-wrapped-paragraphs')] = 'no-limit'
style_graphic_properties.attrib[ns('style:wrap-contour')] = 'false'
style_graphic_properties.attrib[ns('style:vertical-pos')] = 'middle'
style_graphic_properties.attrib[ns('style:vertical-rel')] = 'paragraph-content'
style_graphic_properties.attrib[ns('style:horizontal-pos')] = 'center'
style_graphic_properties.attrib[ns('style:horizontal-rel')] = 'paragraph-content'
style_graphic_properties.attrib[ns('fo:padding')] = '0.0591in'
style_graphic_properties.attrib[ns('fo:border')] = '0.06pt solid #000000'

style_style.append(style_graphic_properties)
doc.styles.styles.xmlnode.append(style_style)

# create a automatic style paragraph style for our page break.  We can
# use the same one for each page break paragraph.  Word processor will
# likely rename it, but that's okay.

# <style:style style:parent-style-name="Standard" style:family="paragraph" style:name="SOMENAME">
#   <style:paragraph-properties fo:break-before="page"/>
# </style:style>

style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'paragraph'
style_style.attrib[ns('style:name')] = 'BlurbPageBreak1'
style_style.attrib[ns('style:parent-style-name')] = 'Standard'

style_paragraph_properties = Element(ns('style:paragraph-properties'))
style_paragraph_properties.attrib[ns('fo:break-before')] = 'page'

style_style.append(style_paragraph_properties)

doc.content.automatic_styles.xmlnode.append(style_style)

style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'paragraph'
style_style.attrib[ns('style:name')] = 'BlurbPageBreakResetNum'
style_style.attrib[ns('style:parent-style-name')] = 'Standard'
style_style.attrib[ns('style:master-page-name')] = 'Standard'

style_paragraph_properties = Element(ns('style:paragraph-properties'))
style_paragraph_properties.attrib[ns('fo:break-before')] = 'page'
style_paragraph_properties.attrib[ns('style:page-number')] = '1'

style_style.append(style_paragraph_properties)

doc.content.automatic_styles.xmlnode.append(style_style)

#style for drawing boxes (temporary)
style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'graphic'
style_style.attrib[ns('style:name')] = 'blurbboxstyle'
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
doc.content.automatic_styles.xmlnode.append(style_style)



frame_count=1
for pageno, page in enumerate(pagesList):
    page_item_count=0
    print ("Processing page %d (%s):" % (pageno,page))
    page_info = soup.find("Page", id=page)

    if pageno > 0:
        # insert a page break
        #TODO: parse the /Book/bookObjects/Page for this page to
        #set the page number with a pagebreak style to 1.

        # Add a new page break paragraph to the body
        paragraph = Element(ns('text:p'))
        if 'pagination' in page_info.attrs and page_info.attrs['pagination'] == 'START_PAGE_NUMBERS':
            paragraph.attrib[ns('text:style-name')] = 'BlurbPageBreakResetNum'
        else:
            paragraph.attrib[ns('text:style-name')] = 'BlurbPageBreak1'
            paragraph.text = ''

        doc.body.xmlnode.append(paragraph)
         
    #paragraph = Element(ns('text:p'))
    #paragraph.text='Page %d' % pageno

    #doc.body.xmlnode.append(paragraph)

    items = soup.find_all(parentId=page)

    for item in items:

        # get x,y, width, height coords
        coord = [int(x) for x in item['re'].split(',')]

        #print ("box coords in pts are: ", coord)
        #print ([x / 72.0 for x in coord])

        #outer frame for either text or graphics, can have a border
        draw_frame = Element(ns('draw:frame'))
        draw_frame.attrib[ns('draw:name')] = 'Frame%d' % (frame_count)
        draw_frame.attrib[ns('draw:style-name')] = 'blurbboxstyle'
        draw_frame.attrib[ns('svg:width')] = '%dpt' % coord[2]
        draw_frame.attrib[ns('svg:height')] = '%dpt' % coord[3]
        draw_frame.attrib[ns('svg:x')] = '%dpt' % coord[0]
        draw_frame.attrib[ns('svg:y')] = '%dpt' % coord[1]
        draw_frame.attrib[ns('text:anchor-type')] = 'page'
        draw_frame.attrib[ns('text:anchor-page-number')] = '%d' % (pageno + 1)
        draw_frame.attrib[ns('draw:z-index')] = '%d' % (page_item_count+1)
        doc.body.xmlnode.insert(2,draw_frame)

        page_item_count += 1
        frame_count +=1

        if item.name == "ImageContent":
            if (item.has_attr("content")):
                booksmart_image=item["content"]
                if booksmart_image[:8] != 'booklogo':

                    img = PIL.Image.open('%s/%s.original' % (library_path,booksmart_image))
                    
                    a = ImageObject('Pictures/%s.%s' % (booksmart_image, img.format.lower()),
                                    '%s/%s.original' % (library_path,booksmart_image))

                    doc.filemanager.register('Pictures/%s.%s' % (booksmart_image, img.format.lower()),
                                             a, 'image/%s' % (img.format.lower()))
                    #print ("%s.original" % item["content"])

                    transformations = item.find_all("TransformEffect")
                    x = int(transformations[0]['x'])
                    y = int(transformations[0]['y'])
                    zoom = float(transformations[0]['zoom']) / 100.0

                    img_aspect = img.size[0] / img.size[1]
                    box_aspect = coord[2] / coord[3]

                    #print (transformations)

                    # calculate pix per point at 100% scale (smallest side scaled to box)
                    # Booksmart transformation numbers are all in points based on the
                    # box size, so we have to figure out what that means in pixels so we
                    # can compute the necessary clipping box in pixels.

                    if img_aspect >= 1 and box_aspect >= 1:
                        # aspects both >= 1

                        if box_aspect < img_aspect:
                            # case 1, box aspect < image aspect: scale image y
                            pixperpt = img.size[1] / coord[3]
                        else:
                            # case 2, box aspect > image aspect: scale image x
                            pixperpt = img.size[0] / coord[2]
                    elif img_aspect < 1 and box_aspect < 1:
                        # aspects both < 1
                        if box_aspect > img_aspect:
                            # case 1, box aspect > image aspect: scale image x
                            pixperpt = img.size[0] / coord[2]
                        else:
                            # case 2, box aspect < image aspect: scale image y
                            pixperpt = img.size[1] / coord[3]
                    elif box_aspect >=1 and img_aspect <1:
                            # box aspect >= 1, image aspect < 1: scale image x
                            pixperpt = img.size[0] / coord[2]
                    else:
                            # box aspect < 1, image aspect >= 1: scale image y
                            pixperpt = img.size[1] / coord[3]

                    # calculate how much of the image will be shown as a percentage
                    clip_pixperpt = pixperpt / zoom

                    # enlarge image dimensions by zoom.
                    width = img.size[0] / clip_pixperpt #width in points
                    height = img.size[1] / clip_pixperpt #height in points
                    crop_left = 0
                    crop_right = 0
                    crop_top = 0
                    crop_bottom = 0
                    
                    # if x is negative, crop on the left, set x to 0
                    if x < 0:
                        crop_left = int(abs(x) * clip_pixperpt) #in pixels
                        width += x # remove left crop from width
                        x = 0
                    
                    # if y is negative, crop on the top, set y to 0
                    if y < 0:
                        crop_top = int(abs(y) * clip_pixperpt)
                        height += y # remove top crop from height
                        y = 0

                    if (width + x) > coord[2]: 
                        # if image sticks beyond the right side of the frame
                        # crop it from the right
                        crop_right = width + x - coord[2]
                        width -= crop_right
                        crop_right = int(crop_right * clip_pixperpt)

                    if (height + y ) > coord[3]:
                        # if image sticks beyond the bottom of the frame,
                        # crop it from the bottom.
                        crop_bottom = height + y - coord[3]
                        height -= crop_bottom
                        crop_bottom = int(crop_bottom * clip_pixperpt)

                    # style to set up the image crop
                    style_style = Element(ns('style:style'))
                    style_style.attrib[ns('style:name')] = 'imageframe%d' % frame_count
                    style_style.attrib[ns('style:family')] = 'graphic'
                    style_style.attrib[ns('style:parent-style-name')] = 'Graphics'
                    doc.content.automatic_styles.xmlnode.append(style_style)

                    style_graphic_properties = Element(ns('style:graphic-properties'))
                    style_graphic_properties.attrib[ns('style:mirror')] = 'none'
                    style_graphic_properties.attrib[ns('fo:clip')] = 'rect(%dpx, %dpx, %dpx, %dpx)' % (crop_top, crop_right, crop_bottom, crop_left)
                    style_graphic_properties.attrib[ns('draw:luminance')] = '0%'
                    style_graphic_properties.attrib[ns('draw:contrast')] = '0%'
                    style_graphic_properties.attrib[ns('draw:red')] = '0%'
                    style_graphic_properties.attrib[ns('draw:green')] = '0%'
                    style_graphic_properties.attrib[ns('draw:blue')] = '0%'
                    style_graphic_properties.attrib[ns('draw:gamma')] = '100%'
                    style_graphic_properties.attrib[ns('draw:color-inversion')] = 'false'
                    style_graphic_properties.attrib[ns('draw:image-opacity')] = '100%'
                    style_graphic_properties.attrib[ns('draw:color-mode')] = 'standard'
                    style_style.append(style_graphic_properties)

                    # place image at x,y, set display width and height
                    # sub-frame around graphic so we can position image properly within the
                    # frame. This is to emulate the way Booksmart allows placing of images,
                    # zooming, panning, etc
                    draw_text_subbox = Element(ns('draw:text-box'))
                    draw_text_subbox.attrib[ns('fo:min-height')] = '%dpt' % coord[3]
                    draw_frame.append(draw_text_subbox)


                    draw_subframe = Element(ns('draw:frame'))
                    draw_subframe.attrib[ns('draw:name')] = 'ImageFrame%d' % (frame_count)
                    draw_subframe.attrib[ns('draw:style-name')] = 'imageframe%d' % frame_count
                    draw_subframe.attrib[ns('svg:width')] = '%dpt' % width
                    draw_subframe.attrib[ns('svg:height')] = '%dpt' % height
                    draw_subframe.attrib[ns('svg:x')] = '%dpt' % x
                    draw_subframe.attrib[ns('svg:y')] = '%dpt' % y
                    draw_subframe.attrib[ns('text:anchor-type')] = 'frame'

                    draw_text_subbox.append(draw_subframe)

                    draw_image = Element(ns('draw:image'))
                    draw_image.attrib[ns('xlink:href')] = "Pictures/%s.%s" % (booksmart_image, img.format.lower())
                    draw_image.attrib[ns('xlink:type')] = 'simple'
                    draw_image.attrib[ns('xlink:show')] = 'embed'
                    draw_image.attrib[ns('xlink:actuate')] = 'onLoad'
                    #draw_image.attrib[ns('loext:mime-type')] = 'image/%s' % (img.format.lower())

                    draw_subframe.append(draw_image)


        elif item.name == "TextContent":
            variable = None

            if 'dc' in item.attrs:
                variable = item['dc']

            container_style = {}
            if 'ts' in item.attrs:
                textstyledef = soup.find('TextStyleDefinition',id=item.attrs['ts'])
                if textstyledef:
                    container_style = textstyledef.attrs

            #TODO font color too

            textxml = (list(item.dm.children)[0])

            textsoup = BeautifulSoup(textxml, "lxml-xml")
            
            draw_text_box = Element(ns('draw:text-box'))
            draw_text_box.attrib[ns('fo:min-height')] = '%dpt' % coord[3]
            draw_frame.append(draw_text_box)

            for object_ in textsoup.java.contents:
                if object_ != "\n" and object_.name == "object":
                    text_data = javaxml_to_python(object_)
                    
                    style_dict = {}

                    display_pageno = False
                    for item in text_data:
                        if isinstance(item, dict):
                            style_dict = {}
                            
                            # bring in container defaults
                            for key in container_style:
                                style_dict[key] = container_style[key]
                            # override with resolver style

                            if item['resolver']:
                                textstyledef = soup.find('TextStyleDefinition',id=item['resolver'].split('.')[0])
                                if textstyledef:
                                    for key in textstyledef.attrs:
                                        style_dict[key] = textstyledef.attrs[key]

                            for key in item:
                                # override anything specified along with the resolver?
                                style_dict[key] = item[key]
                                

                            paragraph = Element(ns('text:p'))

                            alignment = style_dict.get('align',0)
                            alignment = style_dict.get('Alignment',alignment)
                            alignment = int(alignment)
                            
                            paragraph.attrib[ns('text:style-name')] = make_paragraph_style(doc,style_dict,alignment)
                            draw_text_box.append(paragraph)
                            continue

                        generator_wrapper = (i for i in item)
                        for part in generator_wrapper:
                            if isinstance(part, dict):
                                span = part #override again with span-specific formatting
                                text = next(generator_wrapper)
                                style =  (make_span_style(doc, span))

                                print (text)

                                span = Element(ns('text:span'))

                                if text.strip() and variable == '$PageNumber':
                                    fieldtext = Element(ns('text:page-number'))
                                    fieldtext.attrib[ns('text:select-page')] = 'current'
                                    fieldtext.text = text
                                    span.append(fieldtext)
                                elif text.strip() and variable == '$BookTitle':
                                    fieldtext = Element(ns('text:title'))
                                    fieldtext.text = text
                                    span.append(fieldtext)
                                else:
                                    span.text = text
                                span.attrib[ns('text:style-name')] = style


                                paragraph.append(span)
                            else:
                                if part and part.strip():
                                    paragraph.text = part

        
    #if pageno ==20: break
            

print ('Saving document with pictures.  May take a while...')
doc.save()



