from django.shortcuts import render
import spacy
import deepl
import json
from django.http import JsonResponse

nlp = spacy.load("fr_core_news_md")

auth_key = "4b95de03-300f-c18a-c81a-23527d794283:fx"
translator = deepl.Translator(auth_key)

# Create your views here.
def home(request):
    return render(request, 'home.html')

def analyze(request):
    colis = json.loads(request.body)
    texte = colis['inText']

    output = translator.translate_text(texte, target_lang="EN-GB")

    return JsonResponse({"reponse": output.text})
    
    # JsonResponse({"reponse": output})
