from bs4 import BeautifulSoup
from xml.sax import saxutils
import sys

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
                    break
            else:
                print ("we see:", operation["method"])
                raise javaxml_exception("unrecognized dict operation")

    elif object_["class"] == "java.awt.Color":
        current_object = {}
        current_object["id"] = object_['id']

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

width = soup.Book["width"]
height = soup.Book["height"]

print (width, height)

for pageno, page in enumerate(pagesList):
    print ("Processing page %d (%s):" % (pageno,page))
    items = soup.find_all(parentId=page)
    for item in items:
        print (item.name)
        print (item["re"])

        if item.name == "ImageContent":
            if (item.has_attr("content")):
                print ("%s.original" % item["content"])

        elif item.name == "TextContent":
            textxml = (list(item.dm.children)[0])

            textsoup = BeautifulSoup(textxml, "lxml-xml")

            for object_ in textsoup.java.contents:
                if object_ != "\n" and object_.name == "object":
                    text_data = javaxml_to_python(object_)
                    print(text_data)



            

