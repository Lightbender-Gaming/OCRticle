from statistics import median

class Article():

    def __init__(self) -> None:
        self.blocks : list[Block] = []

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