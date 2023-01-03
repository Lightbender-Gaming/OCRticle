import os, sys, subprocess
from functools import partial
from io import BytesIO

from PIL import Image, ImageDraw, ImageEnhance

from ocrticle.article import Article, BlockType
import ocrticle.geometry

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.dropdown import DropDown
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as kiImage
from kivy.properties import StringProperty,\
    BooleanProperty,\
    ListProperty,\
    NumericProperty,\
    ObjectProperty,\
    DictProperty
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.graphics.texture import Texture
from kivy.utils import get_color_from_hex
from kivy.metrics import sp

class FileSelectScreen(Screen):
    pass

class ImagePreviewScreen(Screen):
    drawing = BooleanProperty()
    current_mode = StringProperty()
    rectangles_articles = ListProperty()
    rectangles_exclude = ListProperty()
    image_attributes = DictProperty()
    original_image = ObjectProperty()

    def show_image(self):
        data = BytesIO()
        i = ImageEnhance.Brightness(self.preview).enhance(self.ids.brightness_slider.value / 100)
        i = ImageEnhance.Contrast(i).enhance(self.ids.contrast_slider.value / 100)
        ImageEnhance.Color(i).enhance(self.ids.saturation_slider.value / 100).save(data, format="PNG")
        data.seek(0)
        img = CoreImage(BytesIO(data.read()), ext="png")
        self.ids.image_p.texture = img.texture
        self.ids.image_p.reload

    def on_enter(self, *args):
        self.manager.article_images = []
        self.ids.undo_article_btn.disabled = True
        self.ids.undo_exclude_btn.disabled = True
        self.drawing = False
        self.current_mode = "A"
        self.rectangles_articles = []
        self.rectangles_exclude = []
        self.original_image = Image.open(self.manager.image_source)
        self.preview = self.original_image.copy()
        self.preview.thumbnail((1200, 1200))
        self.show_image()
        self.ids.image_p.opacity = 1
        self.ids.image_p.bind(size=self.on_resize)
        return super().on_enter(*args)

    def on_leave(self, *args):
        for r in self.rectangles_articles:
            for rr in r:
                self.canvas.remove(rr['rect'])
        for r in self.rectangles_exclude:
            self.canvas.remove(r['rect'])
        return super().on_leave(*args)

    def on_touch_down(self, touch):
        image = self.original_image
        image_p = self.ids.image_p

        min_x = image_p.center_x - image_p.norm_image_size[0] / 2
        max_x = image_p.center_x + image_p.norm_image_size[0] / 2
        min_y = image_p.center_y - image_p.norm_image_size[1] / 2
        max_y = image_p.center_y + image_p.norm_image_size[1] / 2

        if min_x <= touch.x <= max_x and min_y <= touch.y <= max_y:
            self.drawing = True
            if self.current_mode == "A":
                rectangles = self.rectangles_articles
                self.canvas.add(Color(rgba=get_color_from_hex("#ffff6666")))
            elif self.current_mode == "E":
                rectangles = self.rectangles_exclude
                self.canvas.add(Color(rgba=get_color_from_hex("#ff666666")))
            r_canvas = Rectangle(pos=touch.pos, size=(1,1))
            new_r = {
                'rect': r_canvas,
                'original_x': (touch.x - min_x) * image.width / image_p.norm_image_size[0],
                'original_y': (touch.y - min_y) * image.height / image_p.norm_image_size[1],
            }
            if self.current_mode == "A" and len(rectangles) > 0 and geometry.point_in_rects((touch.x,touch.y), rectangles[-1]):
                rectangles[-1].append(new_r)
            elif self.current_mode == "A":
                rectangles.append([new_r])
            else:
                rectangles.append(new_r)
            self.canvas.add(r_canvas)
        else:
            return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.drawing and self.current_mode == "A" and len(rr := self.rectangles_articles[-1]) > 1:
            new_rect = rr.pop(-1)
            self.canvas.remove(new_rect['rect'])
            new_rects = geometry.parse_rect(new_rect, rr, self.ids.image_p)
            for r in new_rects:
                self.canvas.add(r['rect'])

            rr.extend(new_rects)
        self.drawing = False
        if len(self.rectangles_articles) > 0:
            self.ids.undo_article_btn.disabled = False
        if len(self.rectangles_exclude) > 0:
            self.ids.undo_exclude_btn.disabled = False

    def on_touch_move(self, touch):
        if self.drawing:
            if self.current_mode == "A":
                rectangles = self.rectangles_articles[-1]
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
            active_rect['original_width'] = width * self.original_image.width / self.ids.image_p.norm_image_size[0]
            active_rect['original_height'] = height * self.original_image.height / self.ids.image_p.norm_image_size[1]
        else:
            return super().on_touch_move(touch)

    def on_resize(self, instance, value):

        for r in self.rectangles_exclude + [r for ra in self.rectangles_articles for r in ra]:
            r['rect'].pos = (r['original_x'] * instance.norm_image_size[0] / self.original_image.width + (instance.center_x - instance.norm_image_size[0] / 2),
                            r['original_y'] * instance.norm_image_size[1] / self.original_image.height + (instance.center_y - instance.norm_image_size[1] / 2))

            r['rect'].size = (r['original_width'] * instance.norm_image_size[0] / self.original_image.width,
                              r['original_height'] * instance.norm_image_size[1] / self.original_image.height)

    def undo_selection(self, btn, mode):
        if mode == 'A':
            rectangles = self.rectangles_articles
        elif mode == 'E':
            rectangles = self.rectangles_exclude
        if len(rectangles) > 0:
            r = rectangles.pop(-1)

            if mode == 'A':
                for rect in r:
                    self.canvas.remove(rect['rect'])
            else:
                self.canvas.remove(r['rect'])
        if len(rectangles) == 0:
            btn.disabled = True

    def submit_image(self):
        get_left = lambda r: r['original_x'] if r['original_width'] > 0 else r['original_x'] + r['original_width']
        get_right = lambda r: r['original_x'] if r['original_width'] < 0 else r['original_x'] + r['original_width']
        get_top = lambda r, h: h - r['original_y'] if r['original_height'] < 0 else h - (r['original_y'] + r['original_height'])
        get_bottom = lambda r, h: h - r['original_y'] if r['original_height'] > 0 else h - (r['original_y'] + r['original_height'])

        im = self.original_image
        im = ImageEnhance.Brightness(im).enhance(self.ids.brightness_slider.value / 100)
        im = ImageEnhance.Contrast(im).enhance(self.ids.contrast_slider.value / 100)
        im = ImageEnhance.Color(im).enhance(self.ids.saturation_slider.value / 100)
        thmb = im.copy()
        thmb.thumbnail((600,600))
        freqs = dict()
        for h in range(thmb.height):
            for w in range(thmb.width):
                c = thmb.getpixel((w,h))
                cf = freqs.setdefault(c, 0)
                freqs[c] = cf + 1
        most_common, _ = max(freqs.items(), key= lambda i: i[1])
        if len(self.rectangles_exclude) > 0:
            draw = ImageDraw.Draw(im)
            for r in self.rectangles_exclude:
                left = get_left(r)
                right = get_right(r)
                top = get_top(r, im.height)
                bottom = get_bottom(r, im.height)
                draw.rectangle([left,top,right,bottom], fill=most_common)
        if len(self.rectangles_articles) > 0:
            for r in self.rectangles_articles:
                if len(r) == 1:
                    r = r[0]
                    left = get_left(r)
                    right = get_right(r)
                    top = get_top(r, im.height)
                    bottom = get_bottom(r, im.height)
                    self.manager.article_images.append(im.crop((left,top,right,bottom)))
                else:
                    mask = Image.new("RGBA", size=im.size)
                    mask_draw = ImageDraw.Draw(mask)
                    min_left = None
                    max_right = None
                    min_top = None
                    max_bottom = None
                    for rect in r:
                        min_left = min(get_left(rect), min_left or get_left(rect))
                        max_right = max(get_right(rect), max_right or get_right(rect))
                        min_top = min(get_top(rect, im.height), min_top or get_top(rect, im.height))
                        max_bottom = max(get_bottom(rect, im.height), max_bottom or get_bottom(rect, im.height))
                        ps = geometry.get_original_rect(rect)
                        mask_draw.rectangle(ps, fill="#fff")
                    mask = mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    blank = Image.new("RGB", color=most_common, size=im.size)
                    final_image = Image.composite(im, blank, mask).crop((min_left, min_top, max_right, max_bottom))
                    # final_image.show()
                    self.manager.article_images.append(final_image)
        else:
            self.manager.article_images.append(im)
        self.manager.processed = False
        self.manager.current = 'article_preview'

