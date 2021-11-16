import lxml.etree
import pprint

class TextBox(object):
    def __init__(self, xmlre = None):
        if xmlre:
            self.x, self.y, self.width, self.height = [ int(i) for i in xmlre.split(',') ]
        else:
            self.x = 0
            self.y = 0
            self.width = 0
            self.height = 0

        self.paragraphs = []

    def __repr__(self):
        return ('TextBox(%d,%d,%d,%d,%s)' % (self.x, self.y, self.width, self.height, repr(self.paragraphs)))

    def __str__(self):
        return repr(self)

class ImageBox(object):
    pass

class ParagraphStyle(object):
    def __init__(self, style_dict = None):
        self.name = None

        if style_dict:
            self.font      = style_dict['font']
            self.size      = style_dict['size']
            self.color     = style_dict['color']
            self.alignment = style_dict['align']
            self.bold      = style_dict['bold']
            self.italic    = style_dict['italic']
        else:
            self.font      = None
            self.size      = None
            self.color     = None
            self.alignment = None
            self.bold      = None
            self.italic    = None

    def __str__(self):
        return "name=%s, font=%s, size=%s, color=%s, alignment=%d, bold=%s, italic=%s" % (
             self.name, self.font, self.size, self.color, self.alignment, self.bold, self.italic)

    def __repr__(self):
        return "Paragraph Style {name:%s, font:%s, size:%s, color:%s, alignment:%d, bold:%s, italic:%s}" % (
                self.name, self.font, self.size, self.color, self.alignment, self.bold, self.italic)

    def __setitem__(self, name, value):
        if name in ['font', 'size', 'color', 'alignment', 'bold', 'italic']:
            self.__dict__[name] = value
        else:
            raise KeyError

    def __getitem__(self, name):
        if name in ['font', 'size', 'color', 'alignment', 'bold', 'italic']:
            return self.__dict__[name]
        else:
            raise KeyError

    def simple_serialize(self):
        s = '%s|%s|%s|%d|%s|%s' % (self.font,
                                   self.size,
                                   self.color,
                                   self.alignment,
                                   self.bold,
                                   self.italic)

        return s

class Paragraph(object):
    def __init__(self):
        self.style = None # a string name referring to a style
        self.spans = [] # list of Span objects

    def __repr__(self):
        return 'Paragraph(%s, %s)' % (self.style, repr(self.spans))

    def __str__(self):
        return repr(self)
    
class Span(object):
    def __init__(self):
        self.style = None # string name of span style
        self.text = None
        self.variable = None

    def __repr__(self):
        return 'Span(%s, "%s", %s)' % (self.style, self.text, self.variable)

    def __str(self):
        return repr(self)

class SpanStyle(object):
    def __init__(self, style_dict = None):
        self.name = None

        if style_dict:
            self.font = style_dict.get('font', None)
            self.size = style_dict.get('size', None)
            self.color = style_dict.get('color', None)
            self.bold = style_dict.get('bold', None)
            self.italic = style_dict.get('italic', None)
            #self.variable = style_dict.get('variable', None)
        else:
            self.font = None
            self.size = None
            self.color = None
            self.bold = None
            self.italic = None
            #self.variable = None

    def simple_serialize(self):
        s = '%s|%s|%s|%s|%s' % (self.font,
                                   self.size,
                                   self.color,
                                   self.bold,
                                   self.italic)

        return s

    def __str__(self):
        return "name=%s, font=%s, size=%s, color=%s, bold=%s, italic=%s" % (
             self.name, self.font, self.size, self.color, self.bold, self.italic)

    def __repr__(self):
        return "Span Style {name:%s, font:%s, size:%s, color:%s, bold:%s, italic:%s}" % (
                self.name, self.font, self.size, self.color, self.bold, self.italic)

    def __setitem__(self, name, value):
        if name in ['font', 'size', 'color', 'bold', 'italic']:
            self.__dict__[name] = value
        else:
            raise KeyError

    def __getitem__(self, name):
        if name in ['font', 'size', 'color', 'bold', 'italic']:
            return self.__dict__[name]
        else:
            raise KeyError


class javaxml_exception(Exception):
    pass

