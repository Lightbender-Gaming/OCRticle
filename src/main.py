# from PIL import Image
from sys import argv
from io import StringIO
from statistics import median

import pandas as pd
import pytesseract
from PIL import Image as Im
import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.utils import get_color_from_hex

from article import Article, Block, Paragraph, Line

# class FileSelect(GridLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.cols = 1
#         self.add_widget(Label(text="Selecione um ficheiro."))
#         self.add_widget(FileChooserIconView(path='.'))

class FileSelectScreen(Screen):
    pass

class ImagePreviewScreen(Screen):
    drawing_mode = BooleanProperty()
    rectangles = ListProperty()

    def on_enter(self, *args):
        self.drawing_mode = False
        self.ids.image_p.source = self.manager.image_source
        self.ids.image_p.opacity = 1
        self.ids.image_p.reload()
        self.ids.image_p.bind(size=self.on_resize)
        return super().on_enter(*args)

    def on_touch_down(self, touch):
        image = self.ids.image_p

        min_x = image.center_x - image.norm_image_size[0] // 2
        max_x = image.center_x + image.norm_image_size[0] // 2
        min_y = image.center_y - image.norm_image_size[1] // 2
        max_y = image.center_y + image.norm_image_size[1] // 2

        if min_x <= touch.x <= max_x and min_y <= touch.y <= max_y:
            self.drawing_mode = True
            r = Rectangle(pos=touch.pos, size=(1,1))
            self.rectangles.append({
                'rect': r,
                'original_x': (touch.x - (image.center_x - image.norm_image_size[0] / 2)) * image.texture_size[0] / image.norm_image_size[0],
                'original_y': (touch.y - (image.center_y - image.norm_image_size[1] / 2)) * image.texture_size[1] / image.norm_image_size[1],
            })
            self.canvas.add(Color(rgba=get_color_from_hex("#ffff6666")))
            self.canvas.add(r)
        else:
            return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.drawing_mode = False
        if len(self.rectangles) > 0:
            self.ids.undo_btn.disabled = False

    def on_touch_move(self, touch):
        if self.drawing_mode:
            r = self.rectangles[-1]
            (x,y) = r['rect'].pos

            min_x = self.ids.image_p.center_x - self.ids.image_p.norm_image_size[0] // 2
            max_x = self.ids.image_p.center_x + self.ids.image_p.norm_image_size[0] // 2
            min_y = self.ids.image_p.center_y - self.ids.image_p.norm_image_size[1] // 2
            max_y = self.ids.image_p.center_y + self.ids.image_p.norm_image_size[1] // 2

            width = (touch.x if min_x <= touch.x <= max_x else (min_x if touch.x < min_x else max_x)) - x
            height = (touch.y if min_y <= touch.y <= max_y else (min_y if touch.y < min_y else max_y)) - y

            r['rect'].size = (width, height)
            r['original_width'] = width * self.ids.image_p.texture_size[0] / self.ids.image_p.norm_image_size[0]
            r['original_height'] = height * self.ids.image_p.texture_size[1] / self.ids.image_p.norm_image_size[1]
        else:
            return super().on_touch_move(touch)

    def on_resize(self, instance, value):

        for r in self.rectangles:
            r['rect'].pos = (r['original_x'] * instance.norm_image_size[0] / instance.texture_size[0] + (instance.center_x - instance.norm_image_size[0] / 2),
                            r['original_y'] * instance.norm_image_size[1] / instance.texture_size[1] + (instance.center_y - instance.norm_image_size[1] / 2))

            r['rect'].size = (r['original_width'] * instance.norm_image_size[0] / instance.texture_size[0],
                              r['original_height'] * instance.norm_image_size[1] / instance.texture_size[1])

    def undo_selection(self, btn):
        if len(self.rectangles) > 0:
            r = self.rectangles.pop(-1)
            self.canvas.remove(r['rect'])
        if len(self.rectangles) == 0:
            btn.disabled = True

    def submit_image(self):
        im = Im.open(self.manager.image_source)
        if len(self.rectangles) > 0:
            for r in self.rectangles:
                left = r['original_x'] if r['original_width'] > 0 else r['original_x'] + r['original_width']
                right = r['original_x'] if r['original_width'] < 0 else r['original_x'] + r['original_width']
                top = im.height - r['original_y'] if r['original_height'] < 0 else im.height - (r['original_y'] + r['original_height'])
                bottom = im.height - r['original_y'] if r['original_height'] > 0 else im.height - (r['original_y'] + r['original_height'])
                self.manager.article_images.append(im.crop((left,top,right,bottom)))
        else:
            self.manager.article_images.append(im)
        self.manager.current = 'article_preview'

class ArticlePreviewScreen(Screen):

    def on_enter(self, *args):
        for im in self.manager.article_images:
            a = Article(im)
            # ti = MyTextInput(text=str(a))
            ti = MyLabel(text=str(a))
            self.ids.articles.add_widget(ti)
            sep = Widget(height=200, size_hint=(1,None))
            self.ids.articles.add_widget(sep)
        self.ids.processing_text.opacity = 0
        return super().on_enter(*args)

class MyScreenManager(ScreenManager):
    image_source = StringProperty()
    article_images = ListProperty()

    def load_image(self, selection):
        self.image_source = selection[0]
        # print(*(str(b) for b in generate_ir(selection[0])), sep='\n---\n')
        # print(generate_ir(selection))

class MyTextInput(TextInput):
    pass

class MyLabel(Label):
    pass

class OCRApp(App):

    def build(self):
        sm = MyScreenManager()

        sm.add_widget(FileSelectScreen(name='file_select'))
        sm.add_widget(ImagePreviewScreen(name='image_preview'))
        sm.add_widget(ArticlePreviewScreen(name='article_preview'))
        return sm

if __name__ == '__main__':
    if len(argv) == 1:
        OCRApp().run()
    else:
        pass
        




        # def insert_range(size, ranges):
        #     new_ranges = []
        #     inserted = False
        #     for (mn,mx) in ranges:
        #         if size >= mn and size <= mx:
        #             new_ranges.append((min(mn,size-3),max(mx,size+3)))
        #             inserted = True
        #         else:
        #             new_ranges.append((mn,mx))
        #     if not inserted:
        #         new_ranges.append((size-3,size+3))
        #     return new_ranges

        # ranges = []
        # for _, size in blocks:
        #     ranges = insert_range(size, ranges)