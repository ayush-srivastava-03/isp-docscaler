#-*- coding: utf-8 -*-

'''
Created on 13 Dec 2017

@author: mwolf
'''

from PIL import Image as PILImage
from io import StringIO
from datetime import date

import re

from operator import truth
from template import ParagraphStyles, flowables
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.flowables import PageBreak, Image, Spacer
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.colors import black, white
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.sequencer import Sequencer
from reportlab.platypus import Paragraph, NextPageTemplate
from reportlab.platypus.doctemplate import FrameBreak
from reportlab.platypus.tableofcontents import TableOfContents
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from preppy import BytesIO

class Picture(Image):
    def __init__(self, image, doc, page=0):
        self.__image_split = image.split(":")
        self.image = self.__image_split[0]
        self.doc = doc
        self.page = page
        
        # Open the image and store it in a variable
        self.im = PILImage.open(self.image)
        
        # Rotate the image if specified
        if len(self.__image_split) > 2 and self.__image_split[2] != "":
            self.im = self.im.rotate(int(self.__image_split[2]))
        
        # Save the modified image to a BytesIO object
        image_data = BytesIO()
        self.im.save(image_data, format="PNG")
        
        # Initialize the Image with the modified image data
        Image.__init__(self, image_data, width=self.scale, height=self.scale, lazy=-1, kind="percentage")   
        
    @property
    def scale(self):
        
        if len(self.__image_split) > 1:
            if self.__image_split[1] != "auto" and self.__image_split[1] != "":
                return int(self.__image_split[1])
        
        # Calculate the minimum scale required to fit the image within the available width or height
        if self.im.size[0] > (self.doc.width - 100) or self.im.size[1] > (self.doc.height - 200):
            if self.page == 1:
                width = 350
                height = 450
            else:
                width = 100
                height = 200
            
            width_scale = (self.doc.width - width) / (self.im.size[0] / 100)
            height_scale = (self.doc.height - height) / (self.im.size[1] / 100)
            
            return min(width_scale, height_scale)
        
        return 100   

#on UTF8/py33 branch, split and strip must be unicode-safe!
#thanks to Dirk Holtwick for helpful discussions/insight
#on this one
_wsc = ''.join((
    u'\u0009',  # HORIZONTAL TABULATION
    u'\u000A',  # LINE FEED
    u'\u000B',  # VERTICAL TABULATION
    u'\u000C',  # FORM FEED
    u'\u000D',  # CARRIAGE RETURN
    u'\u001C',  # FILE SEPARATOR
    u'\u001D',  # GROUP SEPARATOR
    u'\u001E',  # RECORD SEPARATOR
    u'\u001F',  # UNIT SEPARATOR
    u'\u0020',  # SPACE
    u'\u0085',  # NEXT LINE
    #u'\u00A0', # NO-BREAK SPACE
    u'\u1680',  # OGHAM SPACE MARK
    u'\u2000',  # EN QUAD
    u'\u2001',  # EM QUAD
    u'\u2002',  # EN SPACE
    u'\u2003',  # EM SPACE
    u'\u2004',  # THREE-PER-EM SPACE
    u'\u2005',  # FOUR-PER-EM SPACE
    u'\u2006',  # SIX-PER-EM SPACE
    u'\u2007',  # FIGURE SPACE
    u'\u2008',  # PUNCTUATION SPACE
    u'\u2009',  # THIN SPACE
    u'\u200A',  # HAIR SPACE
    u'\u200B',  # ZERO WIDTH SPACE
    u'\u2028',  # LINE SEPARATOR
    u'\u2029',  # PARAGRAPH SEPARATOR
    u'\u202F',  # NARROW NO-BREAK SPACE
    u'\u205F',  # MEDIUM MATHEMATICAL SPACE
    u'\u3000',  # IDEOGRAPHIC SPACE
    ))
_wsc_re_split=re.compile('[%s]+'% re.escape(_wsc)).split

def isBytes(v):
    return isinstance(v, bytes)

def split(text, delim=None):
    if isBytes(text): text = text.decode('utf8')
    if delim is not None and isBytes(delim): delim = delim.decode('utf8')
    return [uword for uword in (_wsc_re_split(text) if delim is None and u'\xa0' in text else text.split(delim))]

def _lineClean(L):
    text = list(filter(truth,split(L, '\n')))
    return ' '.join(text)

