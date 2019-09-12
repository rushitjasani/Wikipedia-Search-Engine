#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import timeit
from glob import glob
from collections import defaultdict
from heapq import heapify, heappush, heappop


splittedIndexFolder = './index'
mergedIndexFolder = './finalIndex'

numberOfMergedIndexfile = 0
chunkSize = 5000
secondaryIndex = defaultdict()
invertedIndex = defaultdict()
splittedFilePathList = glob(splittedIndexFolder + '/*')
numOfSplittedFiles = len(splittedFilePathList)
processedFiles = [0 for _ in range(numOfSplittedFiles)]
filePointers = dict()
currentRowofFile = dict()
kWayHeap = list()
termDict = dict()
total = 0

start = timeit.default_timer()


def writeIndextofile():
    global numberOfMergedIndexfile
    numberOfMergedIndexfile += 1
    fileName = mergedIndexFolder + '/index' \
        + str(numberOfMergedIndexfile) + '.txt'
    firstWord = True
    with open(fileName, 'w') as fp:
        for i in sorted(invertedIndex):
            if firstWord:
                secondaryIndex[i] = numberOfMergedIndexfile
                firstWord = False
            fp.write(str(i) + '=' + invertedIndex[i] + '\n')


def writeSecondaryIndex():
    fileName = mergedIndexFolder + '/secondaryIndex.txt'
    with open(fileName, 'w') as fp:
        for i in sorted(secondaryIndex):
            fp.write(str(i) + '\n')


def writePrimaryIndex():
    global numberOfMergedIndexfile
    numberOfMergedIndexfile += 1
    fileName = mergedIndexFolder + '/index' \
        + str(numberOfMergedIndexfile) + '.txt'
    firstWord = True
    with open(fileName, 'w') as fp:
        for i in sorted(invertedIndex):
            if firstWord:
                secondaryIndex[i] = numberOfMergedIndexfile
                firstWord = False
            fp.write(str(i) + '=' + invertedIndex[i] + '\n')


def kWayMerge():
    global total
    for i in range(numOfSplittedFiles):
        processedFiles[i] = 1
        try:
            filePointers[i] = open(splittedFilePathList[i], 'r')
        except:
            pass
        currentRowofFile[i] = filePointers[i].readline()
        termDict[i] = currentRowofFile[i].strip().split('=')
        if termDict[i][0] not in kWayHeap:
            heappush(kWayHeap, termDict[i][0])

    while True:
        if processedFiles.count(0) == numOfSplittedFiles:
            break
        else:
            total += 1
            word = heappop(kWayHeap)
            for i in range(numOfSplittedFiles):
                if processedFiles[i] and termDict[i][0] == word:
                    if word not in invertedIndex:
                        invertedIndex[word] = termDict[i][1]
                    else:
                        invertedIndex[word] += ',' + termDict[i][1]

                    currentRowofFile[i] = \
                        filePointers[i].readline().strip()

                    if currentRowofFile[i]:
                        termDict[i] = currentRowofFile[i].split('=')
                        if termDict[i][0] not in kWayHeap:
                            heappush(kWayHeap, termDict[i][0])
                    else:
                        processedFiles[i] = 0
                        filePointers[i].close()
                        os.remove(splittedFilePathList[i])
            if total >= chunkSize:
                total = 0
                writePrimaryIndex()
                invertedIndex.clear()


kWayMerge()
writePrimaryIndex()
writeSecondaryIndex()
stop = timeit.default_timer()
print(stop - start)
