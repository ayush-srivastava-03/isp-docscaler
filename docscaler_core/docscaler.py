#!/usr/bin/env python3
# encoding: utf-8

'''
Created on 20 Nov 2022

@author: mwolf
'''

import os
import sys
import optparse
import tempfile


sys.path.append(os.getcwd() + '/lib')
import preppy
from config import ConfigData
from datetime import date
from template import parser


__version__ = 0.2
__date__ = '2019-16-05'
__updated__ = '2022-11-02'

preview = False
previewTemplates = ""

def main(argv=None):

    program_name = os.path.basename(sys.argv[0])
    program_version = "%s" % __version__
    program_build_date = "%s" % __updated__

    program_version_string = "%s %s (%s)" % (program_name, program_version, program_build_date)
    program_longdesc = "Builds the Installation Report from provided logs\n"
    program_license = "Copyright {} DataDirect Networks".format(date.today().year)

    #Check for the libraries

    if argv is None:
        argv = sys.argv[1:]
        optparser = optparse.OptionParser(usage="usage: %prog -c <config_file>", version=program_version_string, epilog=program_license, description=program_longdesc, formatter=optparse.IndentedHelpFormatter())
        optparser.add_option("-c", dest="config", metavar="<file>", help="the config file to use")
        optparser.add_option("--tui", dest="tui", action="store_true", default=False, help="starts the TUI" )
        optparser.add_option("--ignore-check", dest="ignore", action="store_true", default=False, help="ignore host sanity checks" )


    # process options
    (opts, args) = optparser.parse_args()

    if opts.tui:
        from tui import tui
        t = tui()
        t.run()
        exit(0)

    if opts.config:
        try:
            configData = ConfigData(opts.config, True)

        except Exception as e:
            optparser.error("Failed to read the config file {0}: {1}".format(opts.config, e))
            sys.exit()
    elif not opts.config:
        optparser.error("Config file not defined. Can't build Installation Report.")
        sys.exit(1)

    '''Build Doc'''
    config = configData.getConfig()

    story = []
    if preview:
        previewFile = tempfile.NamedTemporaryFile(dir="html/temp", delete=False)
        doc = parser.PreviewTemplate(previewFile.name, config)
    else:
        doc = parser.DDNDocTemplate(configData.getConfigPath() + "/" + configData.getDocumentFilename(), configData)
        doc.arrangeTitle(story)

    templateParser = parser.TemplateParser(doc, configData)

    for template in config.templates:
    #    if config["templates"][template] not in previewTemplates:
    #        continue

        if os.path.isfile(configData.getConfigPath() + "/" + template + ".template"):
            mod = preppy.getModule(configData.getConfigPath() + "/" + template, source_extension=".template", savePyc=0)
        else:
            mod = preppy.getModule("templates/" + template, source_extension=".template", savePyc=0)
        templateParser.parse(mod.get(config), story)

    # remove the last pagebreak
    story.pop()

    print("\nBuilding document: " + configData.getConfigPath() + "/" + config.general.document_name)
    doc.multiBuild(story)

    print ("Done!")


if __name__ == '__main__':
    sys.exit(main())
