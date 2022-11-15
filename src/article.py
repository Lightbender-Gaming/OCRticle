from statistics import median

import pandas as pd
import pytesseract

class Article():

    def __init__(self, image) -> None:
        df : pd.DataFrame = pytesseract.image_to_data(image, lang='por', output_type=pytesseract.Output.DATAFRAME)

        with open('log.csv','w',encoding='UTF-8') as f:
            df.to_csv(f,index=False)

        blocks = []
        for (_,block_df) in df.groupby('block_num'):
            block = Block()
            block.n = block_df['block_num'].iloc[0]

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
            
        self.blocks = blocks

    def __str__(self) -> str:
        return '\n---\n'.join(str(x) for x in self.blocks)

    def optimize(self) -> None:
        new_blocks = []
        prev_block = None
        for block in self.blocks:
            if not prev_block: 
                prev_block = block
                continue

            if prev_block.paragraphs[-1].lines[-1].words.strip()[-1].isalpha():
                prev_block.paragraphs.extend(block.paragraphs)
            else:
                new_blocks.append(prev_block)
                prev_block = block
            
        new_blocks.append(prev_block)
        for block in new_blocks:
            block.optimize()
        self.blocks = new_blocks

class Block():

    def __init__(self) -> None:
        self.paragraphs = []
        self.line_height = None

    def __str__(self) -> str:
        return '\n\n\t'.join(str(x) for x in self.paragraphs)

    def optimize(self) -> None:
        new_paragraphs = []
        prev_paragraph = None
        for paragraph in self.paragraphs:
            if not prev_paragraph: 
                prev_paragraph = paragraph
                continue

            if prev_paragraph.lines[-1].words.strip()[-1].isalpha():
                prev_paragraph.lines.extend(paragraph.lines)
            else:
                new_paragraphs.append(prev_paragraph)
                prev_paragraph = paragraph
            
        new_paragraphs.append(prev_paragraph)
        self.paragraphs = new_paragraphs

    def get_line_height(self) -> int:
        if self.line_height:
            return self.line_height
        self.line_height = median(par.get_line_height() for par in self.paragraphs)
        return self.line_height

class Paragraph():

    def __init__(self) -> None:
        self.lines = []
        self.height = None

    def __str__(self) -> str:
        return '\n'.join(str(x) for x in self.lines)
    
    def get_line_height(self) -> int:
        if self.height:
            return self.height
        self.height = median(line.height for line in self.lines)
        return self.height

class Line():

    def __init__(self, words, height):
        self.words : str = words
        self.height : int = height

    def __str__(self) -> str:
        return self.words