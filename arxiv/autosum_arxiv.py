# -*- coding: utf-8 -*-

import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import regex
from pprint import pprint
from pylatexenc.latex2text import latex2text
import tarfile


def get_source(aid, fromtar=False):
    year = int(aid[:2])
    if year < 17:
        year += 2000
    else:
        year += 1900
    try:
        if fromtar:
            with tarfile.open("./kddcup2003/hep-th-%d.tar.gz" % year, "r:gz") as t:
                for m in t.getmembers():
                    if m.name.find(aid) != -1:
                        return t.extractfile(m).read()
        else:
            with open('./kddcup2003/%d/%s' % (year, aid)) as f:
                return f.read()
    except Exception as e:
        print("ERROR: text not found for %d" % aid)
        return ''


def clean_line(txt):
    # join multiple lines
    txt = txt.replace('\n', ' ')
    # remove multiple spaces
    txt = ' '.join(txt.split())
    return txt


ARXIV_BASE_URL = 'https://arxiv.org/abs/hep-th/'


def get_arxiv_meta(aid):
    title = ''
    authors = []
    jref = ''
    r = requests.get(ARXIV_BASE_URL + aid)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        h1 = soup.find('h1', {'class': 'title'})
        try:
            title = clean_line(h1.text.encode('utf-8').replace('Title:', ''))
        except Exception as e:
            print(e)
        div = soup.find('div', {'class': 'authors'})
        try:
            for a in div.find_all('a'):
                authors.append(clean_line(a.text.encode('utf-8')))
        except Exception as e:
            print(e)
        td = soup.find('td', {'class': 'jref'})
        try:
            jref = clean_line(td.text.encode('utf-8'))
        except Exception as e:
            print(e)

    return title, authors, jref


def get_arxiv_meta_archive(aid):
    title = ''
    authors = []
    jref = ''
    txt = ''
    with tarfile.open("./kddcup2003/hep-th-abs.tar.gz", "r:gz") as t:
        for m in t.getmembers():
            if m.name.find(aid) != -1:
                txt = t.extractfile(m).read()
                break
    for m in regex.finditer(r'Title:\s+(.*)(?=Author)', txt, regex.S):
        title = clean_line(m.group(1))
        break
    for m in regex.finditer(r'Authors?:\s+(.*)(?=Comment)', txt, regex.S):
        a = clean_line(m.group(1))
        authors = regex.split(r'(?:,\s*(?:and\s+)?|\s+and\s+)', a)
        break
    for m in regex.finditer(r'Journal-ref:\s+(.*?)(?=\\\\)', txt, regex.S):
        jref = clean_line(m.group(1))
        break

    return title, authors, jref


def split_sentences(text):
    """Returns split sentences list
       Reference:
       http://stackoverflow.com/questions/8465335/a-regex-for-extracting-
              sentence-from-a-paragraph-in-python
    """
    sentenceEnders = regex.compile(r"""
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
        """, regex.IGNORECASE | regex.VERBOSE)
    sentenceList = sentenceEnders.split(text)
    return sentenceList


def search_citation(sentences, exp):
    '''Finds sentences around citations, where the regexp `exp matches'''
    print("Search...'{0!s}'".format(exp))

    rx = regex.compile(exp, flags=(regex.I))

    founds = set()
    for sent in sentences:
        if rx.search(sent):
            founds.add(sent)
    return founds


def search_citing_sentences(aid, txt, match):
    lines = txt.split('\n')
    txt = ' '.join(lines)
    txt = ' '.join(txt.split())
    sentences = split_sentences(txt)
    founds = set()
    for r in match.keys():
        if r:
            regexp_list = [regex.escape('\cite%s' % r),
                           regex.escape('\\refs{%s}' % r),
                           r'(?<!(bibitem|lref).*?)' + regex.escape('%s' % r)]
            print aid, r
            for regexp in regexp_list:
                results = search_citation(sentences, regexp)
                founds.update(results)
                print("Regex: '{0!s}', Found: {1:d}".format(regexp, len(results)))
                if len(results):
                    break
    print("_" * 50)
    return founds


