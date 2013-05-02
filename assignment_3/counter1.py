#! /usr/bin/python
# -*- coding: latin-1 -*-

__author__ = "Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ = "$April 21, 2013"

import sys
from collections import defaultdict
from numpy import *
from scipy.sparse import lil_matrix
from time import gmtime, strftime
from scipy.io import savemat
import json
import itertools


class Counter():
    """
        Count parameters for IBM Model 1 on training corpus
    """
    def __init__(self, en_filename, fr_filename):
        self.en_filename = en_filename
        self.fr_filename = fr_filename
        self.en_dict = defaultdict(int)
        self.fr_dict = defaultdict(int)
        self.tmatrix = defaultdict(float)
        self.ce = defaultdict(float)
        self.cef = defaultdict(float)

    def iterator(self):
        self.en_file = file(self.en_filename, 'r')
        self.fr_file = file(self.fr_filename, 'r')
        en_l = self.en_file.readline()
        fr_l = self.fr_file.readline()
        while en_l and fr_l:
            en_line = en_l.strip()
            fr_line = fr_l.strip()
            if en_line and fr_line:  # Nonempty line
                yield en_line, fr_line 
            en_l = self.en_file.readline()
            fr_l = self.fr_file.readline()
        self.en_file.close()
        self.fr_file.close()

    def initialize(self):
        words = {}
        for en_line, fr_line in self.iterator():
            en_words = en_line.split(" ")
            fr_words = fr_line.split(" ")
            if "NULL" in words:
                words["NULL"] = words["NULL"].union(set(fr_words))
            else:
                words["NULL"] = set(fr_words)
            for en_word in en_words:
                if en_word in words:
                    words[en_word] = words[en_word].union(set(fr_words))
                else:
                    words[en_word] = set(fr_words)
        self.tmatrix = lil_matrix((len(words.keys()), len(words["NULL"])))
        self.cef = lil_matrix((len(words.keys()), len(words["NULL"])))
        i = 0
        for word in words["NULL"]:
            self.fr_dict[word] = i
            i += 1
        i = 0
        for en_word, value in words.iteritems():
            self.en_dict[en_word] = i
            if len(value):
                for fr_word in value:
                    self.tmatrix[i, self.fr_dict[fr_word]] = pow(len(value), -1) 
            i += 1
        del words

    def iterate(self, n):
        for i in xrange(n):
            print i, strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
            for en_line, fr_line in self.iterator():
                en_words = en_line.split(" ")
                fr_words = fr_line.split(" ")
                for fr_word in fr_words:
                    s = 0
                    for en_word in en_words:
                        s = s + self.tmatrix[self.en_dict[en_word], self.fr_dict[fr_word]]
                    for en_word in en_words:
                        k = self.en_dict[en_word]
                        m = self.fr_dict[fr_word] 
                        delta = self.tmatrix[k, m]*pow(s, -1)
                        self.cef[k, m] += delta
                        self.ce[k] += delta
            cx = self.cef.tocoo()
            for i, j, v in itertools.izip(cx.row, cx.col, cx.data):
                self.tmatrix[i, j] = v*pow(self.ce[i], -1)
            del cx


def main(en_filename, fr_filename):
    print strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
    counter = Counter(en_filename, fr_filename)
    counter.initialize()
    counter.iterate(5)
    json.dump(counter.en_dict, open('en_dict', 'wb'))
    json.dump(counter.fr_dict, open('fr_dict', 'wb'))
    json.dump(counter.ce, open('ce', 'wb'))
    savemat('tmatrix.mat', {'tmatrix': counter.tmatrix})
    savemat('cef.mat', {'cef': counter.cef})


def usage():
    sys.stderr.write("""
    Usage: python counter1.py [en phrase training file] [transl phrase training file] > [IBM Model 1 params matrix]
        Get IBM Model 1 from the training set.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)


main(sys.argv[1], sys.argv[2])
