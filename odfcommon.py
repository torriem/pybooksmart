import ezodf
import PIL.Image
import io
import os

class ODFImageObject(ezodf.filemanager.FileObject):

    def __init__(self, odf_object, filename, format_):
        name = os.path.basename(filename)
        #print (name)
        super(ODFImageObject, self).__init__(name, None)
        self.image_filename = filename
        self.cropped = False
        self.format = format_
        odf_object.filemanager.register('Pictures/%s' % os.path.basename(filename),
                                        self, 'image/%s' % format_)

    def crop(self, left, top, right, bottom):
        image = PIL.Image.open(self.image_filename)
        area = (left, top, image.width - right, height - bottom)
        self.cropped_image = image.crop(area)
        self.cropped = True

    def tobytes(self):
        if self.cropped:
            self.jpeg_array = io.BytesIO()
            self.cropped_image.save(jpeg_array, format = self.format)
            return self.jpeg_array.getvalue()

        imagefile = open(self.image_filename, 'rb')
        return imagefile.read()


