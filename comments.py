APP_VERSION = 0.12
import vk_api
from requests import post, get
import time
import json
import sys
from random import choice

def installUpdate():
    r = get('https://raw.githubusercontent.com/insan1tyyy/comments/main/comments.py').text
    r = r.replace('\r', '')
    with open('comments.py', 'w', encoding='utf-8') as f:
        f.write(r)
    print("Обновление успешно установлено! Запусти скрипт заново.")
    exit()

def checkUpdates():
    r:str = get('https://raw.githubusercontent.com/insan1tyyy/comments/main/comments.py').text
    r = r.split('\r\n', maxsplit=1)[0]
    app_ver = float(r.replace('APP_VERSION = ', ''))
    if APP_VERSION < app_ver:
        confirm = input("Доступно обновление. Чтобы установить - нажми ENTER, Чтобы пропустить - напиши любой символ")
        if not confirm:
            installUpdate()
        else:
            return

checkUpdates()


with open('config.json', 'r') as f:
    config = json.load(f)

def login():
    while True:
        token = input("Введи токен от страницы. Если хочешь использовать несколько токенов, впиши их, разделив знаком ;\n\n>>> ")
        if ';' in token:
            tokens = token.replace(' ', '').split(';')
        else:
            try:
                user = vk_api.VkApi(token=token).get_api().users.get()[0]
                name = '{} {}'.format(user['first_name'], user['last_name'])
                print(f'Успешная авторизация как {name} !')
                return token

            except vk_api.exceptions.VkApiError:
                print('Неверный токен.')
                continue

def newComments() -> list:
    comments = input("Введи новый текст для комментов. Чтобы разделить текст, поставь ; (Пример: Hello world; Bye world; i want some candies)\n\n>>> ").split(';')
    return comments

def answerComments():
    a = input("Если хочешь вставить новый текст для комментариев, введи любой символ, иначе нажми ENTER, оставив поле пустым.\n\n>>> ")
    if a:
        config['comments'] = newComments()
        with open('config.json', 'w') as f:
            json.dump(config, f, indent = 4)
        return
    else:
        return

def answerTokens():
    a = input("Если хочешь вставить новые токены, введи любой символ, иначе нажми ENTER, оставив поле пустым.\n\n>>> ")
    if a:
        config['token'] = login()
        with open('config.json', 'w') as f:
            json.dump(config, f, indent = 4)
        return
    else:
        return

if not config['token']:
    config['token'] = login()
    with open('config.json', 'w') as f: 
        json.dump(config, f, indent = 4)
else:
    answerTokens()


if not config['comments']:
    config['comments'] = newComments()
    with open('config.json', 'w') as f:
        json.dump(config, f, indent = 4)
else:
    answerComments()



def multiTokenSupport():
    
    post_id = vk_api.VkApi(token=config['token'][0]).get_api().wall.get()['items'][0]['id']
    user_id = vk_api.VkApi(token=config['token'][0]).get_api().users.get()[0]['id']
    start = time.time()
    commentList = config['comments']
    print('\n\nНачинаю накрутку...')
    while True:
        for token in config['token']:
            vk = vk_api.VkApi(token=token).get_api()
            msg = choice(commentList)
            try:
                vk.wall.createComment(post_id = post_id, message = msg, owner_id = user_id)
                print(f'[' + str(round(time.time() - start, 3)) + f'] Comment added: "{msg}" comment count: ' + str(vk.wall.get()['items'][0]['comments']['count']))
            except vk_api.exceptions.Captcha as e:
                print(f'[' + str(round(time.time() - start, 3)) + f'] Comment error: CAPTCHA. skip to next token...')
                continue

def singleTokenSupport():
    vk = vk_api.VkApi(token=config['token']).get_api()
    post_id = vk.wall.get()['items'][0]['id']

    start = time.time()
    commentList = config['comments']
    print('\n\nНачинаю накрутку...')
    while True:
        msg = choice(commentList)
        try:
            vk.wall.createComment(post_id = post_id, message = msg)
            print(f'[' + str(round(time.time() - start, 3)) + f'] Comment added: "{msg}" comment count: ' + str(vk.wall.get()['items'][0]['comments']['count']))
        except vk_api.exceptions.Captcha as e:
            print(f'[' + str(round(time.time() - start, 3)) + f'] Comment error: CAPTCHA. trying to sleep 300s...')
            time.sleep(300)

def startFunc():
    if type(config['token']) == type([1,2,3]):
        multiTokenSupport()
    else:
        singleTokenSupport()


startFunc()




