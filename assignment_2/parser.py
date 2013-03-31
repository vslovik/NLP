#! /usr/bin/python

__author__="Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ ="$Mar 31, 2013"

import sys, json
from collections import defaultdict

def corpus_iterator(corpus_file):
    """
    Get an iterator object over the corpus file. The elements of the
    iterator contain word to be tagged. Blank lines, indicating
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


class Cky():
    """
        Parse sentence into tree
    """
    def __init__(self, sentence, parser):
        self.parser = parser
        self.words = sentence.strip().split(" ")
        self.pi = {}
        self.bp = {}

    def get_uq(self, args):
        [X, w] = list(args)
        return float(self.parser.Uq[(X,w)])/float(self.parser.N_counts[X])

    def get_bq(self, args):
        [X, Y, Z] = list(args)
        return float(self.parser.Bq[(X,Y,Z)])/float(self.parser.N_counts[X])

    def filter_rare_word(self, word):
        if self.parser.word_counts[word] >= 5:
            return word
        return '_RARE_'

    def count_arg_max(self, i, j):
        for (X, Y, Z) in self.parser.Bq:
            for s in xrange(i,j):
                if (i, s, Y) in self.pi and (s+1, j, Z) in self.pi:
                    pi = self.get_bq((X, Y, Z))*self.pi[(i, s, Y)]*self.pi[(s+1, j, Z)]
                    if (i, j, X) not in self.pi or pi > self.pi[(i, j, X)] :
                        self.pi[(i, j, X)] = pi
                        self.bp[(i, j, X)] = (Y, Z, s)


    def count_coeff(self):
        n = len(self.words)
        for i in xrange(n):
            word = self.filter_rare_word(self.words[i])
            for (X, w) in self.parser.Uq:
                if word == w:
                    value = self.get_uq((X, word))
                    if value > 0:
                        self.pi[(i+1,i+1,X)] = value

        for l in xrange(1, n):
            for i in xrange(1, n-l+1):
                self.count_arg_max(i, i+l);

    def form_tree(self, tpl):
        [i, j, X] = list(tpl)
        if i == j :
            return [X, self.words[i-1]]
        else:
            [Y, Z, s] = list(self.bp[tpl])
            return [X, self.form_tree((i, s, Y)), self.form_tree((s+1, j, Z))]

       

class Parser():
    """
    Stores counts for n-grams and emissions. 
    """

    def __init__(self):
        self.Uq = defaultdict(int)
        self.Bq = defaultdict(int)
        self.N_counts = defaultdict(int)
        self.word_counts = defaultdict(int)


    def read_counts(self, iterator):
        for line in iterator:
            parts = line.strip().split(" ")
            count = int(parts[0])
            if parts[1] == "NONTERMINAL":
                symbol = parts[2]
                self.N_counts[symbol] += count
            elif parts[1] == "UNARYRULE":
                symbol = parts[2]
                word = parts[3]
                self.Uq[(symbol, word)] += count
                self.word_counts[word] += count
            elif parts[1] == "BINARYRULE":
                ngram = tuple(parts[2:])
                self.Bq[ngram] = count


    def parse(self, s):
        cky = Cky(s, self)
        cky.count_coeff()
        print json.dumps(cky.form_tree((1, len(cky.words), "SBARQ")))


    def parse_corpus(self, iterator):
        for s in iterator:
            self.parse(s)

def main(counts_file, sentences_file):
    parser = Parser()
    parser.read_counts(corpus_iterator(counts_file))
    #print len(parser.N_counts)
    #print parser.word_counts
    #print parser.Uq
    #print len(parser.Bq)
    parser.parse_corpus(corpus_iterator(sentences_file))


def usage():
    sys.stderr.write("""
    Usage: python parser.py [counts_file] [sentense file] > [parse tree file]
        Parse sentences into trees.\n""")

if __name__ == "__main__":
  if len(sys.argv) != 3:
    usage()
    sys.exit(1)

try:
    counts_file = file(sys.argv[1],"r")
    sentences_file   = file(sys.argv[2],"r")
except IOError:
    sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % arg)
    sys.exit(1)

main(counts_file, sentences_file)

