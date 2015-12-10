#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import argparse
import logging
import csv
import re

from getpass import getpass
from glob import glob

import urllib2
import cookielib
from urllib import urlencode

from bs4 import BeautifulSoup
import pdfquery

reload(sys)
sys.setdefaultencoding("utf-8")

__version__ = '0.0.2'

USE_TMP = False    # Set True to use HTML in TMP_DIR
TMP_DIR = 'tmp'

LOG_FILE = 'scholar.log'

GOOGLE_SCHOLAR_URL = 'https://scholar.google.com'

DEF_SEARCH_AUTHOR = 'A Einstein'
DEF_SEARCH_QUERY = 'Can quantum-mechanical description of physical reality be considered complete?'
DEF_CITES_COUNT = 100

DEF_PDF_DIR = 'pdfs'
DEF_OUT_CSV = 'output.csv'

COOKIES_FILENAME = ".cookies"

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


class ScholarWebClient(object):
    """Google Scholar Web Client class
    """
    def __init__(self, args):
        """ Start up... """
        self.args = args
        self.cj = cookielib.MozillaCookieJar(COOKIES_FILENAME)
        if os.access(COOKIES_FILENAME, os.F_OK):
            self.cj.load()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-Agent', ('Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36')),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        ]
        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)

    def save(self):
        logging.debug("save cookies")
        self.cj.save()

    def is_signed_in(self, html=""):
        return (html.find('SignOutOptions') != -1)

    def start(self):
        """
        Handle start page
        """
        logging.info("Session start...")
        try:
            response = self.opener.open("https://accounts.google.com")
            text = response.read()
            if self.args.verbose:
                with open(self.tmp_path('start.html'), 'wb') as f:
                    f.write(text)
            if not self.is_signed_in(text):
                logging.info("Not signed in yet")
                soup = BeautifulSoup(text)
                form = soup.find_all('form', {'id': 'gaia_loginform'})
                self.auth_url = form[0]['action']
                params = {}
                for i in form[0].find_all('input'):
                    if 'name' in i.attrs:
                        if 'value' in i.attrs:
                            params[i['name']] = i['value']
                        else:
                            params[i['name']] = ""
                self.auth_params = params
            else:
                logging.info("Already signed in")
                return True
        except Exception as e:
            logging.error(e)
            return False
        return False

    def login(self):
        """
        Handle login.
        """
        logging.info("Login...")
        logging.info("Sending Email...")
        params = self.auth_params
        if 'Email' in params:
            params['Email'] = self.args.user
        else:
            logging.warn("Invalid sign in page")
            return False
        try:
            response = self.opener.open(self.auth_url, urlencode(params))
            text = response.read()
            soup = BeautifulSoup(text)
            form = soup.find_all('form', {'id': 'gaia_loginform'})
            self.auth_url = form[0]['action']
            params = {}
            for i in form[0].find_all('input'):
                if 'name' in i.attrs:
                    if 'value' in i.attrs:
                        params[i['name']] = i['value']
                    else:
                        params[i['name']] = ""
        except Exception as e:
            logging.error(e)
            return False

        logging.info("Sending password...")
        if 'Passwd' in params:
            params['Passwd'] = self.args.password
        else:
            return False
        try:
            response = self.opener.open(self.auth_url, urlencode(params))
            text = response.read()
            if self.args.verbose:
                with open(self.tmp_path('login.html'), 'wb') as f:
                    f.write(text)
            return self.is_signed_in(text)
        except Exception as e:
            logging.error(e)
        return False

    def tmp_path(self, path):
        return os.path.join(TMP_DIR, path)

    def query(self, query='', author=''):
        logging.info("Query...'{0!s}'".format(query))
        if USE_TMP and os.path.exists(self.tmp_path('query.html')):
            logging.info("Use temporary file...")
            with open(self.tmp_path('query.html'), 'rb') as f:
                text = f.read()
            return text
        url = GOOGLE_SCHOLAR_URL
        params = {
            'as_q': query,
            'as_epq': '',
            'as_oq': '',
            'as_eq': '',
            'as_occt': 'any',
            'as_sauthors': '"{0!s}"'.format(author),
            'as_publication': '',
            'as_ylo': '',
            'as_yhi': '',
            'btnG': '',
            'hl': 'en',
            'as_sdt': '0,5'
        }
        url += '/scholar?' + urlencode(params)
        logging.debug("Query URL: '{0!s}'".format(url))
        text = ''
        try:
            response = self.opener.open(url)
            text = response.read()
            if self.args.verbose:
                with open(self.tmp_path('query.html'), 'wb') as f:
                    f.write(text)
        except Exception as e:
            logging.error(e)
        return text

    def download(self, url, path):
        # Download the file from `url` and save it locally under `path`:
        logging.info("Download URL: '{0!s}'".format(url))
        try:
            response = self.opener.open(url, timeout=30)
            data = response.read()
            with open(path, 'wb') as out_file:
                logging.info("Save to: '{0!s}".format(path))
                out_file.write(data)
        except Exception as e:
            logging.error(e)

    def get_cited_by_url(self, html=''):
        soup = BeautifulSoup(html)
        url = ''
        rows = soup.find_all('div', {'class': 'gs_ri'})
        count = 0
        for r in rows:
            fls = r.find_all('div', {'class': 'gs_fl'})
            for f in fls:
                for l in f.find_all('a'):
                    txt = l.text.strip()
                    if txt.startswith('Cited by'):
                        m = re.match(r'.*\s(\d+)', txt)
                        if m:
                            count = int(m.group(1))
                        url = l['href']
                        # return first matched
                        return url, count
        return url, count

    def browse(self, url='', page=1):
        logging.info("Browse...")
        if USE_TMP and os.path.exists(self.tmp_path('page-{0:d}.html'.format(page))):
            logging.info("Use temporary file...")
            with open(self.tmp_path('page-{0:d}.html'.format(page)), 'rb') as f:
                text = f.read()
            return text
        url = GOOGLE_SCHOLAR_URL + url
        if page > 1:
            url += ('&start={0:d}'.format(((page - 1)*10)))
        logging.debug("Browse URL: '{0!s}'".format(url))
        text = ''
        try:
            response = self.opener.open(url)
            text = response.read()
            if self.args.verbose:
                with open(self.tmp_path('page-{0:d}.html'.format(page)), 'wb') as f:
                    f.write(text)
        except Exception as e:
            logging.error(e)
        return text

    def get_cites(self, html=''):
        i = 0
        soup = BeautifulSoup(html)
        rows = soup.find_all('div', {'class': 'gs_r'})
        cites = []
        for r in rows:
            i += 1
            logging.info("No: {0:d}".format(i))
            title = r.find('h3', class_='gs_rt')
            if title:
                if title.a:
                    title_url = title.a['href']
                else:
                    title_url = ''
                title_text = title.text.encode()
            else:
                title_text = ''
            authors = r.find('div', class_='gs_a')
            if authors:
                authors_text = authors.text.encode()
            else:
                authors_text = ''
            summary = r.find('div', class_='gs_rs')
            if summary:
                summary_text = summary.text.encode()
            else:
                summary_text = ''
            pdf_url = ''
            for l in r.find_all('div', {'class': 'gs_md_wp gs_ttss'}):
                for a in l.find_all('a'):
                    url = a['href']
                    # *** CHECK PDF ***
                    fls = a.find_all('span', {'class': 'gs_ctg2'})
                    for f in fls:
                        if f.text.find('[PDF]') != 1:
                            pdf_url = url
                            break
                        fls = r.find_all('div', {'class': 'gs_fl'})
            cited_by = 0
            for f in r.find_all('div', {'class': 'gs_fl'}):
                for l in f.find_all('a'):
                    txt = l.text.strip()
                    if txt.startswith('Cited by'):
                        m = re.match(r'.*\s(\d+)', txt)
                        if m:
                            cited_by = int(m.group(1))
                        cited_url = l['href']

            cites.append({'title': title_text,
                          'url': title_url,
                          'authors': authors_text,
                          'summary': summary_text,
                          'cited_by': cited_by,
                          'pdf_url': pdf_url
                          })
        return cites

    def is_robot_detected(self, html=''):
        return (html.find('Please show you&#39;re not a robot') != -1)


