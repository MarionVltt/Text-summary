
import nltkenglish
import spacyNLP
import spacyNLPfr
import time
from importlib import reload
reload(spacyNLPfr)
reload(nltkenglish)
reload(spacyNLP)

def printLists(list):
    for i in range(len(list)):
        print()
        if i<len(files):
            print("texte ", files[i], ": ")
        else:
            print("texte" , french[i-len(files)], ": ")
        print("NLTK: ", list[i][1])
        print("Spacy: ", list[i][2])

files =['Insight.txt', 'Snow.txt', 'SpongeBob.txt', 'FrenchRiots.txt', 'Raptors.txt', 'HarryPotter.txt', '1984.txt']
french=['Insightfr.txt', 'Bobleponge.txt', ]
urls = [] #à compléter si texte venant d'internet, exemple : urls=['https://globalnews.ca/news/4698899/mars-landing-2018-nasa-insight/']

summaries=[] #résumés
timesPreprocessing = [] #pré traitement
timesSubject=[] #temps pour trouver seulement le sujet
timesSentence = [] #temps pour la phrase complète
timesComplete = [] #temps du code complet

for i in range(len(files)):
    summarySpacy = spacyNLP.summaryTextSpacy(False, wantedFile=files[i])
    summaryNLTK = nltkenglish.summaryTextNLTK(False, wantedFile=files[i])
    summaries.append((i, summaryNLTK[0:3], summarySpacy[0]))
    timesPreprocessing.append((i,  summaryNLTK[3],  summarySpacy[1]))
    timesSubject.append((i, summaryNLTK[4],  summarySpacy[2]))
    timesSentence.append((i, summaryNLTK[5],  summarySpacy[3]))
    timesComplete.append((i, summaryNLTK[6],  summarySpacy[4]))
for i in range(len(french)):
    summarySpacyfr = spacyNLPfr.summaryTextSpacyfr(False, wantedFile=french[i])
    summaries.append((i, None, summarySpacyfr[0]))
    timesPreprocessing.append((i,  None,  summarySpacyfr[1]))
    timesSubject.append((i, None,  summarySpacyfr[2]))
    timesSentence.append((i, None,  summarySpacyfr[3]))
    timesComplete.append((i, None,  summarySpacyfr[4]))
    
print("Summaries:")
printLists(summaries)
print()
print("Times for the preprocessing:")
printLists(timesPreprocessing)
print()
print("Times for the subject:")
printLists(timesSubject)
print()
print("Times for the complete sentence:")
printLists(timesSentence)
print()
print("Times for the complete code:")
printLists(timesComplete)
