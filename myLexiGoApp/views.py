from django.shortcuts import render, redirect
import spacy
import deepl
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from myLexiGoApp.forms import LoginForm, RegisterForm
from transformers import AutoModel, AutoTokenizer
import itertools
import torch
import os


module_dir = os.path.dirname(__file__)

en_nlp = spacy.load("en_core_web_sm")
fr_nlp = spacy.load("fr_core_news_md")

auth_key = "4b95de03-300f-c18a-c81a-23527d794283:fx"
translator = deepl.Translator(auth_key)

# Create your views here.


def home(request):
    return render(request, 'home.html')


def analyze(request):
    body_unicode = request.body.decode('utf-8')
    colis = json.loads(body_unicode)

    # get the chosen language level
    niveau = str(colis['valNiveau'])

    # get the vocabulary for the chosen level
    file_path = os.path.join(
        module_dir, '../static/lexique/list_'+niveau+'.txt')

    voc = []
    with open(file_path, encoding="utf-8", mode="r") as f:
        for element in f.readlines():
            token = element.strip()
            voc.append(token)

    # define inputs of awesome-align
    src = colis['inText']
    tgt = str(translator.translate_text(src, target_lang="EN-GB"))

    # spacy docs
    src_doc = fr_nlp(src)
    tgt_doc = en_nlp(tgt)

    # load model
    model = AutoModel.from_pretrained("aneuraz/awesome-align-with-co")
    tokenizer = AutoTokenizer.from_pretrained("aneuraz/awesome-align-with-co")

    # model parameters
    align_layer = 8
    threshold = 1e-3

    # pre-processing
    sent_src, sent_tgt = [token. text for token in src_doc], [
        token. text for token in tgt_doc]
    token_src, token_tgt = [tokenizer.tokenize(word) for word in sent_src], [
        tokenizer.tokenize(word) for word in sent_tgt]
    wid_src, wid_tgt = [tokenizer.convert_tokens_to_ids(x) for x in token_src], [tokenizer.convert_tokens_to_ids(x) for x in
                                                                                 token_tgt]
    ids_src, ids_tgt = tokenizer.prepare_for_model(list(itertools.chain(*wid_src)), return_tensors='pt',
                                                   model_max_length=tokenizer.model_max_length, truncation=True)[
        'input_ids'], \
        tokenizer.prepare_for_model(list(itertools.chain(*wid_tgt)), return_tensors='pt', truncation=True,
                                    model_max_length=tokenizer.model_max_length)['input_ids']
    sub2word_map_src = []
    for i, word_list in enumerate(token_src):
        sub2word_map_src += [i for x in word_list]
    sub2word_map_tgt = []
    for i, word_list in enumerate(token_tgt):
        sub2word_map_tgt += [i for x in word_list]

    # alignment
    with torch.no_grad():
        out_src = model(ids_src.unsqueeze(0), output_hidden_states=True)[
            2][align_layer][0, 1:-1]
        out_tgt = model(ids_tgt.unsqueeze(0), output_hidden_states=True)[
            2][align_layer][0, 1:-1]

        dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

        softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
        softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

        softmax_inter = (softmax_srctgt > threshold) * \
            (softmax_tgtsrc > threshold)

    align_subwords = torch.nonzero(softmax_inter, as_tuple=False)
    align_words = set()

    for i, j in align_subwords:
        align_words.add((sub2word_map_src[i], sub2word_map_tgt[j]))

    outText = ""
    for i, j in sorted(align_words):
        if sent_tgt[j] in voc:
            outText = outText + " " + sent_tgt[j]
        else:
            outText = outText + " " + sent_src[i]

    outText = str(outText)

    return JsonResponse({"reponse": outText})

    # JsonResponse({"reponse": output})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # 验证用户名和密码
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # 0 for remembers the user until he closes the browser
                request.session.set_expiry(0)
                return redirect('index')
            else:
                # 登录失败，提示用户名或密码错误
                return render(request, 'login.html', {'form': form, 'error': 'Nom d\'utilisateur ou mot de passe incorrect.'})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('index')


def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 验证用户名、邮箱和密码
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            password_confirm = form.cleaned_data['password_confirm']
            if password != password_confirm:
                # 密码不一致，提示错误
                return render(request, 'register.html', {'form': form, 'error': 'Les deux mots de passe ne correspondent pas, veuillez réessayer !'})
            if User.objects.filter(username=username).exists():
                # 用户名已存在，提示错误
                return render(request, 'register.html', {'form': form, 'error': 'Cet utilisateur existe déjà.'})
            try:
                # 创建新用户
                user = User.objects.create_user(
                    username=username, password=password)
                user.save()
                # 登录新用户
                login(request, user)
                # 重定向到主页
                return redirect('index')
            except Exception as e:
                return render(request, 'register.html', {'form': form, 'error': str(e)})
    else:
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})