def test_pdf():
    for f in glob('*.pdf'):
        print f
        bn = os.path.basename(f)
        try:
            pdf = pdfquery.PDFQuery(f)
            pdf.load()
            pdf.tree.write("{0!s}.xml".format(bn), pretty_print=True, encoding="utf-8")
        except Exception as e:
            print e
            print "ERROR"


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--user', action='store', dest='user',
                        default='', help='Google account e-mail')
    parser.add_argument('-p', '--password', action='store', dest='password',
                        default='', help='Google account password')
    parser.add_argument('-a', '--author', action='store', dest='author',
                        default=DEF_SEARCH_AUTHOR,
                        help='Author to be filtered')
    parser.add_argument('-d', '--dir', action='store', dest='dir',
                        default=DEF_PDF_DIR,
                        help='Output directory for PDF files')
    parser.add_argument('-o', '--output', action='store', dest='output',
                        default=DEF_OUT_CSV, help='CSV output filename')
    parser.add_argument('-n', '--n-cites', type=int, action='store',
                        dest='n_cites', default=DEF_CITES_COUNT,
                        help='Number of cites to be download')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    parser.add_argument('keyword', help='Keyword to be search', nargs='+')

    results = parser.parse_args()
    return results

if __name__ == "__main__":
    args = get_args()
    if args.verbose:
        setup_logger(logging.DEBUG)
    else:
        setup_logger(logging.INFO)
    args.keywords = ' '.join(args.keyword)
    logging.debug("keywords = '{0!s}'".format(args.keywords))
    session = ScholarWebClient(args)
    signed_in = session.start()
    if not signed_in:
        if args.user == '':
            args.user = raw_input('Enter Google account (E-mail): ')
        if args.user != '' and args.password == '':
            args.password = getpass('Enter Google password: ')
        if args.user != '' and args.password != '':
            if session.login():
                logging.info("Signed in")
                # Save cookies for furture use.
                session.save()
            else:
                logging.warn("Cannot signed in continue in Guest mode")
        else:
            logging.warn("No Google E-mail or Password continue in Guest mode")
    if args.keywords == 'default':
        args.keywords = DEF_SEARCH_QUERY
    html = session.query(query=args.keywords, author=args.author)
    if session.is_robot_detected(html):
        logging.error("Google detected, we're a robot.")

    url, count = session.get_cited_by_url(html)
    logging.info("Total cited by {0:d}".format(count))
    n_cites = min(args.n_cites, count)
    all_cites = []
    page = 0
    n_pages = (n_cites - 1)/10 + 1
    while page < n_pages:
        page += 1
        logging.debug("Page = {0:d}".format(page))
        html = session.browse(url, page)
        if session.is_robot_detected(html):
            logging.error("Google detected, we're a robot.")
            break
        cites = session.get_cites(html)
        all_cites += cites
        time.sleep(1)

    all_cites = all_cites[:args.n_cites]
    if not os.path.exists(args.dir):
        logging.info("Create output directory")
        os.makedirs(args.dir)
    for n, c in enumerate(all_cites):
        pdf_url = c['pdf_url']
        if pdf_url != '':
            path = os.path.join(args.dir, '{0:d}.pdf'.format((n + 1)))
            c['pdf_path'] = path
            if os.path.exists(path):
                logging.info("Skip, '{0!s}' exists".format(path))
            else:
                logging.info("Download...'{0!s}'".format(path))
                # Download PDF files
                session.download(pdf_url, path)

    with open(args.output, 'wb') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title', 'authors',
                                'summary', 'cited_by', 'pdf_url', 'pdf_path'])
        writer.writeheader()
        writer.writerows(all_cites)
