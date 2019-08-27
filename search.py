import sys
import re
from collections import defaultdict
# from stemming.porter import stem
from nltk.stem import PorterStemmer

ps = PorterStemmer()


def read_file(testfile):
    with open(testfile, 'r') as file:
        queries = file.readlines()
    return queries


def write_file(outputs, path_to_output):
    '''outputs should be a list of lists.
        len(outputs) = number of queries
        Each element in outputs should be a list of titles corresponding to a particular query.'''
    with open(path_to_output, 'w') as file:
        for output in outputs:
            for line in output:
                file.write(line.strip() + '\n')
            file.write('\n')

docToTitle = dict()
noDocs = 0
try:
    f = open("docToTitle.txt","r")
    for line in f:
        docID, titleMap = line.split("#")
        docToTitle[docID] = titleMap
        noDocs += 1
except:
    print("Can't find docToTitle.txt")
    sys.exit(1)

stopWords = set()
try:
    f = open("stopwords.txt","r")
    for line in f:
        stopWords.add(line.strip())
except:
    print("Can't find stopwords.txt")
    sys.exit(1)

invertedIndex = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))

def readIndex(path_to_index):
    try:
        f = open(path_to_index, "r")
        for line in f:
            word, postingList = line.split("=")
            postingList = postingList.split(",")
            for pl in postingList:
                docID, freqDict = pl.split(":")
                freqDict = freqDict.split("#")
                for freq in freqDict:
                    invertedIndex[word][docID][freq[0]] = int(freq[1:])
    except:
        pass

def cleanText(text):
    # Regular Expression to remove URLs
    reg = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.DOTALL)
    text = reg.sub('',text)
    # Regular Expression to remove CSS
    reg = re.compile(r'{\|(.*?)\|}',re.DOTALL)
    text = reg.sub('',text)
    # Regular Expression to remove {{cite **}} or {{vcite **}}
    reg = re.compile(r'{{v?cite(.*?)}}',re.DOTALL)  
    text = reg.sub('',text)
    # Regular Expression to remove Punctuation
    reg = re.compile(r'[.,;_()"/\']',re.DOTALL)
    text = reg.sub(' ',text)
    # Regular Expression to remove [[file:]]
    reg = re.compile(r'\[\[file:(.*?)\]\]',re.DOTALL)
    text = reg.sub('',text)
    # Regular Expression to remove <..> tags from text
    reg = re.compile(r'<(.*?)>',re.DOTALL)
    text = reg.sub('',text)
    # Regular Expression to remove non ASCII char
    reg = re.compile(r'[^\x00-\x7F]+',re.DOTALL)
    text = reg.sub(' ', text)
    return text

def search(path_to_index, queries):
    '''Write your code here'''
    readIndex(path_to_index)
    finalResult = list()
    for query in queries:
        print(query)
    return finalResult


def main():
    path_to_index = sys.argv[1]
    testfile = sys.argv[2]
    path_to_output = sys.argv[3]

    queries = read_file(testfile)
    outputs = search(path_to_index, queries)
    write_file(outputs, path_to_output)


if __name__ == '__main__':
    main()
