#pour afficher différentes variables, décommentez les print correspondants

import time
import nltk
import requests
import re
from bs4 import BeautifulSoup
import os
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.parse.stanford import StanfordDependencyParser

#outils utiles
stopWords = stopwords.words("english")
#print("NLTK stopwords: ", stopWords)
wnl = nltk.WordNetLemmatizer()

#lignes nécessaires pour faire fonctionner le dependency parser de Stanford, il sera sans doute 
#nécessaire de changer les chemins d'accès
path_to_jar = 'D:/Documents/Ottawa/IA/Code/stanford-parser-full-2018-10-17/stanford-parser.jar'
path_to_models_jar = 'D:/Documents/Ottawa/IA/Code/stanford-parser-full-2018-10-17/stanford-parser-3.9.2-models.jar'
java_path = "C:/Program Files/Java/jdk1.8.0_181/bin/java.exe"
os.environ['JAVAHOME'] = java_path
dependency_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)

#listes utiles pour regrouper les tags
NOUNS = ['NN', 'NNS', 'NNP', 'NNPS']
VERBS = ['VB', 'VBG', 'VBD', 'VBN', 'VBP', 'VBZ']

#si nécessaire récupère le texte sur internet (uniquement le texte entre balise HTML <p>)
def download_document(url):
    r = requests.get(url) #récupérer le texte 
    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.find('title').get_text()
    document = ' '.join([p.get_text() for p in soup.find_all('p')])
    return document

#enlève les signes de ponctuation (sauf le point) et les stopwords
def clean_document(document):
    document = re.sub('[^A-Za-z .]+', ' ', document)
    document = ' '.join(document.split())
    document = ' '.join([i for i in document.split() if i not in stopWords])
    return document
    
#renvoie les phrases sous forme de liste de liste, avec pour chaque phrase la liste de ses tokens
def tokenize_sentence(document):
    sentences = nltk.sent_tokenize(document) #phrase complètes
    sentences = [nltk.word_tokenize(sent) for sent in sentences] #phrases tokenisées
    return sentences
    
#identique au notebook, utile pour la lemmatisation
def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.ADV  # just use as default, for ADV the lemmatizer doesn't change anything
        
#lemmatize les tokens à l'aide des parties du discours
def lemmatizer(tokens, tagged_tokens):
    wordnet_tags = [get_wordnet_pos(p[1]) for p in tagged_tokens]
    posLemmas = [wnl.lemmatize(t,w) for t,w in zip(tokens,wordnet_tags)]
    return posLemmas
    
#extrait le nom le plus souvent sujet 
def extract_subject(tagged_tokens, dependencies):
    #recherche des noms les plus fréquents
    text = nltk.Text([token for token, tag in tagged_tokens if tag in NOUNS])
    fdist = nltk.FreqDist(text)
    most_freq_nouns =[t for t, f in fdist.most_common(20)]
    #print("NLTK most frequent nouns: ", most_freq_nouns)
    #extraction des sujets
    subjtuples = [tuple for tuple in dependencies if  tuple[1] == 'nsubj' ]
    subjects = [tuple[2][0] for tuple in subjtuples]
    #sujets les plus fréquents
    subjfDist = nltk.FreqDist(nltk.Text(subjects))
    most_freq_subjects = [t for t, f in subjfDist.most_common(10)]
    #print("NLTK most frequent subjects: ", most_freq_subjects)
    #intersection des deux listes
    possible_subjects = [t for t in most_freq_subjects if t in most_freq_nouns]
    #print("NLTK possible subjects: ", possible_subjects)
    if len(possible_subjects)>0:
        return possible_subjects[0]
    else:
        return ("no subject", most_freq_subjects, most_freq_nouns)
        
