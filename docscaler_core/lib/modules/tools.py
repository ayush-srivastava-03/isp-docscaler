'''
Created on 24 Feb 2019

@author: mwolf
'''

from __future__ import division

int2byte = (lambda x: bytes((x,)))

def istext(filename):
    try:
        with open(filename, "r") as f:
            for l in f:
                return True
    except UnicodeDecodeError:
        return False
    
    
    # try:
    #     s = open(filename).read(512)
    # except Exception as e:
    #     return False
    #
    # text_characters = (b''.join(int2byte(i) for i in range(32, 127)) + b'\n\r\t\f\b')
    # #.extend(list("\n\r\t\b"))
    # test = dict.fromkeys(map(ord,text_characters.decode('ascii')), None)
    # if not s:
    #     # Empty files are considered text
    #     return True
    # if b'\x00' in s:
    #     # Files with null bytes are likely binary
    #     return False
    # # Get the non-text characters (maps a character to itself then
    # # use the 'remove' option to get rid of the text characters.)
    # t = s.translate(None, text_characters)
    # # If more than 30% non-text characters, then
    # # this is considered a binary file
    #
    # if float(len(t))/float(len(s)) <= 0.30:
    #     print(float(len(t))/float(len(s)))
    #     return False
    # return True