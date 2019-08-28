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
    f = open(sys.argv[1] + "/docToTitle.txt", "r")
    for line in f:
        docID, titleMap = line.split("#")
        docToTitle[docID] = titleMap
        noDocs += 1
except:
    print("Can't find docToTitle.txt")
    sys.exit(1)

stopWords = set()
try:
    f = open("stopwords.txt", "r")
    for line in f:
        stopWords.add(line.strip())
except:
    print("Can't find stopwords.txt")
    sys.exit(1)

invertedIndex = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


def readIndex(path_to_index):
    try:
        f = open(path_to_index + "/invertedIndex.txt", "r")
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
    reg = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.DOTALL)
    text = reg.sub('', text)
    # Regular Expression to remove CSS
    reg = re.compile(r'{\|(.*?)\|}', re.DOTALL)
    text = reg.sub('', text)
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


fieldDict = {"title": "t", "body": "b", "infobox": "i",
             "category": "c", "ref": "r", "ext": "e"}


def parseQuery(queryText, isFieldQuery):
    searchResultTitle = list()
    if isFieldQuery:
        fieldQList = list()
        queryList = queryText.split()
        for word in queryList:
            if ":" not in word:
                word = "body:" + word
            cat, content = word.split(":")
            content = cleanText(content)
            content = ps.stem(content)
            if len(content) > 0 and content not in stopWords:
                fieldQList.append((content, fieldDict[cat]))

        # searchResultDict = dict(set())
        # searchResult = set()
        # for tok, ctype in fieldQList:
        #     searchResultDict[tok] = set(i for i in invertedIndex[tok].keys() if invertedIndex[tok][i][ctype]>0)
        #     if len(searchResult) == 0:
        #         searchResult = searchResultDict[tok]
        #     else:
        #         searchResult = searchResult.intersection(searchResultDict[tok])

        #     print(tok , searchResultDict[tok])

        # for docId in searchResult:
        #     searchResultTitle.append(docToTitle[docId])
        searchResult = defaultdict(int)
        for tok, ctype in fieldQList:
            for docID, freqDict in invertedIndex[tok].items():
                searchResult[docID] += freqDict[ctype]

        searchResult = sorted(searchResult.items(),
                              key=lambda item: item[1], reverse=True)[0:10]

        for tup in searchResult:
            docId, freq = tup
            searchResultTitle.append(docToTitle[docId])

    else:
        queryText = cleanText(queryText)
        tokenList = re.findall(r'\d+|[\w]+', queryText, re.DOTALL)
        finalTokens = list()
        for tok in tokenList:
            val = ps.stem(tok)
            if len(val) > 0 and val not in stopWords:
                finalTokens.append(val)
        searchResultTitle = list()
        # searchResultDict = dict(set())
        # searchResult = set()
        # for tok in finalTokens:
        #     searchResultDict[tok] = set(invertedIndex[tok].keys())
        #     if len(searchResult) == 0:
        #         searchResult = searchResultDict[tok]
        #     else:
        #         searchResult = searchResult.union(searchResultDict[tok])

        searchResult = defaultdict(int)
        for tok in finalTokens:
            for docID, freqDict in invertedIndex[tok].items():
                freq = sum(freqDict.values())
                searchResult[docID] += freq

        searchResult = sorted(searchResult.items(),
                              key=lambda item: item[1], reverse=True)[0:10]

        for tup in searchResult:
            docId, freq = tup
            searchResultTitle.append(docToTitle[docId])
    return searchResultTitle


def search(path_to_index, queries):
    readIndex(path_to_index)
    finalResult = list()
    fields = ['title:', 'body:', 'infobox:', 'category:', 'ref:']
    for query in queries:
        isFieldQuery = False
        for f in fields:
            if f in query:
                isFieldQuery = True
        result = parseQuery(query, isFieldQuery)
        finalResult.append(result)
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
