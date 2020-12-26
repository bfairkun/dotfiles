#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 15:09:19 2018
@author: benfair
"""

import sys
import re
from signal import signal, SIGPIPE, SIG_DFL
import argparse
import sys

parser = argparse.ArgumentParser(description="""
        This command line script will read in a stranded 6column bed file of annotated introns (5' and 3' splice site pairings) and regard those as annotated introns. From there it will annotate an 6 column stranded bed file of input as to whether the introns are annotated, alt5'ss, alt3'ss, new intron (neither 5' or 3' splice sites are annotated), or new splice site pairing (both 5' and 3' splice sites are annotated but the pairing has not been annotated, as is the case in a novel exon skipping event).
        """)
parser.add_argument('-I','--FileIn',  default="-", help="REQUIRED. Stranded 6 column bed file of introns that need alternative splice site classification. Use 'stdin' or '-' to read from stdin", required=True)
parser.add_argument('-A','--AnnotationsBed',  help="REQUIRED. Stranded 6 column bed file of annotated introns", required=True)
parser.add_argument('-O', '--FileOut', default="stdout", help="REQUIRED. Output file. Same as input file but with extra field of alternative splice site classification field. Use 'stdout' to write to stdout", required=True)
parser.add_argument("--quiet", help="OPTIONAL. quiet the output verbosity", action="store_true")
args = parser.parse_args()


if args.FileIn in ("stdin", "-"):
    fhIn = sys.stdin
else:
    fhIn = open(args.FileIn, 'rU')

if args.FileOut in ("stdout"):
    fhOut = sys.stdout
else:
    fhIn = open(args.FileOut, 'w')

fh_AnnotatedSpliceJunctionsBedFile= open(args.AnnotationsBed, 'rU')
signal(SIGPIPE, SIG_DFL)

def GetSpliceDonorAndAcceptorCoordinates(chrom, start, stop, strand):
    '''
    function returns a tuple pair of (SpliceDonor, SpliceAcceptor) where SpliceDonor and SpliceAcceptor are themselves a tuple of (chromosome, coordinate, strand).
    '''
    if strand=='+':
        SpliceDonorCoord=(chrom, start, strand)
        SpliceAcceptorCoord=(chrom, stop, strand)
    elif strand=='-':
        SpliceDonorCoord=(chrom, stop, strand)
        SpliceAcceptorCoord=(chrom, start, strand)
    else:
        print("Failed... Need strand information coded as + or -. This information should be stored in field6 of bed file")
    return (SpliceDonorCoord, SpliceAcceptorCoord)


# AnnotatedSpliceJunctionsBedFile='/Users/benfair/Downloads/TargetIntrons.sorted.bed'
# InputSpliceJunctionsBedFile='/Users/benfair/Downloads/SI_Tables_AlternativeCounts.bed.txt'


#Initialize sets of annotated splice sites
AnnotatedSpliceDonors=set()
AnnotatedSpliceAcceptors=set()
AnnotatedSplicePairs=set()

for line in fh_AnnotatedSpliceJunctionsBedFile:
    l=line.strip('\n').split('\t')
    chrom, start, stop, name, score, strand = l[0:6]
    Donor,Acceptor = GetSpliceDonorAndAcceptorCoordinates(chrom, start, stop, strand)

    #Add to sets
    AnnotatedSpliceDonors.add(Donor)
    AnnotatedSpliceAcceptors.add(Acceptor)
    AnnotatedSplicePairs.add((Donor,Acceptor))

for line in fhIn:
    l=line.strip('\n').split('\t')
    chrom, start, stop, name, score, strand = l[0:6]
    leftovers=l[6:]
    Donor,Acceptor = GetSpliceDonorAndAcceptorCoordinates(chrom, start, stop, strand)

    if (Donor,Acceptor) in AnnotatedSplicePairs:
        AS_type = 'AnnotatedSpliceSite'
    elif Donor in AnnotatedSpliceDonors and Acceptor not in AnnotatedSpliceAcceptors:
        AS_type = 'Alt3ss'
    elif Acceptor in AnnotatedSpliceAcceptors and Donor not in AnnotatedSpliceDonors:
        AS_type = 'Alt5ss'
    elif Donor in AnnotatedSpliceDonors and Acceptor in AnnotatedSpliceAcceptors:
        AS_type = 'AltPairingOfSites'
    elif Donor not in AnnotatedSpliceDonors and Acceptor not in AnnotatedSpliceAcceptors:
        AS_type = 'NewIntron'
    fhOut.write('\t'.join(l + [AS_type]) + '\n')


fh_AnnotatedSpliceJunctionsBedFile.close()
fhIn.close()
fhOut.close()