def javaxml_to_python(object_):
    current_object = None
    if object_.attrib["class"] == "java.util.LinkedList":
        #print ("Creating a new list")
        current_object = []

        for operation in object_: # list contents
            #print ("operation is: ", operation.name, operation["method"])
            if operation.attrib["method"] == "add": # object, method = add
                #print ("adding to list:")
                for to_add in operation: # what will we add?
                    if to_add.tag == "object": 
                        current_object.append(javaxml_to_python(to_add))
                    elif to_add.tag == "string":
                        #print ("added string")
                        current_object.append(to_add.text)
                    elif to_add.tag == "null":
                        #print ("added null")
                        current_object.append(None)
                    else:
                        print ("we got: ",to_add.name)
                        print (operation)
                        raise javaxml_exception("unrecognized list item")
            else:
                print ("we see:", operation["method"])
                raise javaxml_exception("unrecognized list operation")


    elif object_.attrib["class"] == "java.util.HashMap":
        #print ("Creating a new dict")
        current_object = {}
        for operation in object_: # dict contents
            #print ("operation is: ", operation.name, operation["method"])
            if operation.attrib["method"] == "put": # object, method = put
                #print ("adding to dict:")

                # First will always be a string key, second will be a value
                key = None
                for to_add in operation: # what will we add?
                    if not key: 
                        key = to_add.text
                        continue

                    if to_add.tag == "object":

                        if 'class' in to_add.attrib:
                            current_object[key] = javaxml_to_python(to_add)

                        elif 'udref' in to_add.attrib:
                            current_object[key] = to_add.attrib["idref"]

                    elif to_add.tag == "string":
                        current_object[key] = (to_add.text)
                    elif to_add.tag == "null":
                        current_object[key] = None
                    elif to_add.tag == "int":
                        current_object[key] = int(to_add.text)
                    elif to_add.tag == "boolean":
                        current_object[key] = to_add.text #TODO convert to real boolean
                    else:
                        print ("we got: ",to_add.name)
                        print (operation)
                        raise javaxml_exception("unrecognized dict value")
                    break # we only expect two xml elements in a hashmap, and we now have both
            else:
                print ("we see:", operation["method"])
                raise javaxml_exception("unrecognized dict operation")

    elif object_.attrib["class"] == "java.awt.Color":
        current_object = {}
        if 'id' in object_.attrib:
            current_object["color_id"] = object_.attrib['id']

        red = None
        green = None
        blue = None
        alpha = None

        for i in object_:
            if red is None:
                red = int(i.text)
            elif green is None:
                green = int(i.text)
            elif blue is None:
                blue = int(i.text)
            elif alpha is None:
                alpha = int(i.text)
    
        current_object['color'] = (red, green, blue, alpha) 
    else:
        print ("Unknown object: ", _object["class"])
        raise javaxml_exception("unimplemented object class %s" % _object["class"])


    return current_object
       

