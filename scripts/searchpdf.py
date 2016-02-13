#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
import csv
import re

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO


__version__ = '0.0.1'

USE_TMP = False    # Set True to use text file in TMP_DIR
TMP_DIR = 'tmp'

LOG_FILE = 'searchpdf.log'

DEF_IN_CSV = 'output.csv'
DEF_OUT_CSV = 'search-output.csv'

def setup_logger(level=logging.DEBUG):
    """ Set up logging
    """
    logging.basicConfig(level=level,
                        format='%(asctime)s  %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=LOG_FILE,
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', action='store', dest='input',
                        default=DEF_IN_CSV, help='CSV input filename')
    parser.add_argument('-o', '--output', action='store', dest='output',
                        default=DEF_OUT_CSV, help='CSV output filename')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    parser.add_argument('regex', help='Regex to be search', nargs='+')

    results = parser.parse_args()
    return results


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    print(path)
    with  open(path, 'rb') as fp:
        parser = PDFParser(fp)

        doc = PDFDocument(caching=True)
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize('')

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        # Process each page contained in the document.

        for page in doc.get_pages():
            interpreter.process_page(page)

        text = retstr.getvalue()

    device.close()
    retstr.close()

    return text


def search_regex(text, exp):
    # join multiple lines
    lines = text.split('\n')
    text = ' '.join(lines)
    logging.info("Search...'{0!s}'".format(exp))
    regex = re.compile(exp, flags=(re.I))
    founds = []
    for m in regex.finditer(text):
        try:
            founds.append(m.group(1))
        except:
            # No such group
            founds.append(m.group(0))

    return founds

if __name__ == "__main__":
    args = get_args()
    if args.verbose:
        setup_logger(logging.DEBUG)
    else:
        setup_logger(logging.INFO)
    output = []
    with open(args.input, 'r') as f:
        reader = csv.DictReader(f)
        i = 0
        for r in reader:
            i += 1
            pdf_path = r['pdf_path']
            try:
                txtfile = os.path.join(TMP_DIR, "{0:d}.txt".format(i))
                if USE_TMP and os.path.exists(txtfile):
                    logging.info("Use temporary...'{0!s}'".format(txtfile))
                    with open(txtfile, 'rb') as f:
                        text = f.read()
                else:
                    logging.info("Extract text...'{0!s}'".format(pdf_path))
                    text = convert_pdf_to_txt(pdf_path)
                    with open(txtfile, 'wb') as f:
                        f.write(text.encode("utf-8"))
                founds = []
                for e in args.regex:
                    founds += search_regex(text, e)
                r['founds'] = '\n'.join(founds)
                r['status'] = 'OK'
            except Exception as e:
                logging.error(e)
                r['status'] = 'ERROR'
                pass
            output.append(r)

    logging.info("Save output to file...'{0!s}'".format(args.output))
    with open(args.output, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title', 'authors',
                                'summary', 'cited_by', 'pdf_url',
                                'pdf_path', 'founds', 'status'])
        writer.writeheader()
        writer.writerows(output)

    logging.info("Done!")
