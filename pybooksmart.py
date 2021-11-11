from bs4 import BeautifulSoup
from xml.sax import saxutils
import ezodf

import sys

from ezodf.const import ALL_NSMAP
from lxml.etree import QName, Element

#from imagefile import ImageObject

def ns(combined_name):
    prefix,name = combined_name.split(':')
    return "{%s}%s" % (ALL_NSMAP[prefix], name)

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
                            



bsf = open(sys.argv[1],"r") #assume utf-8

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
style_graphic_properties.attrib[ns('style:vertical-pos')] = 'center'
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


#style for drawing boxes (temporary)
style_style = Element(ns('style:style'))
style_style.attrib[ns('style:family')] = 'graphic'
style_style.attrib[ns('style:name')] = 'blurbboxstyle'
style_style.attrib[ns('style:parent-style-name')] = 'Frame'

graphic_properties = Element(ns('style:graphic-properties'))
#graphic_properties.attrib[ns('fo:border')] = '1pt solid #000000'
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
    if pageno > 0:
        # insert a page break
        
        # Add a new page break paragraph to the body
        paragraph = Element(ns('text:p'))
        paragraph.attrib[ns('text:style-name')] = 'BlurbPageBreak1'

        doc.body.xmlnode.append(paragraph)
         
    paragraph = Element(ns('text:p'))
    paragraph.text='Page %d' % pageno

    doc.body.xmlnode.append(paragraph)


    page_info = soup.find("Page", id=page)

    print (page_info.attrs)

    items = soup.find_all(parentId=page)

    for item in items:

        # get x,y, width, height coords
        coord = [int(x) for x in item['re'].split(',')]

        print (coord)
        print ([x / 72.0 for x in coord])


        draw_frame = Element(ns('draw:frame'))
        draw_frame.attrib[ns('draw:name')] = 'Frame%d' % (frame_count)
        draw_frame.attrib[ns('draw:style-name')] = 'blurbboxstyle'
        draw_frame.attrib[ns('svg:width')] = '%dpt' % coord[2]
        #draw_frame.attrib[ns('svg:height')] = '%dpt' % coord[3]
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
                    a = ImageObject('Pictures/%s.jpg' % booksmart_image, 
                                    'library/%s.original' % booksmart_image)

                    doc.filemanager.directory[booksmart_image] = a
                print ("%s.original" % item["content"])

                transformations = item.find_all("TransformEffect")
                x = int(transformations[0]['x'])
                y = int(transformations[0]['y'])
                zoom = int(transformations[0]['zoom'])

                # enlarge image dimensions by zoom.

                # if x is negative, crop on the left, set x to 0
                # if y is negative, crop on the top, set y to 0
                # if (image.width - left crop) > coord[2], crop on the right
                # if (image.height - top crop) > coord[3], crop on the bottom

                # place image at x,y.
                # set display width and height

                draw_text_box = Element(ns('draw:text-box'))
                draw_text_box.attrib[ns('fo:min-height')] = '%dpt' % coord[3]
                draw_frame.append(draw_text_box)



        elif item.name == "TextContent":
            textxml = (list(item.dm.children)[0])

            textsoup = BeautifulSoup(textxml, "lxml-xml")
            
            draw_text_box = Element(ns('draw:text-box'))
            draw_text_box.attrib[ns('fo:min-height')] = '%dpt' % coord[3]
            draw_frame.append(draw_text_box)

            for object_ in textsoup.java.contents:
                if object_ != "\n" and object_.name == "object":
                    text_data = javaxml_to_python(object_)
                    print(text_data)

            paragraph = Element(ns('text:p'))
            paragraph.text='hi'
            draw_text_box.append(paragraph)

        
    #break
            

doc.save()



