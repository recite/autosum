#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
import csv
import re

from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import BytesIO
import ftfy


__version__ = '0.0.1'


LOG_FILE = 'autosumpdf.log'

DEF_IN_CSV = 'output.csv'
DEF_OUT_CSV = 'autosum-output.csv'
DEF_TXT_DIR = 'txt'


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
    parser.add_argument('-t', '--text', action='store', dest='txt_dir',
                        default=DEF_TXT_DIR, help='extract to specific directory')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='force extract text file if exists')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-a1', '--author-1-lastname',action='store',help='1st author of citation',dest='author1',)
    parser.add_argument('-a2', '--author-2-lastname',action='store',help='2nd author of citation',dest='author2')
    parser.add_argument('-y', '--year',action='store',help='Year of publication',dest='year')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-r','--regex', action='store',help="specify custom regex to filter citations.", dest="regex")

    results = parser.parse_args()

    if results.author1 is None and results.regex is None:
        parser.error("You must specify at least an author (-a1), or a custom regexp (-r) to filter citations.")
        exit(-1)

    return results


def build_regexp_list(args):
    '''
    builds a list of regexps to be used for filtering citations using available
    information like first, second author and year (command line arguments -a1,
    -a2 and y) and /or the custom regexp (-r).
    '''
    exp_list = []

    if args.author1 is not None:
        if args.year is None:
            year = ''
            exp_list.append(args.author1 + "\set al\.")
        else:
            year = args.year
            exp_list.append(args.author1 + "\s{0,1}(et al\.){0,1}\,{0,1}\s{0,1}" + args.year)
        if args.author2 is not None:
                exp_list.append(args.author1 + "(\,){0,1}\s{0,1}(and|&){0,1}\s" + args.author2 + "\,{0,1}\s{0,1}" + year)

    if args.regex is not None: #custom regexp
        exp_list.append(args.regex)

    return exp_list

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = BytesIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    with open(path, 'rb') as fp:
        for page in PDFPage.get_pages(fp, pagenos,
                                      maxpages=maxpages, password=password,
                                      caching=caching, check_extractable=True):
            interpreter.process_page(page)

    text = retstr.getvalue()

    device.close()
    retstr.close()

    return text


def split_sentences(text):
    """Returns split sentences list

       Reference:
       http://stackoverflow.com/questions/8465335/a-regex-for-extracting-
              sentence-from-a-paragraph-in-python
    """
    sentenceEnders = re.compile(r"""
        # Split sentences on whitespace between them.
        (?:               # Group for two positive lookbehinds.
          (?<=[.!?])      # Either an end of sentence punct,
        | (?<=[.!?]['"])  # or end of sentence punct and quote.
        )                 # End group of two positive lookbehinds.
        (?<!  Mr\.   )    # Don't end sentence on "Mr."
        (?<!  Mrs\.  )    # Don't end sentence on "Mrs."
        (?<!  Jr\.   )    # Don't end sentence on "Jr."
        (?<!  Dr\.   )    # Don't end sentence on "Dr."
        (?<!  Prof\. )    # Don't end sentence on "Prof."
        (?<!  Sr\.   )    # Don't end sentence on "Sr."
        (?<!  Sen\.  )
        (?<!  Ms\.   )
        (?<!  Rep\.  )
        (?<!  Gov\.  )
        (?<!  et\ al\.  )
        (?<!  i\.e\.  )
        (?<!  U\.S\.  )
        (?<!  p\.  )      # Don't end sentence on "p." (page)
        \s+               # Split on whitespace between sentences.
        """, re.IGNORECASE | re.VERBOSE)
    sentenceList = sentenceEnders.split(text)
    return sentenceList


def search_citation(text, exp):
    '''Finds sentences around citations, where the regexp `exp matches'''

    text = text.decode('utf-8')
    lines = text.split('\n')
    text = ' '.join(lines)
    text = ' '.join(text.split())
    text = ftfy.fix_text(text)
    logging.info("Search...'{0!s}'".format(exp))

    sentences = split_sentences(text)
    regex = re.compile(exp, flags=(re.I))

    founds = set()
    for sent in sentences:
        if regex.search(sent):
            founds.add(sent)
    return founds


if __name__ == "__main__":
    args = get_args()
    regexp_list = build_regexp_list(args)
    if args.verbose:
        setup_logger(logging.DEBUG)
    else:
        setup_logger(logging.INFO)
    output = []

    if not os.path.exists(args.txt_dir):
        logging.info("Create text files directory... ({0!s})".format(args.txt_dir))
        os.makedirs(args.txt_dir)
    else:
        logging.info("Current text files directory... ({0!s})".format(args.txt_dir))

    with open(args.input, 'r',encoding="utf-8") as f:
        reader = csv.DictReader(f)
        i = 0
        for r in reader:
            i += 1
            pdf_path = r['pdf_path']
            try:
                txtfile = os.path.join(args.txt_dir, "{0:d}.txt".format(i))
                if not args.force and os.path.exists(txtfile):
                    logging.info("Use existing text file...'{0!s}'".format(txtfile))
                    with open(txtfile, 'rb') as f:
                        text = f.read()
                else:
                    logging.info("Extract text from PDF...'{0!s}'".format(pdf_path))
                    text = convert_pdf_to_txt(pdf_path)
                    with open(txtfile, 'wb') as f:
                        f.write(text)
                founds = set()
                for regexp in regexp_list:
                    results = search_citation(text, regexp)
                    founds.update(results)
                    logging.info("Regex: '{0!s}', Found: {1:d}".format(regexp, len(results)))
                r['founds'] = '\n'.join(founds)
                r['status'] = 'OK'
            except Exception as e:
                logging.error(e)
                r['status'] = 'ERROR'
                pass
            output.append(r)

    logging.info("Save output to file...'{0!s}'".format(args.output))
    with open(args.output, 'w',encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title', 'authors',
                                'summary', 'cited_by', 'pdf_url',
                                'pdf_path', 'founds', 'status'])
        writer.writeheader()
        writer.writerows(output)

    logging.info("Done!")
