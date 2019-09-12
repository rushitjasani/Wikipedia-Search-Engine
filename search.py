#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import timeit
from collections import defaultdict
from operator import itemgetter
from nltk.stem import PorterStemmer
from bisect import bisect
from math import log10

ps = PorterStemmer()
noDocs = 0
docToTitle = dict()
stopWords = set()
secondaryIndex = list()
invertedIndex = defaultdict(lambda : defaultdict(lambda : \
                            defaultdict(int)))
fieldDict = {
    'title': 't',
    'body': 'b',
    'infobox': 'i',
    'category': 'c',
    'ref': 'r',
    'ext': 'e',
    }
fields = ['title:', 'body:', 'infobox:', 'category:', 'ref:']


def readDocTitleMap():
    global docToTitle, noDocs
    with open('./docToTitle.txt', 'r') as f:
        for line in f:
            (docID, titleMap) = line.split('#')
            docToTitle[docID] = titleMap
            noDocs += 1


def readStopwords():
    global stopWords
    try:
        f = open('stopwords.txt', 'r')
        for line in f:
            stopWords.add(line.strip())
    except:
        print("Can't find stopwords.txt")
        sys.exit(1)


def readSecondaryIndex():
    global secondaryIndex
    try:
        f = open('finalIndex/secondaryIndex.txt', 'r')
        for line in f:
            secondaryIndex.append(line.split()[0])
    except:
        print("Can't find the secondary index file in 'finalIndex' Folder.")
        sys.exit(1)


def processIndex():
    fileName = '/index' + str() + '.txt'
    firstWord = True
    with open(fileName, 'w') as fp:
        for i in sorted(invertedIndex):
            if firstWord:
                secondaryIndex[i] = 1
                firstWord = False
            fp.write(str(i) + '=' + invertedIndex[i] + '\n')


def cleanText(text):

    # Regular Expression to remove {{cite **}} or {{vcite **}}

    reg = re.compile(r'{{v?cite(.*?)}}', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove Punctuation

    reg = re.compile(r'[.,;_()"/\']', re.DOTALL)
    text = reg.sub(' ', text)

    # Regular Expression to remove [[file:]]

    reg = re.compile(r'\[\[file:(.*?)\]\]', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove <..> tags from text

    reg = re.compile(r'<(.*?)>', re.DOTALL)
    text = reg.sub('', text)

    # Regular Expression to remove non ASCII char

    reg = re.compile(r'[^\x00-\x7F]+', re.DOTALL)
    text = reg.sub(' ', text)
    return text


def getFileNumber(word):
    position = bisect(secondaryIndex, word)
    if position - 1 >= 0 and secondaryIndex[position - 1] == word:
        if position - 1 != 0:
            position -= 1
        if position + 1 == len(secondaryIndex) \
            and secondaryIndex[position] == word:
            position += 1
    return position


def getPostingList(word):
    position = getFileNumber(word)
    primaryFile = 'finalIndex/index' + str(position) + '.txt'
    file = open(primaryFile, 'r')
    data = file.readlines()
    low = 0
    high = len(data)
    mid = int()
    while low <= high:
        mid = int(low + (high - low) / 2)
        cur = data[mid].split('=')[0]
        if cur == word:
            break
        elif cur < word:
            low = mid + 1
        else:
            high = mid - 1
    return data[mid].split('=')[1].split(',')


def printResult(lengthFreq):
    count = 0
    flag = False
    K = 10
    for (_, v) in sorted(lengthFreq.items(), reverse=True):
        for (k1, _) in sorted(v.items(), key=itemgetter(1), reverse=True):
            print("=> ", docToTitle[k1], end='')
            count += 1
            if count == K:
                flag = True
                break
        if flag:
            break


def parseQuery(queryText, isFieldQuery):
    wordRegEx = re.compile(r'[\ \.\-\:\&\$\!\*\+\%\,\@]+', re.DOTALL)
    if isFieldQuery:
        fieldQList = list()
        queryList = queryText.split()
        for word in queryList:
            if ':' not in word:
                word = 'body:' + word
            (cat, content) = word.split(':')
            content = cleanText(content)
            content = ps.stem(content)
            content = wordRegEx.sub('', content)
            if len(content) > 0 and content.isalnum and content \
                not in stopWords:
                fieldQList.append((content, fieldDict[cat]))
        globalSearch = dict(list())

        for (word, category) in fieldQList:
            postingListAll = getPostingList(word)
            postingList = [i for i in postingListAll if category in i]
            if len(postingList) < 2:
                postingList = postingListAll
            numDoc = len(postingList)
            idf = log10(noDocs / numDoc)
            for i in postingList:
                (docID, entry) = i.split(':')
                if docID in globalSearch:
                    globalSearch[docID].append(entry + '_' + str(idf))
                else:
                    globalSearch[docID] = [entry + '_' + str(idf)]
    else:

        queryText = cleanText(queryText)
        tokenList = queryText.split(' ')
        tokenList = [wordRegEx.sub('', i) for i in tokenList]
        finalTokens = list()
        for tok in tokenList:
            val = ps.stem(tok)
            if len(val) > 0 and val.isalnum and val not in stopWords:
                finalTokens.append(val)
        globalSearch = dict(list())
        for word in finalTokens:
            postingList = getPostingList(word)
            numDoc = len(postingList)
            idf = log10(noDocs / numDoc)
            for i in postingList:
                (docID, entry) = i.split(':')
                if docID in globalSearch:
                    globalSearch[docID].append(entry + '_' + str(idf))
                else:
                    globalSearch[docID] = [entry + '_' + str(idf)]

    lengthFreq = dict(dict())
    regEx = re.compile(r'(\d+|\s+)')
    for k in globalSearch:
        weightedFreq = 0
        n = len(globalSearch[k])
        for x in globalSearch[k]:
            (x, idf) = x.split('_')
            x = x.split('#')
            for y in x:
                lis = regEx.split(y)
                (tagType, freq) = (lis[0], lis[1])
                if tagType == 't':
                    weightedFreq += int(freq) * 500
                elif tagType == 'i' or tagType == 'c' or tagType == 'r' \
                    or tagType == 'e':
                    weightedFreq += int(freq) * 50
                elif tagType == 'b':
                    weightedFreq += int(freq)
        if n in lengthFreq:
            lengthFreq[n][k] = float(log10(1 + weightedFreq)) \
                * float(idf)
        else:
            lengthFreq[n] = {k: float(log10(1 + weightedFreq)) \
                             * float(idf)}

    printResult(lengthFreq)


def search(path_to_index, query):
    global fields
    isFieldQuery = False
    for f in fields:
        if f in query:
            isFieldQuery = True
            break
    parseQuery(query, isFieldQuery)


def main():
    path_to_index = './finalIndex/'
    while True:
        query = input('\nEnter Query: ')
        print('+++++++++++++++++++++++++++++++++++')
        start = timeit.default_timer()
        search(path_to_index, query)
        end = timeit.default_timer()
        print('\nTook', end - start, 'sec\n')
        print('+++++++++++++++++++++++++++++++++++')


if __name__ == '__main__':
    print ('reading DoctitleMap')
    readDocTitleMap()
    print ('reading secondary Index')
    readSecondaryIndex()
    readStopwords()
    try:
        main()
    except:
        print ('''\n\nThank You..\n''')
