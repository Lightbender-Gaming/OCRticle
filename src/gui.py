import os, sys, subprocess

from PIL import Image as Im
from PIL import ImageDraw

from article import Article
import geometry

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.properties import StringProperty,\
    BooleanProperty,\
    ListProperty,\
    NumericProperty,\
    ObjectProperty,\
    DictProperty
from kivy.graphics import Color, Ellipse, Rectangle
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

    def on_enter(self, *args):
        self.manager.article_images = []
        self.ids.undo_article_btn.disabled = True
        self.ids.undo_exclude_btn.disabled = True
        self.drawing = False
        self.current_mode = "A"
        self.rectangles_articles = []
        self.rectangles_exclude = []
        self.ids.image_p.source = self.manager.image_source
        self.ids.image_p.opacity = 1
        self.ids.image_p.reload()
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
        image = self.ids.image_p

        min_x = image.center_x - image.norm_image_size[0] / 2
        max_x = image.center_x + image.norm_image_size[0] / 2
        min_y = image.center_y - image.norm_image_size[1] / 2
        max_y = image.center_y + image.norm_image_size[1] / 2

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
                'original_x': (touch.x - min_x) * image.texture_size[0] / image.norm_image_size[0],
                'original_y': (touch.y - min_y) * image.texture_size[1] / image.norm_image_size[1],
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
            active_rect['original_width'] = width * self.ids.image_p.texture_size[0] / self.ids.image_p.norm_image_size[0]
            active_rect['original_height'] = height * self.ids.image_p.texture_size[1] / self.ids.image_p.norm_image_size[1]
        else:
            return super().on_touch_move(touch)

    def on_resize(self, instance, value):

        for r in self.rectangles_exclude + [r for ra in self.rectangles_articles for r in ra]:
            r['rect'].pos = (r['original_x'] * instance.norm_image_size[0] / instance.texture_size[0] + (instance.center_x - instance.norm_image_size[0] / 2),
                            r['original_y'] * instance.norm_image_size[1] / instance.texture_size[1] + (instance.center_y - instance.norm_image_size[1] / 2))

            r['rect'].size = (r['original_width'] * instance.norm_image_size[0] / instance.texture_size[0],
                              r['original_height'] * instance.norm_image_size[1] / instance.texture_size[1])

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

        im = Im.open(self.manager.image_source)
        im_colors = im.resize((1000,1000))
        freqs = dict()
        for h in range(1000):
            for w in range(1000):
                c = im_colors.getpixel((w,h))
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
                    mask = Im.new("RGBA", size=im.size)
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
                    mask = mask.transpose(Im.Transpose.FLIP_TOP_BOTTOM)
                    blank = Im.new("RGB", color=most_common, size=im.size)
                    final_image = Im.composite(im, blank, mask).crop((min_left, min_top, max_right, max_bottom))
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

    def change_line_breaks(self):
        self.refresh_articles()

    # def teste(self):
    #     for w in self.ids.articles.children:
    #         print(str(w.article_object))
    #         # TODO Make this method add the articles to the manager's articles list

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

    def add_article(self, article, keep_line_breaks = False):
        self.article_object = article
        for block in article.blocks:
            t = block.to_string(keep_line_breaks)
            if t.startswith("# "):
                font_size = sp(25)
            else:
                font_size = sp(20)
            l = MyLabel(text=t, font_size=font_size)
            self.add_widget(l)

class OCRticleApp(App):

    def build(self):
        sm = MyScreenManager()
        self.sm = sm
        sm.add_widget(FileSelectScreen(name='file_select'))
        sm.add_widget(ImagePreviewScreen(name='image_preview'))
        sm.add_widget(ArticlePreviewScreen(name='article_preview'))
        sm.add_widget(SaveScreen(name='save'))
        return sm