# arXiv Autosum

For quick start we are using the [KDD Cup 2003 Dataset](http://www.cs.cornell.edu/projects/kddcup/datasets.html)

## Step 1 Parse all the citations

(output = article_id, citing_article_ids separated by comma)

### Usage

```
python build_cited_by.py
```

#### Input

From [The citation graph of the hep-th portion](http://www.cs.cornell.edu/projects/kddcup/download/hep-th-citations.tar.gz)

```hep-th-citations.tar.gz```

#### Output

```hep-ph-cited-by.csv```

## Step 2 Then go over the cited articles in the arxiv database and collect all the sentences

(final output = article_id, article_title, key_value pairs of citations: citing_article_id, citing article_sentence_before_after_citation)
