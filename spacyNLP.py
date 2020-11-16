#pour afficher différentes variables, décommentez les print correspondants

import time
import spacy
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

#condensation des tags
NOUNS = ['NOUN', 'PROPN']
VERBS = ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ']
SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS = ["dobj", "dative", "attr", "oprd"]

#modèle anglais
nlp = spacy.load('en_core_web_lg')
nlp.Defaults.stop_words.add("\n")

#si nécessaire récupère le texte sur internet (uniquement le texte entre balise HTML <p>)
def download_document(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.find('title').get_text()
    document = ' '.join([p.get_text() for p in soup.find_all('p')])
    return document
    
#extrait le nom le plus souvent sujet 
def extract_subject(doc):
    #extraction des noms sujets
    possible_subjects = []
    for token in doc:
         if not token.is_stop and not token.is_punct and token.pos_ in NOUNS and token.dep_ in SUBJECTS:
            complete_subj = ''
            #si nécessaire, récupère aussi les adjectifs qui qualifient le nom
            for t in token.subtree:
                complete_subj += t.text + " " if t.pos_ != 'DET' else t.text.lower() + " "
            possible_subjects.append(complete_subj)
    #print("Spacy possible subjects: ", possible_subjects)
    #récupération des plus courants
    sub_freq = Counter(possible_subjects)
    common_subjects = [sub for sub, freq in sub_freq.most_common(10)]
    if len(common_subjects) != 0:
        return nlp(common_subjects[0])
    else:
        return nlp('No subject found')

#extraction du verbe principal
def extract_verb(doc, subject):
    #verbes qui ne sont pas auxiliaires
    verbs = [(tok, tok.lemma_) for tok in doc if tok.pos_ == "VERB" and tok.dep_ != "aux"]
    #verbes les plus courants
    verb_freq=Counter(l for t, l in verbs)
    common_verbs = [verb for verb, freq in verb_freq.most_common(10)]
    #print("Spacy most frequent verbs: ", most_freq_verbs)
    #verbes avec le bon sujet, on prend le dernier mot du sujet car en anglais les adjectifs sont avant le nom
    possible_verbs = [(verb, l) for verb, l in verbs if [t.text for t in subject if t.is_stop == False][-1] in [v.text for v in verb.lefts]]
    #print("Spacy possible verbs: ", possible_verbs)
    if len(possible_verbs) != 0:
        #verbe principal
        main_verb = [v for v, l in possible_verbs if l in common_verbs][0]
        #toutes les apparitions de ce verbe dans le texte 
        verb_occurences = [v for v in doc if v.lemma_ == main_verb.lemma_]
        #forme verbale la plus fréquente (ex: landed ou land)
        form_freq = Counter([v.text for v in verb_occurences])
        most_common_form = [v for v, freq in form_freq.most_common(1)][0]
        return [v for v in verb_occurences if v.text == most_common_form][0]
    else: 
        return nlp('No verb found')

#extrait le complément
def extract_object(doc, verb):
    verb_occurences = [v for v in doc if v.lemma_ == verb.lemma_]
    #extraction de tous les compléments des différentes occurences du verbe choisi
    objs = [[] for i in range(len(verb_occurences))]
    for i in range(len(verb_occurences)):
        v = verb_occurences[i]
        rights = list(v.rights)
        for r in rights: 
            if r.pos_ in NOUNS:
                objs[i].append(r)
            elif r.dep_ == "prep": #récupération des mots introduits par une préposition
                for w in r.subtree:
                    objs[i].append(w)
    #print("Spacy objects: ", objs)
    length_obj = 0
    for i in range(len(verb_occurences)):
        length_obj += len(objs[i])
    #si des compléments existent
    if length_obj !=0:
        #trouve le mot le plus courant dans ceux ci
        freq_word = Counter([w.text for x in objs for w in x if w.pos_ in NOUNS or w.pos_ == 'VERBS'])            
        most_freq_word=freq_word.most_common(1)[0][0]
        #transforme les liste de tokens de chaque complément en un unique string
        merged_objs=[]
        for i in range(len(verb_occurences)):
            s=''
            for w in objs[i]:
                s+=w.text + " "
            merged_objs.append(s)
        #print("Spacy merged objects: ", merged_objs)
        #renvoie le prmeier complément contenant le mot le plus courant
        return [o for o in merged_objs if most_freq_word in o][0]
    else : 
        return ' '
        
#fonction globale qui résume le texte
def summaryTextSpacy(fromInternet, wantedUrl=None, wantedFile=None):
    t0 = time.time() #mesure du temps
    #récupération du texte, soit depuis internet soit par un fichier texte
    if fromInternet :
        url=wantedUrl
        document = download_document(url)
    else : 
        fichier=open(wantedFile, 'r')
        document=fichier.read()
    #création de la variable qui contient toutes les infos
    doc = nlp(document)
    #print("Spacy document: ", doc)
    t1 = time.time()
    #extraction du sujet
    subject = extract_subject(doc) # nlp
    #print("Spacy subject: ", subject)
    t2 = time.time()
    #test
    if subject.text == 'No subject found':
        return subject, t1-t0, t2-t1, None, None
    #extraction du verbe
    verb = extract_verb(doc, subject) #token
    #print("Spacy verb: ", verb)
    t3 = time.time()
    #test
    if verb.text == 'No verb found':
        return subject.text + verb.text, t1-t0, t2-t1, None, None
    #extraction de l'objet
    obj = extract_object(doc, verb) #str
    #print("Spacy object: ", object)
    #concatenation en un string
    str = subject.text +" " + verb.text + " " + obj
    t4 = time.time()
    #fermeture du fichier si nécessaire
    if not fromInternet: 
        fichier.close()
    return str, t1-t0, t2-t1, t4-t1, t4-t0

    
    
    
        
    
    