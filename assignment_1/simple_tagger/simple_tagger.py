#! /usr/bin/python

__author__="Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ ="$Mar 25, 2013"

import sys
from collections import defaultdict

"""
Coursera.org course "Natural Language Processing" by Michael Collins,
Columbia University in the city of New York
NLP Programming Assignment 1: Hidden Markov Models
Simple Tagger
Read in 
the counts file 
the bioligical text file 
write text with all words tagged in stdout.
"""

def corpus_iterator(corpus_file):
    """
    Get an iterator object over the corpus file. The elements of the
    iterator contain sentence word. Blank lines, indicating
    sentence boundaries return None.
    """
    l = corpus_file.readline()
    while l:
        line = l.strip()
        if line: # Nonempty line
            yield line
        else: # Empty line
            yield None
        l = corpus_file.readline()


class Tagger(object):
    """
    Stores counts for n-grams and emissions. 
    """

    def __init__(self, n=3):
        assert n>=2, "Expecting n>=2."
        self.n = n
        self.emission_counts = defaultdict(int)
        self.ngram_counts = [defaultdict(int) for i in xrange(self.n)]
        self.all_states = set()
        self.ne_tag_counts = defaultdict(int)


    def read_counts(self, iterator, output):
        self.n = 3
        self.emission_counts = defaultdict(int)
        self.ngram_counts = [defaultdict(int) for i in xrange(self.n)]
        self.all_states = set()
        for line in iterator:
            parts = line.strip().split(" ")
            count = float(parts[0])
            if parts[1] == "WORDTAG":
                ne_tag = parts[2]
                word = parts[3]
                self.emission_counts[(word, ne_tag)] = count
                self.all_states.add(ne_tag)
                self.ne_tag_counts[ne_tag] += count
            elif parts[1].endswith("GRAM"):
                n = int(parts[1].replace("-GRAM",""))
                ngram = tuple(parts[2:])
                self.ngram_counts[n-1][ngram] = count
        #for tag in self.all_states:
        #    output.write('%s %s\n' % (tag, self.ne_tag_counts[tag]))


    def count_tag(self, word):
        count = 0
        c = 0
        rare = True
        for tag in self.all_states:
            if self.emission_counts[(word, tag)] > 0:
                rare = False
                c = self.emission_counts[(word, tag)]/self.ne_tag_counts[tag]
            if count < c:
                count = c
                ne_tag = tag
        if True == rare:
            return self.count_tag("_RARE_")
        return ne_tag


    def write_tags(self, iterator, output):
        for word in iterator:
            if word:
                output.write("%s %s\n" %(word, self.count_tag(word)))
            else:
                output.write("\n");


def usage():
    print """
    python tagger.py [counts_file] [text2label_file] > [output_file]
        Read in a gene tagged training input file and produce counts.
    """

if __name__ == "__main__":

    if len(sys.argv)!=3: # Expect exactly two arguments: the count file and the biological text file
        usage()
        sys.exit(2)

    try:
        counts_file = file(sys.argv[1],"r")
        gene_file   = file(sys.argv[2],"r")
    except IOError:
        sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % arg)
        sys.exit(1)

    # Initialize a simple gene tagger
    tagger = Tagger(3)
    # Read counts
    tagger.read_counts(corpus_iterator(counts_file), sys.stdout)
    # Tag 
    tagger.write_tags(corpus_iterator(gene_file), sys.stdout)   
