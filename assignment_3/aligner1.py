#! /usr/bin/python
# -*- coding: latin-1 -*-

__author__ = "Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ = "$April 21, 2013"

import sys
from collections import defaultdict
from numpy import *
from scipy.io import loadmat
import json


class Aligner():
    """
        Align words in the translation phrase to the words in the translated phrase
    """
    def __init__(self, en_filename, fr_filename):
        self.en_filename = en_filename
        self.fr_filename = fr_filename
        self.en_dict = defaultdict(int)
        self.fr_dict = defaultdict(int)
        self.tmatrix = defaultdict(float)

    def iterator(self):
        self.en_file = file(self.en_filename, 'r')
        self.fr_file = file(self.fr_filename, 'r')
        en_l = self.en_file.readline()
        fr_l = self.fr_file.readline()
        i = 0
        while en_l and fr_l:
            en_line = en_l.strip()
            fr_line = fr_l.strip()
            if en_line and fr_line:  # Nonempty line
                yield en_line, fr_line
            en_l = self.en_file.readline()
            fr_l = self.fr_file.readline()
            i += 1
        self.en_file.close()
        self.fr_file.close()

    def read_model(self, en_dict_file, fr_dict_file, tmatrix_file):
        en_dict_raw = json.load(open(en_dict_file))
        fr_dict_raw = json.load(open(fr_dict_file))
        for w in en_dict_raw:
            self.en_dict[w.encode('utf-8')] = en_dict_raw[w]
        for w in fr_dict_raw:
            self.fr_dict[w.encode('utf-8')] = fr_dict_raw[w]

        m_lil = loadmat(tmatrix_file)
        self.tmatrix = m_lil['tmatrix']

    def align(self, output):
        phrase = 1
        for en_line, fr_line in self.iterator():
            en_words = en_line.split(" ")
            fr_words = fr_line.split(" ")
            for f in xrange(len(fr_words)):
                m = self.tmatrix[self.en_dict["NULL"], self.fr_dict[fr_words[f]]]
                a = 0
                for e in xrange(len(en_words)):
                    if m < self.tmatrix[self.en_dict[en_words[e]], self.fr_dict[fr_words[f]]]:
                        m = self.tmatrix[self.en_dict[en_words[e]], self.fr_dict[fr_words[f]]]
                        a = e + 1
                output.write("%s %s %s\n" % (phrase, a, f + 1))
            phrase += 1


def main(en_filename, fr_filename):
    aligner = Aligner(en_filename, fr_filename)
    aligner.read_model('en_dict', 'fr_dict', 'tmatrix.mat')
    aligner.align(sys.stdout)


def usage():
    sys.stderr.write("""
    Usage: python aligner1.py [en phrase file] [transl phrase file] > [alignment file]
        Get IBM Model 1 from the training set.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)


main(sys.argv[1], sys.argv[2])
