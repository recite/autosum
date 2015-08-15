#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
import csv
import re

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

from bisect import bisect

import ftfy

reload(sys)
sys.setdefaultencoding("utf-8")

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
                        default=DEF_TXT_DIR, help='Extract to specific directory')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Force extract text file if exists')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    parser.add_argument('regex', help="Regex to filter citation (Authors/Year)", nargs='+')

    results = parser.parse_args()
    return results


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos,
                                  maxpages=maxpages, password=password,
                                  caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()

    return text


def split_sentences(text):
    """Returns split sentences list and index of splitting point

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
        \s+               # Split on whitespace between sentences.
        """, re.IGNORECASE | re.VERBOSE)
    sentenceList = sentenceEnders.split(text)
    st_index = [0]
    for s in sentenceEnders.finditer(text):
        st_index.append(s.start())
    return sentenceList, st_index


def citation_regex():
    author = "(?:[A-Z][_0-9A-Za-z'`-]+)"
    etal = "(?:et al.?)"
    additional = "(?:,? (?:(?:and |& )?" + author + "|" + etal + "))"
    year_num = "(?:19|20)[0-9][0-9]"
    page_num = "(?:, p.? [0-9]+)?"  # Always optional
    year = "(?:,? *"+year_num+page_num+"| *\("+year_num+page_num+"\))"
    regex = "(" + author + additional+"*" + year + ")"

    return re.compile(regex, flags=(re.I))


def search_citation(text, exp):
    lines = text.split('\n')
    text = ' '.join(lines)
    text = ' '.join(text.split())
    text = ftfy.fix_text(text.decode())
    logging.info("Search...'%s'" % exp)
    sentences, st_index = split_sentences(text)
    regex = citation_regex()
    founds = set()
    for m in regex.finditer(text):
        s = m.group(1)
        n = re.findall(exp, s, flags=(re.I))
        if n:
            a = m.start(1)
            idx = bisect(st_index, int(a))
            st = sentences[idx-1]
            #logging.debug("%s: '%s'" % (exp, st))
            founds.add(st)
    return founds


if __name__ == "__main__":
    args = get_args()
    if args.verbose:
        setup_logger(logging.DEBUG)
    else:
        setup_logger(logging.INFO)
    output = []

    if not os.path.exists(args.txt_dir):
        logging.info("Create text files directory... (%s)" % args.txt_dir)
        os.makedirs(args.txt_dir)
    else:
        logging.info("Current text files directory... (%s)" % args.txt_dir)

    with open(args.input, 'rb') as f:
        reader = csv.DictReader(f)
        i = 0
        for r in reader:
            i += 1
            pdf_path = r['pdf_path']
            try:
                txtfile = os.path.join(args.txt_dir, "%d.txt" % i)
                if not args.force and os.path.exists(txtfile):
                    logging.info("Use exists text file...'%s'" % txtfile)
                    with open(txtfile, 'rb') as f:
                        text = f.read()
                else:
                    logging.info("Extract text from PDF...'%s'" % pdf_path)
                    text = convert_pdf_to_txt(pdf_path)
                    with open(txtfile, 'wb') as f:
                        f.write(text)
                founds = set()
                for e in args.regex:
                    results = search_citation(text, e)
                    founds.update(results)
                    logging.info("Regex: '%s', Found: %d" % (e, len(results)))
                r['founds'] = '\n'.join(founds)
                r['status'] = 'OK'
            except Exception as e:
                logging.error(e)
                r['status'] = 'ERROR'
                pass
            output.append(r)

    logging.info("Save output to file...'%s'" % args.output)
    with open(args.output, 'wb') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title', 'authors',
                                'summary', 'cited_by', 'pdf_url',
                                'pdf_path', 'founds', 'status'])
        writer.writeheader()
        writer.writerows(output)

    logging.info("Done!")
