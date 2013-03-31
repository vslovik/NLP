uthor__="Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ ="$March 30, 2013"

import sys, json
from collections import defaultdict

"""
Replace rare words in JSON-like represented parse trees.
"""


class Replacer:
    def __init__(self):
        self.counts = defaultdict(int)

    def count(self, tree):
        """
        Count the frequencies of non-terminals and rules in the tree.
        """
        if isinstance(tree, basestring): return

        if len(tree) == 3:
            self.count(tree[1])
            self.count(tree[2])
        elif len(tree) == 2:
            # It is a unary rule.
            word = tree[1]
            self.counts[word] += 1

    def rare(self):
        for word in self.counts.keys():
            if self.counts[word] > 4:
                del self.counts[word]
        #for word, count in self.counts.iteritems(): 
         #   print word, count


    def process_tree(self, tree):
        if len(tree) == 3:
            # Recursively count the children.
            self.process_tree(tree[1])
            self.process_tree(tree[2])
        elif len(tree) == 2:
            # It is a unary rule.
            word = tree[1]
            if self.counts[word] > 0:
                tree.pop()
                tree.append('_RARE_')


def main(parse_file):
    replacer = Replacer()
    for l in open(parse_file):
        t = json.loads(l)
        replacer.count(t)
    replacer.rare()
    for l in open(parse_file):
        t = json.loads(l)
        replacer.process_tree(t)
        print json.dumps(t)


def usage():
    print """
    python cfg.replace.rare.py [input_file] > [output_file]
        Read in a parse tree training input file and 
        output its content with rare words replaced with _RARE_.
    """

if __name__ == "__main__":

    if len(sys.argv)!=2: # Expect exactly one argument: the training data file
        usage()
        sys.exit(2)
    main(sys.argv[1])
