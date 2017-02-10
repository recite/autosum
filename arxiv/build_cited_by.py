import pandas as pd
import tarfile


if __name__ == "__main__":

    with tarfile.open("hep-th-citations.tar.gz", "r:gz") as t:
        for m in t.getmembers():
            f = t.extractfile(m)
            df = pd.read_csv(f, delim_whitespace=True,
                             header=None, names=['from', 'to'])
            break

    out = []
    for c in df.to.unique():
        cited = []
        for a in df[df.to == c]['from'].unique():
            cited.append('%07d' % a)
        out.append(['%07d' % c, ';'.join(cited)])

    xdf = pd.DataFrame(out)

    xdf.columns = ['article_id', 'citing_article_ids']
    xdf.to_csv('hep-ph-cited-by.csv', index=False)
