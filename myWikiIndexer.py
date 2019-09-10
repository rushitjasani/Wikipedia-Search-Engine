# startting phase 2
import sys
import timeit
import re
import spacy
from xml.sax import parse
from xml.sax import ContentHandler
from collections import defaultdict
from nltk.stem import PorterStemmer


ps = PorterStemmer()
stemmingMap = dict()
fileLim = 25000
dumpFile = sys.argv[1]
path_to_index = sys.argv[2]

if len(sys.argv) != 3:
    print("Arguments invalid")
    print("Run using : bash index.sh <path_to_dump> <path_to_index_folder>")
    sys.exit(1)

documentTitleMapping = open("./docToTitle.txt", "w")

'''
Dictionary structure
{
    word : {
        docID :{
            t1 : cnt1,
            t2 : cnt2
        }
        docId : {
            t1 : cnt3,
            t2 : cnt4
        }
        .
        .
        .
    }
    .
    .
    .
}
'''
invertedIndex = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

stopwordsList = set()
with open("stopwords.txt", 'r') as f:
    for line in f:
        line = line.strip()
        stopwordsList.add(line)

# Regular Expression to remove Brackets and other meta characters from title
regExp1 = re.compile(r"[~`!@#$%\-^*+{\[}\]\|\\<>/?,]", re.DOTALL)
# Regular Expression for Categories
catRegExp = r'\[\[category:(.*?)\]\]'
# Regular Expression for Infobox
infoRegExp = r'{{infobox(.*?)}}'
# Regular Expression for References
referenesRegExp = r'== ?references ?==(.*?)=='
# Regular Expression to remove Infobox
regExp2 = re.compile(infoRegExp, re.DOTALL)
# Regular Expression to remove references
regExp3 = re.compile(referenesRegExp, re.DOTALL)
# Regular Expression to remove junk from text
regExp4 = re.compile(r"[~`!@#$%\-^*+{\[}\]\|\\<>/?,]", re.DOTALL)


def cleanText(text):
    # Regular Expression to remove {{cite **}} or {{vcite **}}
    reg = re.compile(r'{{v?cite(.*?)}}', re.DOTALL)
    text = reg.sub('', text)
    # Regular Expression to remove Punctuation
    reg = re.compile(r'[.,;_()/\"\'\=]', re.DOTALL)
    text = reg.sub(' ', text)
    # Regular Expression to remove [[file:]]
    reg = re.compile(r'\[\[file:(.*?)\]\]', re.DOTALL)
    text = reg.sub('', text)
    # Regular Expression to remove <..> tags from text
    reg = re.compile(r'<(.*?)>', re.DOTALL)
    text = reg.sub('', text)
    # Remove Non ASCII characters
    reg = re.compile(r'[^\x00-\x7F]+', re.DOTALL)
    text = reg.sub(' ', text)
    return text


def addToIndex(wordList, docID, t):
    for word in wordList:
        word = word.strip()
        word = re.sub(r'[\ \.\-\:\&\$\!\*\+\%\,\@]+',"",word)
        if len(word) >= 3 and len(word) <= 500 and word not in stopwordsList:
            if word not in stemmingMap.keys():
                stemmingMap[word] = ps.stem(word)
            word = stemmingMap[word]
            if word not in stopwordsList:
                if word in invertedIndex:
                    if docID in invertedIndex[word]:
                        if t in invertedIndex[word][docID]:
                            invertedIndex[word][docID][t] += 1
                        else:
                            invertedIndex[word][docID][t] = 1
                    else:
                        invertedIndex[word][docID] = {t: 1}
                else:
                    invertedIndex[word] = dict({docID: {t: 1}})


