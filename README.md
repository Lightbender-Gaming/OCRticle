# OCRticle

GUI application capable of extracting text from an image, while keeping the text's original structure. OCRticle works best with articles (hence the name), but it should function with any kind of text.

## Installation

OCRticle requires Python >= 3.10 and the Tesseract OCR engine. Instructions for installing Tesseract can be found [here](https://tesseract-ocr.github.io/tessdoc/Installation.html). Currently, OCRticle supports OCR for text in English and in Portuguese. For detecting text in Portuguese, the corresponding Tesseract language pack must be installed.

Linux users should be able to install OCRticle by just running:

```
pip install ocrticle
```

For Windows users, a pre-compiled binary can be downloaded from [here](https://github.com/RisingFisan/Projeto-PI/releases/).

## Usage

When invoked from the command line, OCRticle can be given an image path as an optional argument. Otherwise, the application will ask the user to select an image from the computer.

After an image has been selected, the next window of the application allows the user to draw rectangles to select the articles present in the image. Each rectangle or group of intersecting rectangles should correspond to one article. Alternatively, the user can draw rectangles to exclude certain parts of the image from being scanned by selecting the corresponding option. There are also options to change the brightness, contrast and saturation of the source image. For example, to convert an image to black and white, the saturation can be set to 0.

Once this step is concluded, OCRticle will use Tesseract to scan the image or the selected rectangles and extract the text found in each. Then, OCRticle will try to automatically join the text in different blocks. This behavior is largely dependent on Tesseract's detection, which is not perfect, therefore the blocks may not exactly match the original text.

The user is able to tag each block, according to its contents. These tags are: Title, Text, Quote, and Code. OCRticle will try to automatically "guess" which block is the article's title, but, if it fails, the user can fix the mislabeling. OCRticle will also remove some line breaks, when it believes that two lines are part of the same paragraph. This behavior can be toggled during this step.

Finally, the user can save the scanned articles in a Markdown file, where the blocks will be identified according to their tags.