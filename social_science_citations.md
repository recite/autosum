### Searching for Text Near Citations in Typical Social Science Articles

How the articles are cited varies very widely. Not only is there considerable variation in the citation format, where the citations are placed also varies widely. For instance, in some natural sciences journals citations are footnoted. 

Variation in location of citation is somewhat smaller if we limit ourselves to social science journals. In social science journals, citation abuts the point(s) being cited: "Authors (XYZ) show that moon is a satellite," or "Moon is a satellite (Authors XYZ)." Though [not always][testdata/13.pdf]. 

Ideally we would like a script that works for all citation formats. But doing so is a challenging task. For one, the domain is unknown. So we attempt to cover the prominent formats, not letting perfect be the enemy of good.  

#### Basic Patterns in Citation

**Number of authors**  

1. When there are 1 or 2 authors, citation generally takes the form:
  * (Author1_Last_Name Year) 
  * (Author1_Last_Name and Author2_Last_Name Year)
  * (Author1_Last_Name, and Author2_Last_Name Year)
  * (Author1_Last_Name and Author2_Last_Name, Year) 
  * (Author1_Last_Name & Author2_Last_Name Year)
  * (Author1_Last_Name & Author2_Last_Name, Year)
  * A comma may or may not separate list of authors, and list of authors and year
  * Bottom line: Regex for 1 or 2 author citation ignores commas, some extra spaces, treats "and" and "&" as the same

2. When there are 3 or more authors, as in the test data, citation generally takes the form:
  * (Author1_Last_Name, Author2_Last_Name, Author3_Last_Name, .... Year)
  * (Author1_Last_Name et al. Year)
  * (Author1_Last_Name et al., Year)
  * Again commas are optional. 
  * Bottom line: Regex for 3 or more author citation ignores commas, some extra spaces, treats "and" and "&" as the same, also looks for Author1_last_name et al., Year

**Parenthesis or Not**  

1. Part of the sentence:  
  * Citation generally comes at the end. And when it comes right before the period, it generally is in parenthesis.
  * Citation can be at the start of the sentence -- so right after a period -- and then it generally doesn't have parenthesis. 
  * Citation in the middle of the sentence 
    - citation before a comma will generally have parenthesis. 
    - otherwise it won't
  * Bottom line: Ignore parenthesis or a regex that looks for parenthesis when citation is before a period, comma or semi-colon. Otherwise not. 

2. Multiple citations:  
  * When there are multiple citations, the middle citations won't have parenthesis.

**What to harvest**  

* If citation is at the end of the sentence, harvest the sentence before it. Anything before the previous period. 
* If citation is at the start, harvest everything before the end of the sentence.
* If citation in between a sentence, harvest everything from start of the sentence till the citation or till the end of the sentence. 
* Ignore periods that come after Mr., Mrs. etc. for nicer sentence splitting. 
* Generally documents are well structured so won't go too long before a period but good to set a max. number of words. Say 100.