from django.shortcuts import render, redirect
import spacy
import deepl
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from myLexiGoApp.forms import LoginForm, RegisterForm


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


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # 验证用户名和密码
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # 登录成功，重定向到主页
                login(request, user, remember=True)
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
