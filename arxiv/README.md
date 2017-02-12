# arXiv Autosum

For quick start we are using the [KDD Cup 2003 Dataset](http://www.cs.cornell.edu/projects/kddcup/datasets.html)

## Step 0

Download all papers in the hep-th portion of the arXiv until May 1, 2003 from KDD Cup 2003

```
python download_kdd2003.py
```

## Step 1

Parse all the citations.

### Usage

```
python build_cited_by.py
```

#### Input

```hep-th-citations.tar.gz``` can be download from [the citation graph of the hep-th portion](http://www.cs.cornell.edu/projects/kddcup/download/hep-th-citations.tar.gz)

#### Output

(output = article_id, citing_article_ids separated by comma)

[```hep-ph-cited-by.csv```](arxiv/hep-ph-cited-by.csv)

## Step 2

Then go over the cited articles in the arxiv database and collect all the sentences

(final output = article_id, article_title, key_value pairs of citations: citing_article_id, citing article_sentence_before_after_citation)

There are a few major citations styles in LaTeX sources (> 80%) should be parsed by the script.

### `\bibitem` and `\cite`

```
\bibitem{me:lK3}
P.~S. Aspinwall,
\newblock {\em K3 Surfaces and String Duality},
\newblock in C.~Esthimiou and B.~Greene, editors, ``Fields, Strings and
  Duality, TASI 1996'', pages 421--540, World Scientific, 1997,
\newblock hep-th/9611137.
```

```
The subject of $N=2$ compactifications is enormous and we will present
here only a rather biased set of highlights. These lectures will be
sometimes closely-related to a set of lectures I gave at TASI 3 years ago
\cite{me:lK3}. Having said that, the focus of these lectures differs
from the former and the set of topics covered is not identical.
I will however often refer to \cite{me:lK3} for details of certain subjects.
```

### `\lref`

```
\lref\dufflm{M.J.~Duff, J.T.~Liu and R.~Minasian, Nucl. Phys. 
{\bf B452} (1995) 261.}
```

```
In $D=9$ a one-loop calculation of the anomaly-generating function \lnsw\
gives a result similar to the one of the ten-dimensional type $IIA$
calculation \vafawit\ and is of the form $\int A_1 \wedge I_8(R),$ where 
$I_8(R)$ is  an eight-form polynomial in curvature \dufflm, and the vector
can be identified with $B_{\mu 9}$ in type $IIA$ and with the Kaluza-Klein 
gauge boson
```

### `\nref`

```
\nref\dlp{J.~Dai, R.~G.~Leigh and J.~Polchinski, ``New
Connections Between String Theories'', Mod. Phys. Lett. 
{\bf A4}, 2073 (1989);
```

```
We will be particularly interested in computing the
intersection forms \atrace\ and \btrace,
as we will be able to use them to
extract the charges and open string spectrum for a given brane.
The main advantage of considering these quantities over the charges themselves
is that they are canonically normalized, as already noted in \dlp.
```

### `\ref` with bracket and `\cite`

```
\REF{\rReid}{M.~Reid, Math.\ Ann.\ {\bf 278} (1987) 329.}
\REF{\rCDLS}{P.~Candelas, A.M.~Dale, C.A.~L\"utken, R.~Schimmrigk,\hfill\break
       \npb{298}~(1988)~493.}
```

```
It has been known for some time \cite{{\rReid,\rCDLS,\rRolling,\rAGM}} that the
moduli spaces of
some \cys\ meet along boundary components that correspond to certain singular
manifolds.
```

### Inline `\ref` and `\cite`

```
A semi-period is also the solution of
a generalized hypergeometric system of equations.
The periods are solutions of the Picard-Fuchs (PF) equations.
In the toric varietal approach,
differential equations are constructed based on
the points in the dual polyhedron and the generators of Mori cone
  ~\REF{\rBKK}{P.~Berglund, S.~Katz and  A.~Klemm,
    \npb{456} (1995) 153, hep-th/9506091.}
\cite{{\rBatyrev,\rHKTY,\rBKK}}.
```

```
In \rsmalldist, fundamental string instantons which wrap around holomorphic
 spheres
were used as a probe of two-cycle volumes within  a Calabi-Yau manifold.
This resulted in some interesting observations regarding the identification
of special points in and the overall structure of the quantum Calabi-Yau 
moduli space;
these results  played a role in 
\ref\rWittenMF{E. Witten, {\it Phase Transitions In M-Theory And F-Theory,}
Nucl. Phys. {\bf B471} (1996) 195}\  and \ref\rAspinwallOrb{P. Aspinwall, 
{\it Enhanced Gauge Symmetries and K3 Surfaces,}\ 
Phys. Lett. {\bf B357} (1995) 329 }, for instance.
```

```
In the language of \rsmalldist\ the algebraic
measure will flow to the sigma model measure, a feature
that has also played an important role in the phase structure
of $M$ and $F$-theories on Calabi-Yau manifolds
\rWittenMF.
```

The following are minority citation styles the are not support by the script yet.

* `\item` list and/or superscript
* Manually assigned number
* Reference to the external bibilography


### Usage

```
python autosum_arxiv.py
```

The output will be saved as `hep-th-cited-by-sentences.csv`. Please note that the script may take a few days to process all of 23k articles.

Please look at the sample output (first 100 articles) [hep-th-cited-by-sentences-sample.csv](arxiv/hep-th-cited-by-sentences-sample.csv)

