import os, sys, subprocess
from io import StringIO
from statistics import median

import pandas as pd
import pytesseract
from PIL import Image as Im
from PIL import ImageDraw
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
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.graphics import Line as KVLine
from kivy.utils import get_color_from_hex

from article import Article, Block, Paragraph, Line
import geometry

# class FileSelect(GridLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.cols = 1
#         self.add_widget(Label(text="Selecione um ficheiro."))
#         self.add_widget(FileChooserIconView(path='.'))

class FileSelectScreen(Screen):
    pass

class ImagePreviewScreen(Screen):
    drawing = BooleanProperty()
    current_mode = StringProperty()
    rectangles_articles = ListProperty()
    rectangles_exclude = ListProperty()

    def on_enter(self, *args):
        self.drawing = False
        self.current_mode = "A"
        self.rectangles_articles = []
        self.rectangles_exclude = []
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
            self.drawing = True
            if self.current_mode == "A":
                rectangles = self.rectangles_articles
                self.canvas.add(Color(rgba=get_color_from_hex("#ffff6666")))
            elif self.current_mode == "E":
                rectangles = self.rectangles_exclude
                self.canvas.add(Color(rgba=get_color_from_hex("#ff666666")))
            r = Rectangle(pos=touch.pos, size=(1,1))
            if self.current_mode == "A" and len(rectangles) > 0 and geometry.point_in_rects((touch.x,touch.y), rectangles[-1]['rects']):
                rectangles[-1]['rects'].append({
                    'rect': r,
                    'original_x': (touch.x - (image.center_x - image.norm_image_size[0] / 2)) * image.texture_size[0] / image.norm_image_size[0],
                    'original_y': (touch.y - (image.center_y - image.norm_image_size[1] / 2)) * image.texture_size[1] / image.norm_image_size[1],
                })
            else:
                if self.current_mode == "A":
                    rectangles.append({
                        'rects': [{
                            'rect': r,
                            'original_x': (touch.x - (image.center_x - image.norm_image_size[0] / 2)) * image.texture_size[0] / image.norm_image_size[0],
                            'original_y': (touch.y - (image.center_y - image.norm_image_size[1] / 2)) * image.texture_size[1] / image.norm_image_size[1],
                        }]
                    })
                else:
                    rectangles.append({
                        'rect': r,
                        'original_x': (touch.x - (image.center_x - image.norm_image_size[0] / 2)) * image.texture_size[0] / image.norm_image_size[0],
                        'original_y': (touch.y - (image.center_y - image.norm_image_size[1] / 2)) * image.texture_size[1] / image.norm_image_size[1],
                    })
            self.canvas.add(r)
        else:
            return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.drawing and self.current_mode == "A":
            r = self.rectangles_articles[-1]
            self.canvas.remove(r['rects'][-1]['rect'])
            if 'line' in r:
                self.canvas.remove(r['line'])

            line = KVLine(points=geometry.calc_line_points(r['rects']), width=1.5)

            self.canvas.add(Color(rgb=get_color_from_hex("#ffff66")))
            self.canvas.add(line)

            r['line'] = line

        self.drawing = False
        if len(self.rectangles_articles) > 0:
            self.ids.undo_article_btn.disabled = False
        if len(self.rectangles_exclude) > 0:
            self.ids.undo_exclude_btn.disabled = False

    def on_touch_move(self, touch):
        if self.drawing:
            if self.current_mode == "A":
                rectangles = self.rectangles_articles[-1]['rects']
            elif self.current_mode == "E":
                rectangles = self.rectangles_exclude
            active_rect = rectangles[-1]
            (x,y) = active_rect['rect'].pos

            min_x = self.ids.image_p.center_x - self.ids.image_p.norm_image_size[0] // 2
            max_x = self.ids.image_p.center_x + self.ids.image_p.norm_image_size[0] // 2
            min_y = self.ids.image_p.center_y - self.ids.image_p.norm_image_size[1] // 2
            max_y = self.ids.image_p.center_y + self.ids.image_p.norm_image_size[1] // 2

            width = (touch.x if min_x <= touch.x <= max_x else (min_x if touch.x < min_x else max_x)) - x
            height = (touch.y if min_y <= touch.y <= max_y else (min_y if touch.y < min_y else max_y)) - y

            active_rect['rect'].size = (width, height)
            active_rect['original_width'] = width * self.ids.image_p.texture_size[0] / self.ids.image_p.norm_image_size[0]
            active_rect['original_height'] = height * self.ids.image_p.texture_size[1] / self.ids.image_p.norm_image_size[1]
        else:
            return super().on_touch_move(touch)

    def on_resize(self, instance, value):

        for r in self.rectangles_exclude + [r for ra in self.rectangles_articles for r in ra['rects']]:
            r['rect'].pos = (r['original_x'] * instance.norm_image_size[0] / instance.texture_size[0] + (instance.center_x - instance.norm_image_size[0] / 2),
                            r['original_y'] * instance.norm_image_size[1] / instance.texture_size[1] + (instance.center_y - instance.norm_image_size[1] / 2))

            r['rect'].size = (r['original_width'] * instance.norm_image_size[0] / instance.texture_size[0],
                              r['original_height'] * instance.norm_image_size[1] / instance.texture_size[1])

        for r in self.rectangles_articles:
            self.canvas.remove(r['line'])

            r['line'] = KVLine(points=geometry.calc_line_points(r['rects']), width=1.5)
            self.canvas.add(Color(rgb=get_color_from_hex("#ffff66")))
            self.canvas.add(r['line'])

    def undo_selection(self, btn, mode):
        if mode == 'A':
            rectangles = self.rectangles_articles
        elif mode == 'E':
            rectangles = self.rectangles_exclude
        if len(rectangles) > 0:
            r = rectangles.pop(-1)
            #self.canvas.remove(r['rect'])
            self.canvas.remove(r.get('line', r.get('rect')))
        if len(rectangles) == 0:
            btn.disabled = True

    def submit_image(self):
        get_left = lambda r: r['original_x'] if r['original_width'] > 0 else r['original_x'] + r['original_width']
        get_right = lambda r: r['original_x'] if r['original_width'] < 0 else r['original_x'] + r['original_width']
        get_top = lambda r, h: h - r['original_y'] if r['original_height'] < 0 else h - (r['original_y'] + r['original_height'])
        get_bottom = lambda r, h: h - r['original_y'] if r['original_height'] > 0 else h - (r['original_y'] + r['original_height'])

        im = Im.open(self.manager.image_source)
        if len(self.rectangles_exclude) > 0:
            draw = ImageDraw.Draw(im)
            for r in self.rectangles_exclude:
                left = get_left(r)
                right = get_right(r)
                top = get_top(r, im.height)
                bottom = get_bottom(r, im.height)
                draw.rectangle([left,top,right,bottom], fill="black")
        if len(self.rectangles_articles) > 0:
            for r in self.rectangles_articles:
                if len(r['rects']) == 1:
                    r = r['rects'][0]
                    left = get_left(r)
                    right = get_right(r)
                    top = get_top(r, im.height)
                    bottom = get_bottom(r, im.height)
                    self.manager.article_images.append(im.crop((left,top,right,bottom)))
                else:
                    mask = Im.new("RGBA", size=im.size)
                    mask_draw = ImageDraw.Draw(mask)
                    for rect in r['rects']:
                        ps = geometry.get_rect(rect)
                        mask_draw.rectangle(ps, fill="#fff")
                    mask = mask.transpose(Im.Transpose.FLIP_TOP_BOTTOM)
                    blank = Im.new("RGB", size=im.size)
                    self.manager.article_images.append(Im.composite(im, blank, mask))
        else:
            self.manager.article_images.append(im)
        self.manager.current = 'article_preview'

class ArticlePreviewScreen(Screen):

    def on_enter(self, *args):
        for im in self.manager.article_images:
            a = Article(im)
            self.manager.articles.append(a)
            # ti = MyTextInput(text=str(a))
            ti = MyLabel(text=str(a))
            self.ids.articles.add_widget(ti)
            sep = Widget(height=200, size_hint=(1,None))
            self.ids.articles.add_widget(sep)
        self.ids.processing_text.opacity = 0
        # self.manager.current = 'save'
        return super().on_enter(*args)

class SaveScreen(Screen):
    def save(self, filepath, filename):
        file = os.path.join(filepath, filename + ".md")
        with open(file, "w", encoding='UTF-8') as f:
            for article in self.manager.articles:
                f.write(str(article) + "\n\n---\n\n")
        if sys.platform == "win32":
            os.startfile(file)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, file])
        OCRApp.get_running_app().stop()

class MyScreenManager(ScreenManager):
    image_source = StringProperty()
    article_images = ListProperty()
    articles = ListProperty()

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
        sm.add_widget(SaveScreen(name='save'))
        return sm

if __name__ == '__main__':
    if len(sys.argv) == 1:
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