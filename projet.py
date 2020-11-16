# -*- coding: utf-8 -*-
"""
Created on Wed Nov 21 17:27:35 2018

@author: mario
"""

import nltk
import requests
import re
from bs4 import BeautifulSoup
from nltk.corpus import stopwords, wordnet
stopFrench = stopwords.words("french")
wnl = nltk.WordNetLemmatizer()
#print(stopFrench)
#Tags utilisés par le POS tagging de nltk
NOMS = ['NC', 'NP', 'N', 'ET']
VERBES = ['V', 'VPP', 'VPR', 'VINF']
NOUNS = ['NN', 'NNS', 'NNP', 'NNPS']
VERBS = ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ']

#POS tagging pour le français
from nltk.tag import StanfordPOSTagger
jar = 'D:/Documents/Ottawa/IA/Code/stanford-postagger-full-2018-10-16/stanford-postagger-3.9.2.jar'
model = 'D:/Documents/Ottawa/IA/Code/stanford-postagger-full-2018-10-16/models/french.tagger'
import os
java_path = "C:/Program Files/Java/jdk1.8.0_181/bin/java.exe"
os.environ['JAVAHOME'] = java_path

pos_tagger = StanfordPOSTagger(model, jar, encoding='utf8' )
    
#récupérer le texte 
url = 'https://www.tomsguide.fr/2018/08/23/une-ia-pour-detecter-les-fake-news/'
r = requests.get(url)

#récupérer le titre et le document en ne conservant que le texte se trouvant entre balises <p>
soup = BeautifulSoup(r.text, 'html.parser')
title = soup.find('title').get_text()
document = ' '.join([p.get_text() for p in soup.find_all('p')])
print(title)

#1er tag avant le lower pour repérer les noms propres
preTokens = nltk.word_tokenize(document)
prePosTokens = pos_tagger.tag(preTokens)

tokens=[]
for i in range(len(prePosTokens)):
    if prePosTokens[i][1]=='NPP':
        tokens.append(prePosTokens[i][0])
    else:
        tokens.append((prePosTokens[i][0]).lower())

#Lemmatisation avec TreeTagger
import treetaggerwrapper
from treetaggerwrapper import TreeTagger
tagger = TreeTagger(TAGLANG='fr')
tags=tagger.tag_text(tokens)
lemmas = [t[2] for t in treetaggerwrapper.make_tags(tags)]

#Filtre alphanumérique
alphaTokens = [t for t in lemmas if re.match("^[A-Za-z -]+$",t)]

#Filtre stopwords
filteredLemmas = [t for t in alphaTokens if t not in stopFrench]
#print(filteredLemmas)
filteredText = nltk.Text(filteredLemmas)
fdistFiltered = nltk.FreqDist(filteredText)

filteredLemmasTaged={} #dictionnaire
for i in range(len(filteredLemmas)):
    filteredLemmasTaged[filteredLemmas[i]]= pos_tagger.tag([filteredLemmas[i]])[0][1]
    
#10 noms les plus utlisés
most_freq_nouns = [w for w, c in fdistFiltered.most_common(50)
                   if filteredLemmasTaged[w] in NOMS]
print(most_freq_nouns)

noms_propres = [w for w in filteredLemmas
                   if filteredLemmasTaged[w]=='NPP']
print(noms_propres)

#Reconnaissance entités nommées pas facile en français à moins d'entrainer son modèle avec French Treebank
