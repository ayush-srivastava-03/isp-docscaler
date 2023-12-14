'''
Created on 13 Feb 2019

@author: mwolf
'''
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth

class code(Flowable):
    
    def __init__(self, text, style, index="BOX"):
        Flowable.__init__(self)
        self.text = text
        self.style = style
        self.index = index
        self.padding = self.style.padding
        
    def prepareText(self):
        self.text = self.splitLines()
    
    def splitLines(self):
        text = [] 
        for t in self.text:
            text.extend(self.splitLine(t))
              
        return text
    
    def splitLine(self, text):
        if stringWidth(text, self.style.fontName, self.style.fontSize) > self.maxWidth:
            splittedLine = []
            delimiter = [" ",",","."]
            textWidth = stringWidth(text, self.style.fontName, self.style.fontSize)
            charWidth = stringWidth(text[:1], self.style.fontName, self.style.fontSize)
            
            #totalWidth = textWidth / charWidth              #number of chars
            maxTextWidth = int(self.maxWidth / charWidth)   #max allowed chars
            
            while textWidth > self.maxWidth:
                line = text[:maxTextWidth]
                
                #split the line based on a delimiter
                #had to choose a maximum search radius for the splitting of the lines
                for i in range(1, 36):        
                    if len([item for item in delimiter if line[len(line) - i:len(line) - i+1] == item]) == 1:
                        line = line[:len(line) - i+1]
                        break
                
                splittedLine.append(line)
                text = text[len(line):]
                textWidth = stringWidth(text, self.style.fontName, self.style.fontSize)
            
            splittedLine.append(text.rstrip())
            
            return splittedLine
        else:
            return [text.rstrip()]
      
    def wrap(self, availWidth, availHeight):
        """This will be called by the enclosing frame before objects
        are asked their size, drawn or whatever.  It returns the
        size actually used."""
        
        self.availWidth = availWidth
        self.availHeight = availHeight
        
        self.width = self.availWidth
        self.maxWidth = self.width - (2 * self.padding[0]) - (2 * self.style.borderWidth) - self.style.leftIndent
        
        self.prepareText()
        self.height = self.calcHeight(self.text)
        
        return (self.width, self.height)
    
    def split(self, availWidth, availHeight):
        """This will be called by more sophisticated frames when
        wrap fails. Stupid flowables should return []. Clever flowables
        should split themselves and return a list of flowables.
        If they decide that nothing useful can be fitted in the
        available space (e.g. if you have a table and not enough
        space for the first row), also return []"""
        if (self.height + self.calcHeight()) > self.availHeight:
            
            if self.availHeight < self.calcHeight() + 10:
                return []

            if self.index == "BOX":
                self.index = "TOP"
            
            lines = []
            for t in self.text:
                lines.append(t)
                
                if self.calcHeight(lines) >= self.availHeight:
                    lines.pop()
                    break
             
            if self.calcHeight(self.text[len(lines):]) < self._frame._aH:
                index = "BOTTOM"
            else:
                index = "MIDDLE"
                
            return [self.__class__(lines, self.style, self.index), self.__class__(self.text[len(lines):], self.style, index)]
    
    def calcHeight(self, text=[""]):
        textHeight = 0
        if self.style.leading == 0:
            textHeight = self.style.fontSize
        elif self.style.leading <= self.style.fontSize:
            textHeight = self.style.fontSize + ((len(text) - 1) * self.style.leading)
        else:
            textHeight = (len(text) * self.style.fontSize) + (len(text) * (self.style.leading - self.style.fontSize))
            
        if self.index == "BOTTOM":
            textHeight = textHeight + self.padding[1]
        
        return textHeight + (2 * self.padding[1]) + (2 * self.style.borderWidth)
    
    def drawBox(self):
        self.canv.setStrokeColor(self.style.borderColor)
        self.canv.setLineWidth(self.style.borderWidth)
        self.canv.setLineCap(1)
        
        if self.index == "TOP" or self.index == "BOX":
            self.canv.line(self.style.leftIndent, self.height, self.width, self.height) #TOP
        self.canv.line(self.style.leftIndent, self.height, self.style.leftIndent, 0)    #LEFT
        self.canv.line(self.width, self.height, self.width, 0)                          #RIGHT
        if self.index == "BOTTOM" or self.index == "BOX":
            self.canv.line(self.style.leftIndent, 0, self.width, 0)                     #BOTTOM
    
    def draw(self):
        self.canv.saveState()
        
        tx = self.canv.beginText(self.padding[0] + self.style.leftIndent, self.height - (self.style.fontSize - (self.style.fontSize/6)) - self.padding[1] + self.style.borderWidth)
        tx.setFont( self.style.fontName,
                    self.style.fontSize,
                    self.style.leading)
        for l in self.text:
            for sp in self.splitLine(l):
                tx.textLine(sp)
            
        self.canv.drawText(tx)
        self.drawBox()
        
        self.canv.restoreState()