def processBuffer(text, docID, isTitle):
    global path_to_index
    text = text.lower()
    text = cleanText(text)
    if isTitle == True:
        regExp1.sub(' ', text)
        words = text.split()
        tokens = list()
        for word in words:
            if word not in stopwordsList:
                tokens.append(word.strip())

        addToIndex(tokens, docID, "t")
    else:
        infobox = list()
        categories = list()
        external = list()
        references = list()

        externalLinkIndex = 0
        categoryIndex = len(text)

        categories = re.findall(catRegExp, text, flags=re.MULTILINE)

        lines = text.split('\n')
        flag = 1
        for i in range(len(lines)):
            if '{{infobox' in lines[i]:
                flag = 0
                temp = lines[i].split('{{infobox')[1:]
                infobox.extend(temp)
                while True:
                    if(i >= len(lines)):
                        break
                    if '{{' in lines[i]:
                        count = lines[i].count('{{')
                        flag += count
                    if '}}' in lines[i]:
                        count = lines[i].count('}}')
                        flag -= count
                    if flag <= 0:
                        break
                    i += 1
                    if(i < len(lines)):
                        infobox.append(lines[i])
            if flag <= 0:
                text = '\n'.join(lines[i+1:])
                break

        try:
            externalLinkIndex = text.index('==external links==')+20
        except:
            pass

        if externalLinkIndex == 0:
            try:
                externalLinkIndex = text.index('== external links ==')+22
            except:
                pass

        try:
            categoryIndex = text.index('[[category:')
        except:
            pass

        if externalLinkIndex != 0:
            external = text[externalLinkIndex:categoryIndex]
            external = re.findall(r'\[(.*?)\]', external, flags=re.MULTILINE)

        references = re.findall(referenesRegExp, text, flags=re.DOTALL)

        if externalLinkIndex != 0:
            text = text[0:externalLinkIndex-20]

        text = regExp3.sub('', text)
        text = regExp4.sub(' ', text)
        words = text.split()
        addToIndex(words, docID, "b")

        categories = ' '.join(categories)
        categories = regExp4.sub(' ', categories)
        categories = categories.split()
        addToIndex(categories, docID, "c")

        external = ' '.join(external)
        external = regExp4.sub(' ', external)
        external = external.split()
        addToIndex(external, docID, "e")

        references = ' '.join(references)
        references = regExp4.sub(' ', references)
        references = references.split()
        addToIndex(references, docID, "r")

        for infoList in infobox:
            tokenList = list()
            tokenList = re.findall(r'\d+|[\w]+', infoList, re.DOTALL)
            tokenList = ' '.join(tokenList)
            tokenList = regExp4.sub(' ', tokenList)
            tokenList = tokenList.split()
            addToIndex(tokenList, docID, "i")

        if docID%fileLim == 0:
            f = open(path_to_index + "/" + str(docID) + ".txt", "w")
            for key, val in sorted(invertedIndex.items()):
                s = str(key)+"="
                for k, v in sorted(val.items()):
                    s += str(k) + ":"
                    for k1, v1 in v.items():
                        s = s + str(k1) + str(v1) + "#"
                    s = s[:-1]+","
                f.write(s[:-1]+"\n")
            f.close()
            invertedIndex.clear()
            stemmingMap.clear()


class WikiContentHandler(ContentHandler):
    def __init__(self):
        self.docID = 0
        self.isTitle = False
        self.flag = False
        self.title = ""
        self.buffer = ""

    def characters(self, content):
        self.buffer = self.buffer + content

    def startElement(self, element, attributes):
        if element == "title":
            self.buffer = ""
            self.isTitle = True
            self.flag = True
        if element == "page":
            self.docID += 1
        if element == "text":
            self.buffer = ""
        if element == "id" and self.flag:
            self.buffer = ""

    def endElement(self, element):
        if element == "title":
            processBuffer(self.buffer, self.docID, self.isTitle)
            self.isTitle = False
            self.title = self.buffer
            self.buffer = ""
        elif element == "text":
            processBuffer(self.buffer, self.docID, self.isTitle)
            self.buffer = ""
        elif element == "id" and self.flag == True:
            try:
                documentTitleMapping.write(str(self.docID)+"#"+self.title+"\n")
            except:
                documentTitleMapping.write(
                    str(self.docID)+"#"+self.title.encode('utf-8')+"\n")
            self.flag = False
            self.buffer = ""


def main():
    parse(dumpFile, WikiContentHandler())
    f = open(path_to_index + "/19567269.txt", "w")
    for key, val in sorted(invertedIndex.items()):
        s = str(key)+"="
        for k, v in sorted(val.items()):
            s += str(k) + ":"
            for k1, v1 in v.items():
                s = s + str(k1) + str(v1) + "#"
            s = s[:-1]+","
        f.write(s[:-1]+"\n")
    f.close()
    invertedIndex.clear()
    stemmingMap.clear()


if __name__ == "__main__":
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print(stop - start)