class ArticlePreviewScreen(Screen):

    def on_enter(self, *args):
        if not self.manager.processed:
            self.ids.articles.clear_widgets()
            self.manager.articles = []
            for im in self.manager.article_images:
                a = Article(im)
                self.manager.articles.append(a)
            self.refresh_articles()
            self.ids.processing_text.opacity = 0
            self.manager.processed = True
        return super().on_enter(*args)

    def on_leave(self, *args):
        self.ids.processing_text.opacity = 1
        self.manager.keep_line_breaks = self.ids.line_breaks_cb.active
        return super().on_leave(*args)

    def refresh_articles(self):
        self.ids.articles.clear_widgets()
        for a in self.manager.articles:
            aw = ArticleWidget()
            aw.add_article(a, self.ids.line_breaks_cb.active)
            self.ids.articles.add_widget(aw)

class SaveScreen(Screen):
    def save(self, filepath, filename):
        file = os.path.join(filepath, filename + ".md")
        with open(file, "w", encoding='UTF-8') as f:
            for article in self.manager.articles:
                f.write(article.to_string(self.manager.keep_line_breaks) + "\n\n---\n\n")
        if sys.platform == "win32":
            os.startfile(file)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, file])
        OCRticleApp.get_running_app().stop()

class MyScreenManager(ScreenManager):
    image_source = StringProperty()
    article_images = ListProperty()
    articles = ListProperty()
    processed = BooleanProperty()
    keep_line_breaks = BooleanProperty()

    def load_image(self, selection):
        if len(selection) > 0:
            self.image_source = selection[0]
            self.current = 'image_preview'

    def return_to_prev(self):
        self.current = self.previous()