def cleanBlockQuotedText(text,joiner=' '):
    """This is an internal utility which takes triple-
    quoted text form within the document and returns
    (hopefully) the paragraph the user intended originally."""
    L=list(filter(truth,list(map(_lineClean, split(text, '\n')))))
    return joiner.join(L)

class TextParagraph(Paragraph):
    def __init__(self, text, style=None, bulletText = None, frags=None, caseSensitive=1, encoding='utf8'):
        if style is None:
            style = ParagraphStyle(name='paragraphImplicitDefaultStyle')
        self.caseSensitive = caseSensitive
        self.encoding = encoding
        self._setup(text, style, bulletText or getattr(style,'bulletText',None), frags, cleanBlockQuotedText)


class TemplateParser():
    def __init__(self, doc, configData):
        self.doc = doc
        self.configData = configData
        
    def parse(self, html, story):
        self.story = story
        soup = BeautifulSoup(html, 'html.parser')
        
        #print(soup.prettify())
        
        for tag in soup.contents:
            
            if tag.name == None:
                if tag.string.startswith("#") or tag.string == (""):
                    continue   
            
            if tag.name == "text":
                s = ""
 
                for string in tag.contents:
                    if isinstance(string, NavigableString):
                        s = s + str(string).replace("\n", "<br/>\n")
                    else:
                        s = s + str(string)#.lstrip("\n")
                #
                # s.replace("\n", "<br/>\n")
                self.story.append(Paragraph(s, ParagraphStyles.normal))
            
            if tag.name == "br":
                self.story.append(Paragraph("", ParagraphStyles.normal))
            
            if tag.name == "bullet":
                self.story.append(Paragraph(tag.string.strip(), ParagraphStyles.bullet, bulletText="•"))
            
            if tag.name == "pagebreak":
                self.story.append(PageBreak())
            
            if tag.name == "img":
                self.story.append(Picture(self.configData.getConfigPath() + "/" + tag["src"], self.doc))
            
            if tag.name == "h1":
                self.story.append(Paragraph(tag.string, ParagraphStyles.h1))               
                
            if tag.name == "h2":
                self.story.append(Paragraph(tag.string, ParagraphStyles.h2))
                
            if tag.name == "h3":
                self.story.append(Paragraph(tag.string, ParagraphStyles.h3))
                
            if tag.name == "h4":
                self.story.append(Paragraph("<u>" + tag.string + "</u>", ParagraphStyles.h4))
                
            if tag.name == "code":
                code = []
                
                if tag.string != None:
                    d = StringIO(tag.string)
                    for line in d:
                        if line == "\n" and d.tell() == 1:
                            continue
                        elif line == "\n":
                            line = " "
                        code.append(line.lstrip('\t'))
                else:
                    line = ""
                    for c in tag.contents:
                        line = line + str(c)
                    
                    code.append(line)
                    
                self.story.append(flowables.code(code, ParagraphStyles.codeBlank))
                
            if tag.name == "table":
                tableData = []
                
                for tr in tag.findAll("tr"):
                    rowData = []
                    
                    for td in tr.children:
                        if td.string != "\n" and td.string != None:
                            rowData.append(td.string)
                    tableData.append(rowData)
                
                #print(tableData)
                
                #VDS
                if tag.has_attr('style'):
                    if tag["style"] == "vds":
                        t = Table(tableData, colWidths=60 ,
                                  style=[('ALIGN',(0,0),(-1,-1),'CENTER'),
                                         ('GRID', (0,0), (-1,-1), 0.25, black),
                                         ('BOX', (0,0), (-1,-1), 0.25, black),
                                         ('BACKGROUND',(0,0),(3,0),black),
                                         ('TEXTCOLOR',(0,0),(3,0),white),
                                         ('SPAN',(0,0),(3,0)),
                                         ('BACKGROUND',(0,1),(3,1), ParagraphStyles.ddnRed),
                                         ('TEXTCOLOR',(0,1),(3,1),white),
                                         ('SPAN',(0,1),(1,1)),
                                         ('SPAN',(2,1),(3,1)),
                                         ('BACKGROUND',(0,2),(-1,-2), ParagraphStyles.ddnGrey),
                                         ('TEXTCOLOR',(0,2),(-1,-2),white),
                                         ('FONT', (0,0), (-1,-1), 'Lato', 9, 11)
                                        ]) 
                        self.story.append(t)
                          
                    #NOBORDER
                    if tag["style"] == "noborder":
                        for td in tableData:
                            td.insert(0, "")
                        
                        t = Table(tableData, hAlign='LEFT', 
                                  style=[('ALIGN',(0,0),(-1,-1),'LEFT'),
                                         ('VALIGN',(0,0),(-1,-1),'TOP'),
                                         ('FONT', (0,0), (-1,-1), 'Lato', 9, 11),
                                         ('TEXTCOLOR',(1,0),(-2,-1), ParagraphStyles.ddnRed)
                                        ])
                        #fake left indent
                        t._argW[0]=0.5*cm
                        self.story.append(t)
                else:  
                    #ANY OTHER TABLE
                    t = Table(tableData)
                    for each in range(len(tableData)):
                        if each % 2 == 0:
                            bg_color = ParagraphStyles.ddnGrey
                            fg_color = white
                        else:
                            bg_color = white
                            fg_color = black
    
                        t.setStyle(TableStyle([('BACKGROUND', (0, each), (-1, each), bg_color),
                                               ('TEXTCOLOR', (0, each), (-1, each), fg_color)
                                               ]))
                    
                    t.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'LEFT'),
                                           ('VALIGN',(0,0),(-1,-1),'TOP'),
                                           ('GRID', (0,0), (-1,-1), 0.25, black),
                                           ('BOX', (0,0), (-1,-1), 0.25, black),
                                           ('BACKGROUND',(0,0),(-1,0), ParagraphStyles.ddnRed),
                                           ('TEXTCOLOR',(0,0),(-1,0),white),
                                           ('FONT', (0,0), (-1,-1), 'Lato', 9, 11)
                                           ]))
                    
                    self.story.append(t)
                    
        self.story.append(PageBreak())    
            