class BookXML(object):

    def __init__(self, book_file):
        tree = lxml.etree.parse(open(book_file, 'r'))
        self.book = tree.getroot()


        self.pages = []
        self.page_info = {}
        self.text_boxes = {}
        self.images = {}
        self.paragraph_styles = []
        self.span_styles = []

        self._styles = {}  # BookSmart TextStyleDefinitions
        self._color_cache = {} # BookSmart color definitions
        self._paragraph_style_cache = {}
        self._pgs_no = 0
        self._span_style_cache = {}
        self._ss_no = 0

        self.read_book_styles()
        self.read_pages()
        print(self._paragraph_style_cache)
        print(self._span_style_cache)
        print(self.text_boxes)

        

    def read_book_styles(self):
        style_defs = self.book.findall('TextStyleDefinition')

        for s in style_defs:
            sid = s.attrib['id'].lower()
            self._styles[sid] = { 'align': 0,
                                  'bold' : False,
                                  'italic' : False }
            for key in s.attrib:
                if key in ['font', 'size']:
                    self._styles[sid][key] = s.attrib[key]
                if key == 'color':
                    self._styles[sid][key] = '#%s' % s.attrib[key][-6:]
                if key == 'align':
                    self._styles[sid][key] = int(s.attrib[key])

                if key == 'italic':
                    if s.attrib[key] == 'true':
                        self._styles[sid][key] = True
                    else:
                        self._styles[sid][key] = False
                   
                if key == 'bold':
                    if s.attrib[key] == 'true':
                        self._styles[sid][key] = True
                    else:
                        self._styles[sid][key] = False

    def read_pages(self):
        pagesList = self.book.find('pagesList')
        self.book_objects = self.book.find('bookObjects')

        pagesList = [ pagesList[2]]
        for page in pagesList:
            id_ = page.attrib['id']
            self.pages.append(id_)
            self.page_info[id_] = self.book_objects.findall("Page[@id='%s']" % id_)[0].attrib

            self.text_boxes[id_] = []
            for tc in self.book_objects.findall("TextContent[@parentId='%s']" % id_):
                text_box = TextBox(tc.attrib['re'])

                base_style = {} # this will hold the default style going into the parsing
                lookup_style = self._styles[tc.attrib['ts'].lower()]
                for key in lookup_style:
                    base_style[key] = lookup_style[key]

                base_style['color'] = '#%s' % base_style['color'][-6:] # trim off alpha channel

                #text is a serialized structure of java objects stored in the dm tag
                #TODO put this in some kind of Python class structure so it's easier to
                #process.  Probably we need paragraph and span objects
                dmtext = tc[0].text.encode('utf-8')
                dmobj = lxml.etree.fromstring(dmtext)[0] # get the first child of the java node
                text_structure = javaxml_to_python(dmobj)


                pstyle = None
                paragraph = None

                for i in text_structure:
                    if isinstance(i, dict):
                        # a pgraph style dict signifies the start of a new paragraph

                        if pstyle:

                            # paragraph was open, close it now, append it to the
                            # list we're building.  If it was empty we can just
                            # throw it away.

                            if len(paragraph.spans):
                                if not pstyle.simple_serialize() in self._paragraph_style_cache:
                                    pstyle.name = 'PS%d' % self._pgs_no
                                    self._pgs_no += 1

                                    self._paragraph_style_cache[pstyle.simple_serialize()] = pstyle
                                else:
                                    pstyle = self._paragraph_style_cache[pstyle.simple_serialize()]
                                paragraph.style = pstyle.name

                                text_box.paragraphs.append(paragraph)
                                # append to list

                        paragraph = Paragraph()
                        pstyle = ParagraphStyle(base_style)

                        if 'resolver' in i:
                            # override our default style for this paragraph 
                            lookup_style = self._styles[i['resolver'].split('.')[0].lower()]

                            for key in lookup_style:
                                if key == 'align': pstyle['alignment'] = lookup_style[key]
                                elif key != 'id':
                                    pstyle[key] = lookup_style[key]

                        if 'Alignment' in i:
                            pstyle['alignment'] = int(i['Alignment'])

                        continue
                    
                    spans_wrapper = (sp for sp in i) # list of items
                    span_style = SpanStyle
                    text_span = Span()

                    for span in spans_wrapper:
                        if isinstance(span, dict):
                            # style the span
                            span_style = SpanStyle()

                            if 'size' in span:
                                span_style['size'] = span['size']
                            if 'family' in span:
                                span_style['font'] = span['family']
                            if 'foreground' in span:
                                if isinstance(span['foreground'], str):
                                    # if just a color-id, look it up
                                    color = self._color_cache[span['foreground']]
                                else:
                                    # otherwise parse it, save it in cache
                                    color = span['foreground']['color']

                                    if 'color_id' in span['foreground']:
                                        self._color_cache[span['foreground']['color_id']] = color

                                color_hex = '#%x02%x02%x02' % ( color[0], color[1], color[2] )
                                span_style['color'] = colorhex
                            if 'bold' in span:
                                if span['bold'].lower() == 'true':
                                    span_style['bold'] = True
                                else:
                                    span_style['bold'] = False
                            else:
                                span_style['bold'] = False

                            if 'italic' in span:
                                if span['italic'].lower() == 'true':
                                    span_style['italic'] = True
                                else:
                                    span_style['italic'] = False
                            else:
                                span_style['italic'] = False

                            if 'bsVar' in span:
                                text_span.variable = span['bsVar']

                            # now get the text that follows
                            span = next(spans_wrapper)
                        
                        if span and span.strip():

                            if not span_style.simple_serialize() in self._span_style_cache:
                                span_style.name = 'SS%d' % self._ss_no
                                self._ss_no += 1
                                
                                self._span_style_cache[span_style.simple_serialize()] = span_style
                            else:
                                span_style = self._span_style_cache[span_style.simple_serialize()]
                            text_span.text = span
                            text_span.style = span_style.name

                            paragraph.spans.append( text_span )
                # if the paragraph is empty, we should throw it away.

                if len(paragraph.spans):
                    if not pstyle.simple_serialize() in self._paragraph_style_cache:
                        pstyle.name = 'PS%d' % self._pgs_no
                        self._pgs_no += 1
                        self._paragraph_style_cache[pstyle.simple_serialize()] = pstyle
                    else:
                        pstyle = self._paragraph_style_cache[pstyle.simple_serialize()]

                    paragraph.style = pstyle.name
                    text_box.paragraphs.append(paragraph)
                self.text_boxes[id_].append(text_box)

            self.images[id_] = []
            for ic in self.book_objects.findall("ImageContent[@parentId='%s']" % id_):
                imagebox = {}
                for key in ic.attrib:
                    imagebox[key] = ic.attrib[key]

                imagebox['transformations'] = []

                if len(ic.getchildren()):
                    for transform in ic[0]:
                        imagebox['transformations'].append(transform.attrib)

                self.images[id_].append(imagebox)
                

    def page_ids(self):
        return self.page_ids

    def page_info(self):
        pass

if __name__ == "__main__":
    book = BookXML('/home/torriem/booksmart/BookSmartData/isreal and jerusalem/isreal and jerusalem.book')

    import pprint
    #pprint.pprint (book.text_boxes['8df464d8-7216-4972-8f0d-56ac7e918e48'])
    #pprint.pprint (book.images)




