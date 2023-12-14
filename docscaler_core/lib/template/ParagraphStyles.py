'''
Created on 13 Dec 2017

@author: mwolf
'''

import sys, os
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4

def getRuntimePath(file):
    if getattr( sys, 'frozen', False ) :
        bundle_dir = sys._MEIPASS + "/" + file
    else:
        bundle_dir = os.path.abspath(file)
        
    return bundle_dir

styles = getSampleStyleSheet()
styleN = styles["Normal"]

ddnRed = HexColor(0xA71930)
ddnGrey = HexColor(0x4D4F53)
ddnLightRed = HexColor(0xDD4814)
#ddnLightRed = toColor("rgb(245,209,209)")

pdfmetrics.registerFont(TTFont("Inconsolata-Regular", getRuntimePath("media/fonts/Inconsolata/Inconsolata-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Inconsolata-Bold", getRuntimePath("media/fonts/Inconsolata/Inconsolata-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Inconsolata-Light", getRuntimePath("media/fonts/Inconsolata/Inconsolata-Light.ttf")))
pdfmetrics.registerFont(TTFont("Inconsolata-Medium", getRuntimePath("media/fonts/Inconsolata/Inconsolata-Medium.ttf")))
pdfmetrics.registerFont(TTFont("FreeMono", getRuntimePath("media/fonts/FreeMono/FreeMono.ttf")))
pdfmetrics.registerFont(TTFont("Lato", getRuntimePath("media/fonts/Lato/Lato-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Lato-Bold", getRuntimePath("media/fonts/Lato/Lato-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Lato-Italic", getRuntimePath("media/fonts/Lato/Lato-Italic.ttf")))
pdfmetrics.registerFont(TTFont("Lato-BoldItalic", getRuntimePath("media/fonts/Lato/Lato-BoldItalic.ttf")))

title = ParagraphStyle(name='title', fontName = "Lato", fontSize=26, textColor=black)
title_red = ParagraphStyle(name='title', fontName = "Lato-Bold", fontSize=22, textColor=ddnRed)
title_company = ParagraphStyle(name='title_company', fontSize=22, parent=title)
title_date = ParagraphStyle(name='title_date', fontSize=18, parent=title)
title_info = ParagraphStyle(name='title_info', fontName = "Lato", fontSize=11, textColor=ddnGrey)

normal = ParagraphStyle(name='normal', fontName = "Lato", fontSize=9, leading=12, leftIndent=20, spaceBefore=5, spaceAfter=5)
bold = ParagraphStyle(name='bold', fontName = "Lato-Bold", fontSize=9, leading=12, leftIndent=20, spaceBefore=5, spaceAfter=5)
italic = ParagraphStyle(name='italic', fontName = "Lato-Italic", fontSize=9, leading=12, leftIndent=20, spaceBefore=5, spaceAfter=5)
boldItalic = ParagraphStyle(name='italicbold', fontName = "Lato-BoldItalic", fontSize=9, leading=12, leftIndent=20, spaceBefore=5, spaceAfter=5)

addMapping('Lato', 0, 0, 'Lato')             #normal
addMapping('Lato', 0, 1, 'Lato-Italic')      #italic
addMapping('Lato', 1, 0, 'Lato-Bold')        #bold
addMapping('Lato', 1, 1, 'Lato-BoldItalic')  #italic and bold

htoc = ParagraphStyle(name='TOC', fontName = "Lato-Bold", fontSize=18, leading=14, spaceAfter=6, textColor=ddnRed)
h1 = ParagraphStyle(name='Heading1', fontName = "Lato", fontSize=18, leading=10, spaceBefore=6, spaceAfter=6, textColor=ddnRed)
h2 = ParagraphStyle(name='Heading2', fontName = "Lato", fontSize=14, leading=10, spaceBefore=12, spaceAfter=10, leftIndent=10, textColor=ddnRed)
h3 = ParagraphStyle(name='Heading3', fontName = "Lato", fontSize=11, leading=10, spaceBefore=12, spaceAfter=10, leftIndent=14, textColor=ddnRed)
h4 = ParagraphStyle(name='Heading4', fontName = "Lato", fontSize=10, leading=10, spaceBefore=12, spaceAfter=10, leftIndent=20, underlineOffset="-0.2*F", underlinewidth=0.5)

appendix = ParagraphStyle(name='Appendix', fontName = "Lato", fontSize=18, leading=10, spaceBefore=6, spaceAfter=6, textColor=ddnRed)

h1toc = ParagraphStyle(name='Heading1TOC', fontName = "Lato-Bold", fontSize=10, leading=12, spaceBefore=8, spaceAfter=6, textColor=ddnRed)
h2toc = ParagraphStyle(name='Heading2TOC', fontName = "Lato-Bold", fontSize=10, leading=8, spaceAfter=8, leftIndent=10)
h3toc = ParagraphStyle(name='Heading3TOC', fontName = "Lato", fontSize=10, leading=7, spaceAfter=8, leftIndent=18)

appendixtoc = ParagraphStyle(name='AppendixTOC', fontName = "Lato-Bold", fontSize=10, leading=14, spaceBefore=6, spaceAfter=6)

bullet = ParagraphStyle(name='bullet', fontName = "Lato", fontSize=9, leftIndent=10, spaceBefore=5, spaceAfter=10, leading=5, bulletIndent=10)
syntax = ParagraphStyle(name='syntax', fontName = "FreeMono", fontSize=7, leading=5)
codeBlank = ParagraphStyle(name='codeBlank', fontName = "Inconsolata-Regular", fontSize=6.7, leading=7.4, borderWidth=0.3, borderColor=ddnRed, leftIndent=20, padding=(4,2))
codeBold = ParagraphStyle(name='codeBold', fontName = "Inconsolata-Bold", fontSize=6.7, leading=7.4, borderWidth=0.3, borderColor=ddnRed, leftIndent=20, padding=(4,2))
codeItalic = ParagraphStyle(name='codeItalic', fontName = "Inconsolata-Light", fontSize=6.7, leading=7.4, borderWidth=0.3, borderColor=ddnRed, leftIndent=20, padding=(4,2))
codeBoldItalic = ParagraphStyle(name='codeBoldItalic', fontName = "Inconsolata-Medium", fontSize=6.7, leading=7.4, borderWidth=0.3, borderColor=ddnRed, leftIndent=20, padding=(4,2))

addMapping('Inconsolata', 0, 0, 'Inconsolata-Regular')             #normal
addMapping('Inconsolata', 0, 1, 'Inconsolata-Bold')      #italic
addMapping('Inconsolata', 1, 0, 'Inconsolata-Light')        #bold
addMapping('Inconsolata', 1, 1, 'Inconsolata-Medium')  #italic and bold