class DDNDocTemplate(BaseDocTemplate):
    
    def __init__(self, filename, configData):
        BaseDocTemplate.__init__(self, filename, pagesize=A4, leftMargin=30, rightMargin=30, bottomMargin=60, topMargin=85)
        self._leftMargin=20
        self._rightMargin=20
        self._bottomMargin=60
        self._topMargin=85
        self.configData = configData
        
        textFrameFirstPage = Frame(self.leftMargin, self.bottomMargin + 85, self.width, self.height - self.topMargin - 25, id="textFrameFirstPage", showBoundary=0)
        textFrameNormalPage = Frame(self.leftMargin, self.bottomMargin, self.width, self.height - 30, id="textFrameNormalPage", showBoundary=0)
        frame2 = Frame(self.leftMargin, self.bottomMargin, self.width/2, self.bottomMargin + 30, id="frame2", showBoundary=0)
        frame3 = Frame(self.leftMargin + self.width/2, self.bottomMargin, self.width/2, self.bottomMargin + 30, id="frame3", showBoundary=0)
        firstPage = PageTemplate(id="firstPage", frames=[textFrameFirstPage, frame2, frame3], onPage=self.firstPageHeader, onPageEnd=self.footer)
        self.normalPage = PageTemplate(id="normalPage", frames=textFrameNormalPage, onPage=self.header, onPageEnd=self.footer)
        self.addPageTemplates([firstPage, self.normalPage])
        
        self.headerSectionText = None
        self.seq = Sequencer()

    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if flowable.__class__.__name__ == 'Paragraph':
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'TOC':
                key = 'toc-%s' % self.seq.nextf('TOC')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
            if style == 'Heading1':
                key = 'h1-%s' % self.seq.nextf('heading1')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
            if style == 'Heading2':
                key = 'h2-%s' % self.seq.nextf('heading2')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (1, text, self.page, key))
            if style == 'Heading3':
                key = 'h3-%s' % self.seq.nextf('heading3')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (2, text, self.page, key))
            if style == 'Heading4':
                key = 'h4-%s' % self.seq.nextf('heading3')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (3, text, self.page, key))
            if style == 'Appendix':
                self.seq.setFormat('appendix', "A")
                key = 'appendix-%s' % self.seq.nextf('appendix')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))
    
    def filterFlowables(self, flowables):
        if flowables[0].__class__.__name__ == 'Paragraph':
            style = flowables[0].style.name
            if style == 'TOC':
                self.headerSectionText = flowables[0].text
            if style == 'Heading1':
                self.headerSectionText = "Section %(Section+)s, " % self.seq + flowables[0].text
                flowables[0].frags[0].text = ("%(Section)s. " % self.seq) + flowables[0].text
                self.seq.reset("Figure1")
                self.seq.reset("Figure2")
            if style == 'Heading2':
                flowables[0].frags[0].text = ("%(Section)s.%(Figure1+)s " % self.seq) + flowables[0].text
                self.seq.reset("Figure2")
            if style == 'Heading3':
                flowables[0].frags[0].text = ("%(Section)s.%(Figure1)s.%(Figure2+)s " % self.seq) + flowables[0].text
            if style == 'Appendix':
                self.seq.setFormat('appendix', "A")
                self.headerSectionText = "%(appendix+)s, " % self.seq + flowables[0].text
                flowables[0].frags[0].text = ("%(appendix)s. " % self.seq) + flowables[0].text
                self.seq.reset("Section", 1)
                self.seq.reset("Figure1")
                self.seq.reset("Figure2")
                
                

    def afterPage(self):
        if self.headerSectionText != None and self.canv._pageNumber > 1:
            self.canv.setFont("Lato-Bold", 14)
            self.canv.setFillColor(white)
            self.canv.drawString(self.leftMargin + 10, self.height + self.topMargin - 45, self.headerSectionText)

    def firstPageHeader(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(white)
        #canvas.drawImage("media/InstallationReport.png", doc.leftMargin, doc.height, width=doc.width, preserveAspectRatio=True)
        canvas.rect(doc.leftMargin, doc.height + doc.topMargin - 50, doc.width, 80, stroke=0, fill=1)
        canvas.drawImage("media/DDNLogoLandscape.png", doc.leftMargin + 2, doc.height + doc.topMargin - 50, width=120, height=80, preserveAspectRatio=True)
        canvas.setFont("Lato-Bold", 32)
        canvas.setFillColor(black)
        canvas.drawString(doc.leftMargin + 160, doc.height + doc.topMargin - 20, "INSTALLATION REPORT")
        canvas.drawImage("media/separator.png", doc.leftMargin, doc.height + doc.topMargin - 50, width=doc.width, height=4, preserveAspectRatio=False)        
        canvas.drawImage("media/DDN - Watermark.png", 0, -280, width=doc.width, preserveAspectRatio=True)
        canvas.restoreState()
    
    def header(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColorRGB(ParagraphStyles.ddnRed.red, ParagraphStyles.ddnRed.green, ParagraphStyles.ddnRed.blue)
        canvas.rect(doc.leftMargin, doc.height + doc.topMargin - 29, doc.width, 59, stroke=0, fill=1)
        canvas.setFont("Lato-Bold", 14)
        canvas.setFillColor(white)
        canvas.drawString(self.leftMargin + 10, self.height + self.topMargin + 10, "Installation Report")
        canvas.setFont("Lato", 11)
        canvas.drawString(self.leftMargin + 10, self.height + self.topMargin - 5, self.configData.getConfig().customer.company)
        canvas.drawString(self.leftMargin + 10, self.height + self.topMargin - 20, "%s, %s" % (date.today().strftime("%B"), date.today().year))
        canvas.setFillColor(black)
        canvas.rect(doc.leftMargin, doc.height + doc.topMargin - 50, doc.width, 20, stroke=0, fill=1)
        canvas.restoreState()
         
    def footer(self, canvas, doc):
        canvas.saveState()
        #canvas.setLineWidth(1)
        #canvas.setStrokeColor(ParagraphStyles.ddnGrey)
        #canvas.line(doc.leftMargin, doc.bottomMargin, doc.width + doc.rightMargin, doc.bottomMargin)
        canvas.drawImage("media/separator.png", doc.leftMargin, doc.bottomMargin, width=doc.width, preserveAspectRatio=True)                
        canvas.drawImage("media/DDNLogoLandscape.png", doc.leftMargin, 15, width=60, height=40, preserveAspectRatio=True)
        #canvas.setFillColorRGB(ParagraphStyles.ddnRed.red, ParagraphStyles.ddnRed.green, ParagraphStyles.ddnRed.blue)
        canvas.setFillColor(black)
        canvas.setFont("Lato-Bold", 8)
        canvas.drawRightString(doc.width + doc.rightMargin, doc.bottomMargin - 15, "www.ddn.com  |  +1-818-700-7801")
        canvas.setFont("Lato", 8)
        canvas.drawRightString(doc.width + doc.rightMargin, doc.bottomMargin - 25, "Copyright %s DataDirect Networks, Inc. All Rights Reserved" % (date.today().year)) 
        canvas.drawRightString(doc.width + doc.rightMargin, doc.bottomMargin - 35, "Page  |  %s" % (doc.page))
        canvas.restoreState()
        
    def arrangeTitle(self, story):
        story.append(NextPageTemplate("normalPage"))
        story.append(FrameBreak("textFrameFirstPage"))
        story.append(Spacer(1,50))
        story.append(Paragraph("""<para align=center>""" + self.configData.getConfig().general.title["1"] + """</para>""", ParagraphStyles.title_red))
        story.append(Spacer(1,15))
        story.append(Paragraph("""<para align=center>""" + self.configData.getConfig().general.title["2"] + """</para>""", ParagraphStyles.title_red))
        story.append(Spacer(1,15))
        story.append(Paragraph("""<para align=center>""" + self.configData.getConfig().general.title["3"] + """</para>""", ParagraphStyles.title_red))    
        story.append(Spacer(1,30))
        story.append(Paragraph("""<para align=center>-</para>""", ParagraphStyles.title))    
        story.append(Spacer(1,30))
        story.append(Paragraph("""<para align=center>""" + self.configData.getConfig().customer.company + """</para>""", ParagraphStyles.title_company))
        story.append(Spacer(1,15))
        story.append(Paragraph("""<para align=center>Date: %s, %s</para>""" % (date.today().strftime("%B"), date.today().year), ParagraphStyles.title_date))
        story.append(Spacer(1,100))
        
        if len(self.configData.getConfig().customer.logo.split(".")) > 1:
            story.append(Picture(self.configData.getConfigPath("/") + self.configData.getConfig().customer.logo, self, page=1))
        else:
            story.append(Paragraph("""<para align=center>""" + self.configData.getConfig().customer.logo + """</para>""", ParagraphStyles.title))
            
        story.append(FrameBreak("frame2"))
        story.append(Paragraph("""<para align=left><font face="Lato-Bold" color="#8D040A" size=11><left>Prepared for:</left></font></para>""", ParagraphStyles.styleN))
        story.append(Paragraph("""<para align=left>""" + self.configData.getConfig().customer.name + """</para>""", ParagraphStyles.title_info))
        story.append(Paragraph("""<para align=left>""" + self.configData.getConfig().customer.company + """</para>""", ParagraphStyles.title_info))
        story.append(Paragraph("""<para align=left>""" + self.configData.getConfig().customer.phone + """</para>""", ParagraphStyles.title_info))
        story.append(Paragraph("""<para align=left>""" + self.configData.getConfig().customer.email + """</para>""", ParagraphStyles.title_info))
        story.append(FrameBreak("frame3"))
        story.append(Paragraph("""<para align=right><font face="Lato-Bold" color="#8D040A" size=11><right>Prepared by:</right></font></para>""", ParagraphStyles.styleN))
        
        doc_creator = [c for c in self.configData.getConfig().ddn.team if c.doc_creator]
        
        if len(doc_creator) == 0:
            doc_creator = self.configData.getConfig().ddn.team[len(self.configData.getConfig().ddn.team) - 1]
            print("No doc creator selected. Assuming the last entry which is {}".format(doc_creator.name))
        
        else:
            doc_creator = doc_creator[0]
        
        if doc_creator:
            story.append(Paragraph("""<para align=right>""" + doc_creator.name + """</para>""", ParagraphStyles.title_info))
            story.append(Paragraph("""<para align=right>""" + doc_creator.role + """</para>""", ParagraphStyles.title_info))
            story.append(Paragraph("""<para align=right>""" + doc_creator.phone + """</para>""", ParagraphStyles.title_info))
            story.append(Paragraph("""<para align=right>""" + doc_creator.email + """</para>""", ParagraphStyles.title_info))
        story.append(PageBreak())
        story.append(Paragraph("Table of contents", ParagraphStyles.htoc))
        toc = TableOfContents()
        toc.dotsMinLevel=0
        toc.levelStyles = [ParagraphStyles.h1toc, ParagraphStyles.h2toc, ParagraphStyles.h3toc]
        story.append(toc)
        story.append(PageBreak()) 
        
class PreviewTemplate(DDNDocTemplate):
    
    def __init__(self, filename, config, **kw):
        DDNDocTemplate.__init__(self, filename, config)
        self.pageTemplates = [self.normalPage]