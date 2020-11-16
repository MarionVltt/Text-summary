
#voir commentaires dans le fichier spacyNLP, la différence principale est le modèle utilisé
import time
import spacy
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

NOUNS = ['NOUN', 'PROPN']
VERBS = ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ']
SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS = ["dobj", "dative", "attr", "oprd"]

nlp = spacy.load('fr')
nlp.Defaults.stop_words.add("\n")

def download_document(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.find('title').get_text()
    document = ' '.join([p.get_text() for p in soup.find_all('p')])
    return document
    
def extract_subject(doc):
    possible_subjects = []
    for token in doc:
         if not token.is_stop and not token.is_punct  and token.pos_ in NOUNS and token.dep_ in SUBJECTS:
            complete_subj = ''
            for t in token.subtree:
                complete_subj += t.text + " " if t.pos_ != 'DET' else t.text.lower() + " "
            possible_subjects.append(complete_subj)
    sub_freq = Counter(possible_subjects)
    common_subjects = [sub for sub, freq in sub_freq.most_common(10)]
    #print(common_subjects)
    if len(common_subjects) !=0:
        return nlp(common_subjects[0])
    else : 
        return nlp('Sujet non trouvé')
    
def extract_verb(doc, subject):
    verbs = [(tok, tok.lemma_) for tok in doc if tok.pos_ == "VERB" and tok.dep_ != "aux"]
    print(verbs)
    verb_freq=Counter(l for t, l in verbs)
    common_verbs = [verb for verb, freq in verb_freq.most_common(10)]
    #verbes avec le bon sujet, on prend le premier mot du sujet car en français les adjectifs sont après le nom
    possible_verbs = [(verb, l) for verb, l in verbs if [t.text for t in subject if t.is_stop == False][0] in [v.text for v in verb.lefts]]
    if len(possible_verbs) !=0:
        main_verb = [v for v, l in possible_verbs if l in common_verbs][0]
        verb_occurences = [v for v in doc if v.lemma_ == main_verb.lemma_]
        form_freq = Counter([v.text for v in verb_occurences])
        most_common_form = [v for v, freq in form_freq.most_common(1)][0]
        return [v for v in verb_occurences if v.text == most_common_form][0]
    else:
        return nlp('Verbe non trouvé')
    
def extract_object(doc, verb):
    verb_occurences = [v for v in doc if v.lemma_ == verb.lemma_]
    objs = [[] for i in range(len(verb_occurences))]
    for i in range(len(verb_occurences)):
        v = verb_occurences[i]
        rights = list(v.rights)
        for r in rights: 
            if r.pos_ in NOUNS:
                objs[i].append(r)
            elif r.dep_ == "prep":
                for w in r.subtree:
                    objs[i].append(w)
    length_obj = 0
    for i in range(len(verb_occurences)):
        length_obj += len(objs[i])
    if length_obj !=0:
        freq_word = Counter([w.text for x in objs for w in x if w.pos_ in NOUNS or w.pos_ == 'VERBS'])            
        most_freq_word=freq_word.most_common(1)[0][0]
        merged_objs=[]
        for i in range(len(verb_occurences)):
            s=''
            for w in objs[i]:
                s+=w.text + " "
            merged_objs.append(s)
        return [o for o in merged_objs if most_freq_word in o][0]
    else : 
        return ' '
        
def summaryTextSpacyfr(fromInternet, wantedUrl=None, wantedFile=None):
    t0 = time.time()
    fromInternet = fromInternet
    if fromInternet :
        url=wantedUrl
        document = download_document(url)
    else : 
        fichier=open(wantedFile, 'r')
        document=fichier.read()
    doc = nlp(document)
    t1 =time.time()
    subject = extract_subject(doc) # nlp
    t2 =time.time()
    if subject.text == 'Sujet non trouvé':
        return subject, t1-t0, t2-t1, None, None
    verb = extract_verb(doc, subject) #token
    t3 =time.time()
    if verb.text == 'Verbe non trouvé':
        return subject.text + verb.text, t1-t0, t2-t1, None, None
    obj = extract_object(doc, verb) #str can be empty
    str = subject.text +" " + verb.text + " " + obj
    t4 =time.time()
    #fermeture du fichier si nécessaire
    if not fromInternet: 
        fichier.close()
    return str, t1-t0, t2-t1, t4-t1, t4-t0
    
    
    
        
    
    