def autosum_arxiv_by_id(a):
    global xdf

    output = []

    txt = get_source(a)
    title, authors, jref = get_arxiv_meta_archive(a)
    print("Title: %s" % title)
    print("Authors: %s" % ' | '.join(authors))
    print("Journal ref: %s" % jref)
    for c in xdf[xdf.article_id == a]['citing_article_ids']:
        count = 0
        n = 0
        for d in c.split(';'):
            n += 1
            txt = get_source(d)
            found = {}
            for m in regex.finditer(r'\\b?bibitem(\[.*?\])?(\{.*?\})(.*?)(:?(?=\\bibitem.*?\{)|(?=\\end))', txt, flags=regex.S):
                #break
                if m.group(1) is not None:
                    mlabel1 = m.group(1).strip()
                else:
                    mlabel1 = ''
                mlabel2 = m.group(2).strip()
                mtxt = m.group(3).strip()
                if mlabel2 != '{}':
                    mlabel = mlabel2
                else:
                    mlabel = mlabel1
                #print d, mlabel, len(mtxt)
                #print('_'*50)
                if mlabel not in found:
                    found[mlabel] = mtxt
                else:
                    #print d, mlabel, len(mtxt)
                    pass
            for result in regex.finditer(r'''\\[ln]?refs?(?:con)?(\\.*?)
            (?<rec> #capturing group rec
             \{ #open parenthesis
             (?: #non-capturing group
              [^{}]++ #anyting but parenthesis one or more times without backtracking
              | #or
               (?&rec) #recursive substitute of group rec
             )*
             \} #close parenthesis
            )
            ''', txt, flags=regex.VERBOSE|regex.I):
                mlabel = result.group(1)
                mtxt = result.captures('rec')[-1][1:-1]
                #print d, mlabel, len(mtxt)
                #print('_'*50)
                if mlabel not in found:
                    found[mlabel] = mtxt
                else:
                    #print d, mlabel, len(mtxt)
                    pass
                #break
            for result in regex.finditer(r'''\\[ln]?refs?(?:con)?(\{\\.*?\})
            (?<rec> #capturing group rec
             \{ #open parenthesis
             (?: #non-capturing group
              [^{}]++ #anyting but parenthesis one or more times without backtracking
              | #or
               (?&rec) #recursive substitute of group rec
             )*
             \} #close parenthesis
            )
            ''', txt, flags=regex.VERBOSE|regex.I):
                mlabel = result.group(1)
                mtxt = result.captures('rec')[-1][1:-1]
                #print d, mlabel, len(mtxt)
                #print('_'*50)
                if mlabel not in found:
                    found[mlabel] = mtxt
                else:
                    #print d, mlabel, len(mtxt)
                    pass
                #break
            newfound = {}
            for c in found:
                try:
                    t = latex2text(found[c])
                except:
                    t = found[c]
                t = clean_line(t)
                newfound[c] = t
            found = newfound
            #pprint(newfound)
            #print('_'*80)
            match = {}
            for c in found:
                # match with arXiv's article ID
                if found[c].find(a) != -1:
                    match[c] = found[c]
                    count += 1
                    #pprint(match)
                    #print("_"*80)
                    break
                # match with Journal Reference
                if len(jref) and found[c].find(jref) != -1:
                    match[c] = found[c]
                    count += 1
                    #pprint(match)
                    #print("_"*80)
                    break
                # match with Title
                if len(title) and found[c].find(title) != -1:
                    match[c] = found[c]
                    count += 1
                    #pprint(match)
                    #print("_"*80)
                    break
                # match with all authors
                if False:
                    if len(authors):
                        m = 0
                        for at in authors:
                            if found[c].find(at) != -1:
                                m += 1
                            else:
                                break
                        if m == len(authors):
                            count += 1
                            match[c] = found[c]
                            #pprint(match)
                            #print("_"*80)
                            break
                        else:
                            # strip all spaces
                            m = 0
                            for at in authors:
                                if found[c].replace(' ', '').find(at.replace(' ', '')) != -1:
                                    m += 1
                                else:
                                    break
                            if m == len(authors):
                                count += 1
                                match[c] = found[c]
                                #pprint(match)
                                #print("_"*80)
                                break
            #pprint(match)
            #print("_"*80)
            sentences = search_citing_sentences(d, txt, match)
            for s in sentences:
                output.append([a, title, d, s])

    print("%s: %d/%d" % (a, count, n))
    print("=" * 80)

    return output


def autosum_arxiv_init():
    global xdf

    xdf = pd.read_csv('hep-th-cited-by.csv', converters={'article_id': str})


if __name__ == "__main__":

    autosum_arxiv_init()

    f = open('hep-th-cited-by-sentences.csv', 'wb')
    writer = csv.writer(f)
    writer.writerow(['article_id', 'article_title', 'citing_article_id',
                     'citing_article_sentence'])
    try:
        for a in xdf.article_id.unique():
            output = autosum_arxiv_by_id(a)
            for o in output:
                writer.writerow(o)
    finally:
        f.close()
