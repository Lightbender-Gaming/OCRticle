from statistics import median
from string import ascii_lowercase
from enum import Enum

import pandas as pd
import pytesseract

class BlockType(Enum):
    TITLE = 0
    TEXT = 1
    QUOTE = 2
    CODE = 3

class Article():

    def __init__(self, image) -> None:
        df : pd.DataFrame = pytesseract.image_to_data(image, lang='por', output_type=pytesseract.Output.DATAFRAME)

        with open('log.csv','w',encoding='UTF-8') as f:
            df.to_csv(f,index=False)

        blocks = []
        for (_,block_df) in df.groupby('block_num'):
            block = Block()
            block.width = block_df['width'].iloc[0]

            for (_,par_df) in block_df.groupby('par_num'):
                paragraph = Paragraph()

                for (_,line_df) in par_df.groupby('line_num'):
                    words = line_df.loc[line_df['level'] == 5]['text'].tolist()
                    if len(words) > 0 and not all(word.isspace() for word in words):
                        line = Line(words, line_df.iloc[0]['height'])
                        paragraph.lines.append(line)

                if len(paragraph.lines) > 0:
                    block.paragraphs.append(paragraph)

            if len(block.paragraphs) > 0:
                blocks.append(block)
            
        self.blocks : list[Block] = blocks
        if len(blocks) > 0:
            self.optimize()
                
        font_sizes = sorted(((i,x.get_line_height()) for i,x in enumerate(self.blocks) if len(x.paragraphs) == 1), reverse=True, key=lambda x: x[1])

        if len(font_sizes) > 1 and font_sizes[0][1] > font_sizes[1][1] + 5:
            self.blocks[font_sizes[0][0]].type = BlockType.TITLE

    def __str__(self) -> str:
        # '\n\n<br/>\n\n'
        return '\n\n\n\n'.join(str(x) for x in self.blocks)

    def to_string(self, keep_line_breaks) -> str:
        return '\n\n\n\n'.join(x.to_string(keep_line_breaks) for x in self.blocks)

    def optimize(self) -> None:
        new_blocks : list[Block] = []
        prev_block : Block = None
        changes = False
        for block in self.blocks:
            if not prev_block: 
                prev_block = block
                continue

            if (abs(prev_block.get_line_height() - block.get_line_height()) <= 3
                and prev_block.get_last_char() in ascii_lowercase + "-"
                and (abs(prev_block.width - block.width) / block.width) < 0.1):
                prev_block.paragraphs.extend(block.paragraphs)
                prev_block.width = max(prev_block.width, block.width)
                prev_block.line_height = None
                changes = True
            else:
                new_blocks.append(prev_block)
                prev_block = block
            
        new_blocks.append(prev_block)
        for block in new_blocks:
            block.optimize()

        self.blocks = new_blocks
        if changes:
            self.optimize()

class Block():

    def __init__(self) -> None:
        self.paragraphs : list[Paragraph] = []
        self.line_height = None
        self.type = BlockType.TEXT
        self.width = None

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self, keep_line_breaks = False, type_formatting = True):
        pars = '\n\n'.join(x.to_string(keep_line_breaks) for x in self.paragraphs)
        if type_formatting:
            if self.type == BlockType.TITLE:
                return "# " + self.paragraphs[0].to_string()
            if self.type == BlockType.QUOTE:
                return '\n'.join("> " + x for x in pars.splitlines())
            if self.type == BlockType.CODE:
                return "```\n" + pars + "\n```"
            return pars
        else:
            return pars

    def optimize(self) -> None:
        new_paragraphs = []
        prev_paragraph : Paragraph = None
        changes = False
        for paragraph in self.paragraphs:
            if not prev_paragraph: 
                prev_paragraph = paragraph
                continue

            last_char = prev_paragraph.get_last_char() 
            if last_char in ascii_lowercase:
                prev_paragraph.lines.extend(paragraph.lines)
                prev_paragraph.line_height = None
                changes = True
            elif last_char == '-' and paragraph.get_first_char() in ascii_lowercase:
                prev_paragraph.remove_last_char()
                prev_paragraph.lines[-1].words[-1] += paragraph.pop_first_word()
                prev_paragraph.lines.extend(paragraph.lines)
                prev_paragraph.line_height = None
                changes = True
            else:
                new_paragraphs.append(prev_paragraph)
                prev_paragraph = paragraph
            
        new_paragraphs.append(prev_paragraph)
        for paragraph in new_paragraphs:
            paragraph.optimize()
        self.paragraphs = new_paragraphs
        if changes:
            self.optimize()

    def get_line_height(self) -> int:
        if self.line_height:
            return self.line_height
        self.line_height = median(par.get_line_height() for par in self.paragraphs)
        return self.line_height

    def get_last_char(self) -> str:
        if len(self.paragraphs) == 0:
            return None
        return self.paragraphs[-1].get_last_char()
    
    def remove_last_char(self) -> None:
        if len(self.paragraphs) > 0:
            self.paragraphs[-1].remove_last_char()

class Paragraph():

    def __init__(self) -> None:
        self.lines = []
        self.height = None

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self, keep_line_breaks = False):
        if keep_line_breaks:
            return '\n'.join(str(x) for x in self.lines)
        else:
            return ' '.join(str(x) for x in self.lines)
    
    def get_line_height(self) -> int:
        if self.height:
            return self.height
        self.height = median(line.height for line in self.lines)
        return self.height

    def get_last_char(self) -> str:
        if len(self.lines) == 0:
            return None
        return self.lines[-1].get_last_char()

    def get_first_char(self) -> str:
        if len(self.lines) == 0:
            return None
        return self.lines[0].get_first_char()

    def pop_first_word(self) -> str:
        if len(self.lines) == 0:
            return None
        return self.lines[0].pop_first_word()

    def remove_last_char(self) -> None:
        if len(self.lines) > 0:
            self.lines[-1].remove_last_char()

    def optimize(self) -> None:
        new_lines = []
        prev_line : Line = None
        for line in self.lines:
            if not prev_line: 
                prev_line = line
                continue

            last_char = prev_line.get_last_char() 
            if last_char == '-' and line.get_first_char() in ascii_lowercase:
                prev_line.remove_last_char()
                prev_line.words[-1] += line.pop_first_word()
            if len(line.words) > 0:
                new_lines.append(prev_line)
                prev_line = line
            
        new_lines.append(prev_line)
        self.lines = new_lines

class Line():

    def __init__(self, words, height):
        self.words : list[str] = words
        self.height : int = height

    def __str__(self) -> str:
        return ' '.join(self.words)

    def get_last_char(self) -> str:
        if len(self.words) == 0:
            return None
        return self.words[-1][-1]

    def get_first_char(self) -> str:
        if len(self.words) == 0:
            return None
        return self.words[0][0]

    def pop_first_word(self) -> str:
        if len(self.words) == 0:
            return None
        return self.words.pop(0)

    def remove_last_char(self) -> None:
        self.words[-1] = self.words[-1][:-1]