#extrait le verbe principal
def extract_verb(subject, tagged_tokens, lemmatized_sentences):
    tagged_verbs = [(token,tag) for token, tag in tagged_tokens if tag in VERBS]
    verbs = [tok for tok, tag in tagged_verbs]
    #lemmatise les verbes pour pouvoir compter leur fréquence correctement
    verbs_lemmas = lemmatizer(verbs, tagged_verbs)
    #print("NLTK verbs lemmas: ", verbs_lemmas)
    #verbes les plus courants
    text = nltk.Text(verbs_lemmas)
    fdist = nltk.FreqDist(text)
    most_freq_verbs = [v for v, f in fdist.most_common(10)]
    #print("NLTK most frequent verbs: ", most_freq_verbs)
    #verbes avec le bon sujet
    good_verbs = []
    #lemmatisation du sujet pour avoir plus de chance de le retrouver
    subject_lemma = lemmatizer([subject], nltk.pos_tag([subject]))[0] 
    #extraction des phrases contenant ce sujet
    sentences_with_subject = [sentence for sentence in lemmatized_sentences if subject_lemma in sentence]
    #extraction des verbes de ces phrases
    for sentence in sentences_with_subject:
        good_verbs.extend([verb for verb in most_freq_verbs if verb in sentence])
    #print("NLTK good verbs: ", good verbs)
    if len(good_verbs) != 0:
        # bon verbe le plus courant
        text = nltk.Text(good_verbs)
        fdist = nltk.FreqDist(text)
        final_verb = [v for v, f in fdist.most_common(1)]
        return final_verb[0]
    else:
        return 'No verb found'
        
#extrait une liste de compléments possibles 
def extract_objet(subject, verb, lemmatized_sentences):
    #phrases comprenant le sujet et le verbe trouvés aux étapes précédentes
    interesting_sentences = [sentence for sentence in lemmatized_sentences if subject in sentence and verb in sentence]
    #extraction des noms de ces phrases
    interesting_tokens = [tok for sentence in interesting_sentences for tok in sentence if nltk.pos_tag([tok])[0][1] in NOUNS]
    #on enlève le sujet pour éviter de l'avoir dans les compléments
    interesting_tokens.remove(subject)
    #print("NLTK interesting tokens: ", interesting_tokens)
    #noms les plus courants
    text = nltk.Text(interesting_tokens)
    fdist = nltk.FreqDist(text)
    max_freq = max([f for w, f in fdist.most_common(20)])
    #mots avec la fréquence maximale
    final_objects = [v for v, f in fdist.most_common(20) if f==max_freq]
    return final_objects

#fonction globale qui résume le texte
def summaryTextNLTK(fromInternet, wantedUrl=None, wantedFile=None):
    t0 = time.time() #mesure du temps
    #récupération du texte, soit depuis internet soit par un fichier texte
    if fromInternet :
        url = wantedUrl
        document = download_document(url)
    else : 
        fichier = open(wantedFile, 'r')
        document=fichier.read()
    #nettoyage
    document=clean_document(document)
    #suite du pré traitement avec création des listes utilisées dans les fonctions ci dessus
    tokens = nltk.word_tokenize(document)
    #print("NLTK tokens: ", tokens)
    tagged_tokens = nltk.pos_tag(tokens) #tokens avec POS tagging
    #print("NLTK tagged tokens: ", tagged_tokens)
    complete_sentences = nltk.sent_tokenize(document) #liste des phrases
    #print("NLTK complete sentences: ", complete_sentences)
    tokenized_sentences = tokenize_sentence(document) #liste de listes des tokens des phrases
    #print("NLTK tokenized sentences: ", tokenized_sentences)
    tagged_sentences = [(sentence, nltk.pos_tag(sentence)) for sentence in tokenized_sentences] # POS tagging
    #print("NLTK tagged sentences: ", tagged_sentences)
    lemmatized_sentences = [lemmatizer(sentence, tagged_sentence) for sentence, tagged_sentence in tagged_sentences] #lemmatisation 
    #print("NLTK lemmatized sentences: ", lemmatized_sentences)
    #dependency parsing
    result = dependency_parser.raw_parse_sents(complete_sentences)
    dep = result.__next__().__next__()
    list_dep = list(dep.triples())
    t1 = time.time()
    #extraction du sujet
    subject = extract_subject(tagged_tokens, list_dep)
    #print("NLTK subject: ", subject)
    t2 = time.time()
    #test pour vérifier qu'un sujet a  été trouvé
    if subject[0]=="no subject":
        return "Failed to find subject", None, None, t1-t0, t2-t1, None, None
    #extraction du verbe
    verb = extract_verb(subject, tagged_tokens, lemmatized_sentences)
    #print("NLTK verb: ", verb)
    t3 = time.time()
    #test 
    if verb == 'No verb found':
        return subject, verb, None, t1-t0, t2-t1, None, None
    #extraction des compléments
    objects = extract_objet(subject, verb, lemmatized_sentences)
    #print("NLTK objects: ", objects)
    t4 = time.time()
    #fermeture du fichier si nécessaire
    if not fromInternet: 
        fichier.close()
    return subject, verb, objects, t1-t0, t2-t1, t4-t1, t4-t0

    