class MyTextInput(TextInput):
    pass

class MyLabel(Label):
    pass

class ReturnButton(Button):
    pass

class ArticleWidget(GridLayout):
    article_object = ObjectProperty()
    ls = ListProperty()
    dds = ListProperty()

    def change_dd(self, btn, instance, x):
        bt = BlockType[x]
        self.article_object.blocks[btn.i].type = BlockType[x]
        if bt == BlockType.TITLE:
            self.ls[btn.i].font_size=sp(25)
        else:
            self.ls[btn.i].font_size=sp(20)
        setattr(btn ,'text', x)

    def select_option(self, dd, btn):
        dd.select(btn.text)

    def add_article(self, article, keep_line_breaks = False):
        self.ls = []
        self.dds = []
        self.article_object = article
        for i,block in enumerate(article.blocks):
            t = block.to_string(keep_line_breaks, type_formatting=False)
            if block.type == BlockType.TITLE:
                font_size = sp(25)
            else:
                font_size = sp(20)
            l = MyLabel(text=t, font_size=font_size)
            self.add_widget(l)
            self.ls.append(l)
            dd = DropDown()
            self.dds.append(dd)
            for t in BlockType:
                btn = Button(text=t.name, size_hint_y=None, height=44)
                btn.bind(on_release=partial(self.select_option, dd))
                dd.add_widget(btn)
            b = Button(text=block.type.name, size_hint=(None, None), height=44, pos_hint={'right': 1, 'top': 1})
            b.i = i
            b.bind(on_release=dd.open)
            dd.bind(on_select=partial(self.change_dd, b))

            f = FloatLayout(size_hint=(0.1, 1))
            f.add_widget(b)
            self.add_widget(f)

class MainApp(App):

    def build(self):
        sm = MyScreenManager()
        self.sm = sm
        sm.add_widget(FileSelectScreen(name='file_select'))
        sm.add_widget(ImagePreviewScreen(name='image_preview'))
        sm.add_widget(ArticlePreviewScreen(name='article_preview'))
        sm.add_widget(SaveScreen(name='save'))
        if self.default_image:
            sm.image_source = self.default_image
            sm.current = 'image_preview'
        return sm