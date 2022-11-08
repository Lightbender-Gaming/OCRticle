# from PIL import Image
from sys import argv
from io import StringIO
from statistics import median

import pandas as pd
import pytesseract
import kivy
kivy.require('2.1.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.properties import StringProperty
from kivy.graphics import Color, Ellipse

from article import Article, Block, Paragraph, Line

def generate_ir(filename):
    df : pd.DataFrame = pytesseract.image_to_data(filename, lang='por', output_type=pytesseract.Output.DATAFRAME)

    with open('log.csv','w',encoding='UTF-8') as f:
        df.to_csv(f,index=False)

    blocks = []
    for (_,block_df) in df.groupby('block_num'):
        block = Block()

        for (_,par_df) in block_df.groupby('par_num'):
            paragraph = Paragraph()

            for (_,line_df) in par_df.groupby('line_num'):
                words = line_df.loc[line_df['level'] == 5]['text'].tolist()
                if len(words) > 0 and not all(word.isspace() for word in words):
                    line = Line(' '.join(words), line_df.iloc[0]['height'])
                    paragraph.lines.append(line)

            if len(paragraph.lines) > 0:
                block.paragraphs.append(paragraph)

        if len(block.paragraphs) > 0:
            block.optimize()
            # article.blocks.append(block)
            blocks.append(block)
    
    return blocks

# class FileSelect(GridLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.cols = 1
#         self.add_widget(Label(text="Selecione um ficheiro."))
#         self.add_widget(FileChooserIconView(path='.'))

class FileSelectScreen(Screen):
    pass

class ImagePreviewScreen(Screen):
    def on_enter(self, *args):
        self.ids.image_p.source = self.manager.image_source
        self.ids.image_p.opacity = 1
        self.ids.image_p.reload()

    def on_touch_down(self, touch):
        print(touch)
        with self.canvas:
            Color(1,0,1)
            d = 5
            Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d,d))

        return super().on_touch_down(touch)

class MyScreenManager(ScreenManager):
    image_source = StringProperty()

    def load_image(self, selection):
        self.image_source = selection[0]
        # print(*(str(b) for b in generate_ir(selection[0])), sep='\n---\n')
        # print(generate_ir(selection))

class OCRApp(App):

    def build(self):
        sm = MyScreenManager()

        sm.add_widget(FileSelectScreen(name='file_select'))
        sm.add_widget(ImagePreviewScreen(name='image_preview'))
        return sm

if __name__ == '__main__':
    if len(argv) == 1:
        OCRApp().run()
    else:
        print(*(str(b) for b in generate_ir(argv[1])), sep='\n---\n')
        




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