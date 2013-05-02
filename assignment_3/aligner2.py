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
        self.qjilm = defaultdict(list)

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

    def read_model(self, en_dict_file, fr_dict_file, qjilm_file, tmatrix_file):
        en_dict_raw = json.load(open(en_dict_file))
        fr_dict_raw = json.load(open(fr_dict_file))
        for w in en_dict_raw:
            self.en_dict[w.encode('utf-8')] = en_dict_raw[w]
        for w in fr_dict_raw:
            self.fr_dict[w.encode('utf-8')] = fr_dict_raw[w]
        m_lil = loadmat(tmatrix_file)
        self.tmatrix = m_lil['tmatrix']
        self.qjilm = load(qjilm_file)

    def align(self, output):
        phrase = 1
        for en_line, fr_line in self.iterator():
            en_words = en_line.split(" ")
            fr_words = fr_line.split(" ")
            l = len(en_words)
            m = len(fr_words)
            key = "%s_%s" % (l, m)
            for i in xrange(len(fr_words)):
                n = self.fr_dict[fr_words[i]]
                maxi = 0
                a = 0
                for j in xrange(len(en_words)):
                    k = self.en_dict[en_words[j]]
                    t = self.tmatrix[k, n]
                    q = self.qjilm[key][j][i]
                    val = q*t
                    if maxi < val:
                        maxi = val
                        a = j + 1
                output.write("%s %s %s\n" % (phrase, a, i + 1))
            phrase += 1


def main(en_filename, fr_filename):
    aligner = Aligner(en_filename, fr_filename)
    aligner.read_model('en_dict', 'fr_dict', 'qjilm.npz', 'tmatrix_ibm2.mat')
    aligner.align(sys.stdout)


def usage():
    sys.stderr.write("""
    Usage: python aligner.py [en phrase file] [transl phrase file] > [alignment file]
        Get IBM Model 1 from the training set.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)


main(sys.argv[1], sys.argv[2])
