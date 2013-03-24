__author__="Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ ="$Mar 23, 2013"

import sys
from collections import defaultdict
import re

"""
We need to predict emission probabilities for words in the test data
that do not occur in the traning data. One simple approach is to map
infrequent words in the training data to a common class and to treat
unseen words as members of this class. Replace infrequent words 
(Count(x) < 5) in the original training data file with a common 
symbol _RARE_.

HMM taggers can be improved by grouping words into informative word
classes rather than just into a single class of rare words. Here 
four rare word classes are implemented: Numeric, All Capital, Last
Capital and Rare. 
"""

def corpus_iterator(corpus_file):
    """
    Get an iterator object over the corpus file. The elements of the
    iterator contain word. Blank lines, indicating
    sentence boundaries return None.
    """
    l = corpus_file.readline()
    while l:
        line = l.strip()
        if line: # Nonempty line
            # Extract information from line.
            # Each line has the format
            # word ne_tag
            fields = line.split(" ")
            ne_tag = fields[-1]
            word = " ".join(fields[:-1])
            yield (word, ne_tag)
        else: # Empty line
            yield (None, None)
        l = corpus_file.readline()


class Replacer(object):
    """
    Find rare words in train corpus. 
    """

    def __init__(self):
        self.counts = defaultdict(int)
        self.rare_words_filter = {}

    def set_rare_word_filter(self, filter):
        self.rare_words_filter = filter

    def word_count(self, corpus_file, output):
        iterator = corpus_iterator(corpus_file)
        for word, ne_tag in iterator:
            if word:
                self.counts[word] += 1
        for word in self.counts.keys():
            if self.counts[word] >= 5:
                del self.counts[word]
        #for word in self.counts:
         #   output.write('%s %s\n' %(word, self.counts[word]))

    def filter_rare_word(self, word):
        if self.counts[word] == 0:
            return word
        # Use rare word classes
        for [mark, regex] in self.rare_words_filter:
            if re.search(regex, word):
                return mark
        return '_RARE_'
	
    def replace_rare(self, corpus_file, output):
        iterator = corpus_iterator(corpus_file)
        for word, ne_tag in iterator:
            if word is None:
                output.write('\n');
            else:
                output.write('%s %s\n' %(self.filter_rare_word(word), ne_tag))

def usage():
    print """
    python replace_rare.py [input_file] > [output_file]
        Read in a gene tagged training input file and 
        output its content with rare words replaced with _RARE_.
    """

if __name__ == "__main__":

    if len(sys.argv)!=2: # Expect exactly one argument: the training data file
        usage()
        sys.exit(2)

    try:
        input1 = file(sys.argv[1],"r")
        input2 = file(sys.argv[1],"r")
    except IOError:
        sys.stderr.write("ERROR: Cannot read inputfile %s.\n" % arg)
        sys.exit(1)

    # Initialize a counter
    replacer = Replacer()
    # Use rare word classes
    replacer.set_rare_word_filter([['_NUMERIC_' , "[0-9]+"], ['_ALL_CAPITALS_' , "^[A-Z]+$"], ['_LAST_CAPITAL_' , "[A-Z]+$"]])
    # Collect counts
    replacer.word_count(input1, sys.stdout)
    # Replace rare words
    replacer.replace_rare(input2, sys.stdout)

