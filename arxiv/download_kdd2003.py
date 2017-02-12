# -*- coding: utf-8 -*-

import requests
import os
import urllib
import tarfile


def download_file(url, directory):
    local_filename = url.split('/')[-1]
    local_filename = urllib.unquote(local_filename).decode('utf-8')
    local_filename = directory + '/' + local_filename
    print local_filename
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename


if __name__ == "__main__":
    #target_dir = 'test'
    target_dir = 'kddcup2003'

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Download LaTex sources of all papers
    for year in range(1992, 2004):
        print("Download LaText sources for year %d..." % year)
        local_filename = download_file('http://www.cs.cornell.edu/projects/kddcup/download/hep-th-%d.tar.gz' % year, target_dir)
        print("Extracting...")
        tar = tarfile.open(local_filename)
        tar.extractall(target_dir)
        tar.close()

    # Download abstract
    print("Download abstract data...")
    download_file('http://www.cs.cornell.edu/projects/kddcup/download/hep-th-abs.tar.gz', target_dir)

    # Download citations graph
    print("Download citations graph...")
    download_file('http://www.cs.cornell.edu/projects/kddcup/download/hep-th-citations.tar.gz', target_dir)
