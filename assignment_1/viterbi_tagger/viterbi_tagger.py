#! /usr/bin/python

__author__="Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ ="$Mar 25, 2013"

import sys
from collections import defaultdict
import re

"""
Coursera.org course "Natural Language Processing" by Michael Collins,
Columbia University in the city of New York
NLP Programming Assignment 1: Hidden Markov Models
Viterbi Tagger
Read in 
the counts file 
the bioligical text file 
write text with all words tagged in stdout.
"""

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



def sentence_iterator(corpus_iterator):
    """
    Return an iterator object that yields one sentence at a time.
    Sentences are represented as lists of words.
    """
    current_sentence = [] #Buffer for the current sentence
    for l in corpus_iterator:
            if l==None:
                if current_sentence:  #Reached the end of a sentence
                    yield current_sentence
                    current_sentence = [] #Reset buffer
                else: # Got empty input stream
                    sys.stderr.write("WARNING: Got empty input file/stream.\n")
                    raise StopIteration
            else:
                current_sentence.append(l) #Add token to the buffer

    if current_sentence: # If the last line was blank, we're done
        yield current_sentence  #Otherwise when there is no more token
                                # in the stream return the last sentence.



class Viterbi(object):
    """
        Counts and stores coefficients alog iteration path
    """
    def __init__(self, sentence, tagger):
        self.tagger = tagger
        self.sentence = sentence
        self.pi = defaultdict(int)
        self.bp = defaultdict(int)


    def get_factor(self, q_args, e_args):
        q = self.get_q(q_args)
        e = self.get_e(e_args)
        return q*e

 
    def get_q(self, args):
        [w, u, v] = list(args)
        return self.tagger.ngram_counts[self.tagger.n-1][(w, u, v)]/self.tagger.ngram_counts[self.tagger.n-2][(w, u)]


    def get_e(self, args):
        [word, v] = list(args)
        return self.tagger.emission_counts[(word, v)]/self.tagger.ne_tag_counts[v]


    def filter_rare_word(self, word):
        if self.tagger.word_counts[word] >= 5:
            return word
        # Use rare word classes
        for [mark, regex] in self.tagger.rare_words_filter:
            if re.search(regex, word):
                return mark
        return '_RARE_'


    def count_step_coeff(self, step):
        word = self.filter_rare_word(self.sentence[step-1])
        if 1 == step:
            for v in self.tagger.all_states:
                self.pi[(step, '*', v)] = self.get_factor(('*', '*', v), (word, v))
        elif 2 == step:
            for v in self.tagger.all_states:
                for u in self.tagger.all_states:
                    self.pi[(step, u, v)] = self.pi[(step - 1,'*', u)]*self.get_factor(('*', u, v), (word, v))
        else:
            for v in self.tagger.all_states:
                for u in self.tagger.all_states:
                    arg_max = u
                    for w in self.tagger.all_states:
                        pi = self.pi[(step - 1, w, u)]*self.get_factor((w, u, v), (word, v))
                        if pi > self.pi[(step, u, v)]:
                            self.pi[(step, u, v)] = pi
                            self.bp[(step, u, v)] = w


    def count_coeff(self):
        n = len(self.sentence)
        for i in xrange(n):
            self.count_step_coeff(i+1)


    def make_tag_sequence(self):
        self.count_coeff()
        n = len(self.sentence)
        if 1 == n:
            max_val = 0
            for v in self.tagger.all_states:
                p = self.pi[(n, '*', v)]*self.get_q(('*', v, 'STOP'))
                if p > max_val:
                   max_val = p
                   arg_max = v
            if 0 == max_val:
                arg_max = v
            retun [arg_max]
        else:
            max_val = 0
            for u in self.tagger.all_states:
                for v in self.tagger.all_states:
                    p = self.pi[(n, u, v)]*self.get_q((u, v, 'STOP'))
                    if p > max_val:
                        max_val = p
                        tag_sequence = [u, v]
            if 0 == max_val:
                tag_sequence = [u, v]
            if 2 == n:
                return tag_sequence 

            for k in xrange(n-2, 0, -1):
                prev = self.bp[(k+2, tag_sequence[0], tag_sequence[1])]
                tag_sequence.insert(0, prev)
            return tag_sequence



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
        self.word_counts = defaultdict(int)
        self.ne_tag_counts = defaultdict(int)
        self.rare_words_filter = {}


    def set_rare_word_filter(self, filter):
        self.rare_words_filter = filter


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
                self.word_counts[word] += count
            elif parts[1].endswith("GRAM"):
                n = int(parts[1].replace("-GRAM",""))
                ngram = tuple(parts[2:])
                self.ngram_counts[n-1][ngram] = count


    def tag_sentence(self, sentence, output):
        viterbi = Viterbi(sentence, self)
        return viterbi.make_tag_sequence()


    def write_tags(self, iterator, output):
        k = 0
        for sentence in iterator:
            k += 1
            tag_sequence = self.tag_sentence(sentence, output)
            for i in xrange(len(sentence)):
                output.write('%s %s\n' % (sentence[i], tag_sequence[i]))
            output.write('\n');


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
    # Use rare word classes
    tagger.set_rare_word_filter([['_NUMERIC_', "[0-9]+"], ['_ALL_CAPITALS_', "^[A-Z]+$"], ['_LAST_CAPITAL_', "[A-Z]+$"]])
    # Read counts
    tagger.read_counts(corpus_iterator(counts_file), sys.stdout)
    # Tag 
    tagger.write_tags(sentence_iterator(corpus_iterator(gene_file)), sys.stdout)   
