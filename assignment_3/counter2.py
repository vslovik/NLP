#! /usr/bin/python
# -*- coding: latin-1 -*-
__author__ = "Valeriya Slovikovskaya <vslovik@gmail.com>"
__date__ = "$April 21, 2013"
import sys
from numpy import *
from scipy.sparse import lil_matrix
from time import gmtime, strftime
from scipy.io import loadmat, savemat
import json
import itertools


class Counter():
    """
        Count parameters for IBM Model 2 on training corpus
    """
    def __init__(self, en_filename, fr_filename, en_dict_file, fr_dict_file, cef_file, ce_file, tmatrix_file):
        # for iterations
        self.en_filename = en_filename
        self.fr_filename = fr_filename
        self.tmatrix_file = tmatrix_file
        self.cef_file = cef_file
        self.ce_file = ce_file

        # dicts
        self.en_dict = {}
        self.fr_dict = {}

        # t
        self.ce = {}

        # q
        self.qjilm = {}
        self.cjilm = {}
        self.cilm = {}

        # read dict
        en_dict_raw = json.load(open(en_dict_file))
        fr_dict_raw = json.load(open(fr_dict_file))
        for w in en_dict_raw:
            self.en_dict[w.encode('utf-8')] = en_dict_raw[w]
        del en_dict_raw
        for w in fr_dict_raw:
            self.fr_dict[w.encode('utf-8')] = fr_dict_raw[w]
        del fr_dict_raw

        # read t
        self.tmatrix = lil_matrix((len(self.en_dict), len(self.fr_dict)))
        self.cef = lil_matrix((len(self.en_dict), len(self.fr_dict)))
        self.read_t()
        self.read_c()
        # read q
        self.init_q()

    def read_t(self):
        m_lil = loadmat(self.tmatrix_file)
        self.tmatrix = m_lil['tmatrix']

    def read_c(self):
        print 'c', strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
        ce_raw = json.load(open(self.ce_file))
        for j in ce_raw:
            self.ce[int(j)] = ce_raw[j]
        del ce_raw
        m_lil = loadmat(self.cef_file)
        self.cef = m_lil['cef']
        
    def revise_t(self):
        print 't', strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
        cx = self.cef.tocoo()
        for j, i, v in itertools.izip(cx.row, cx.col, cx.data):
            self.tmatrix[j, i] = v*pow(self.ce[j], -1)
        del cx
        self.tmatrix = lil_matrix(self.tmatrix.todense())

    def init_q(self):
        print 'q', strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
        lms = set([])
        for en_line, fr_line in self.iterator():
            en_words = en_line.split(" ")
            fr_words = fr_line.split(" ")
            l = len(en_words)
            m = len(fr_words)
            lms.add((l, m))

        for (l, m) in lms:
            key = "%s_%s" % (l, m)
            self.qjilm[key] = tile(array([pow(l + 1, -1)]), l*m).reshape((l, m))
            self.cjilm[key] = tile(array([0]), l*m).reshape((l, m))
            self.cilm[key] = tile(array([0]), m)
        del lms

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

    def index_iterator(self):
        for en_line, fr_line in self.iterator():
            en_words = en_line.split(" ")
            fr_words = fr_line.split(" ")
            l = len(en_words)
            m = len(fr_words)
            key = "%s_%s" % (l, m)
            dt = lil_matrix((len(self.en_dict), len(self.fr_dict)))
            dq = tile(array([0]), l*m).reshape((l, m))
            for i in xrange(m):
                n = self.fr_dict[fr_words[i]]
                self.cilm[key][i] += 1
                s = 0
                for j in xrange(l):
                    k = self.en_dict[en_words[j]]
                    d = self.qjilm[key][j][i] * self.tmatrix[k, n]
                    dt[k, n] = d
                    dq[j][i] = d
                    s += d
                yield key, dt, dq, s

    def revise_tmatrix(self):
        cx = self.cef.tocoo()
        for j, i, v in itertools.izip(cx.row, cx.col, cx.data):
            self.tmatrix[j, i] = v*pow(self.ce[j], -1)
        del cx

    def iterate(self, n):
        for it in xrange(n):
            print it, strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
            num = 0
            for key, dt, dq, s in self.index_iterator():
                num += 1
                print num, strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
                ps = pow(s, -1)
                dt = dt.tocoo()
                dq = multiply(dq, ps)
                for k, n, v in itertools.izip(dt.row, dt.col, dt.data):
                    self.cef[k, n] += v * ps
                    self.ce[k] += v * ps
                self.cjilm[key] = add(self.cjilm[key], dq)

            print 'revise t, ', strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
            self.revise_tmatrix()

            print 'revise q', strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
            for key in self.qjilm:
                if sum(self.cilm[key]) > 0:
                    self.qjilm[key] = divide(self.cjilm[key], self.cilm[key])
            

def main(en_filename, fr_filename):
    print strftime("%a, %d %b %y %H:%M:%S +0000", gmtime())
    counter = Counter(en_filename, fr_filename, 'en_dict', 'fr_dict', 'cef.mat', 'ce', 'tmatrix.mat')
    counter.iterate(1)
    json.dump(counter.en_dict, open('en_dict', 'wb'))
    json.dump(counter.fr_dict, open('fr_dict', 'wb'))
    savemat('tmatrix_ibm2.mat', {'tmatrix': counter.tmatrix})
    savez('qjilm.npz', **counter.qjilm)


def usage():
    sys.stderr.write("""
    Usage: python counter2.py [en phrase training file] [transl phrase training file] > [IBM Model 1 params matrix]
        Get IBM Model 1 from the training set.\n""")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)


main(sys.argv[1], sys.argv[2])