APP_VERSION = 0.18
import vk_api
from requests import post, get
import time
import json
import sys
from vk_api import upload
from vk_api.longpoll import VkLongPoll, VkEventType
from random import choice
from colorama import init, Fore
init()

CHECK_UPDATE_DELAY = 300
TOKEN_DELAY = 600

def loadData() -> dict:
    with open('data.json', 'r') as f:
        data = json.load(f)
    return data

def dumpData(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent = 4)
    return

dumpData({
    "tokenDelays": {},
    "tokensOnDelay": [],
    "checkUpdateDelay": 0
})

def installUpdate():
    r = get('https://raw.githubusercontent.com/insan1tyyy/comments/main/comments.py').text
    r = r.replace('\r', '')
    with open('comments.py', 'w', encoding='utf-8') as f:
        f.write(r)
    print(f"{Fore.CYAN}Обновление успешно установлено! Запусти скрипт заново.")
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

def checkUpdateNotification():
    data = loadData()
    if time.time() - data['checkUpdateDelay'] < CHECK_UPDATE_DELAY:
        return
    r:str = get('https://raw.githubusercontent.com/insan1tyyy/comments/main/comments.py').text
    r = r.split('\r\n', maxsplit=1)[0]
    app_ver = float(r.replace('APP_VERSION = ', ''))
    if APP_VERSION < app_ver:
        print(f"\n\n\n{Fore.BLUE}Доступно обновление. Перезапусти скрипт, чтобы инициализировать установку!\n\n\n")
    
    data['checkUpdateDelay'] = int(time.time())
    dumpData(data)
    return

with open('config.json', 'r') as f:
    config = json.load(f)

def newCaptchaUserId() -> int:
    userId = input("Чтобы пропустить этот этап - оставь поле пустым.\nВведи ссылку на пользователя, кому отправлять капчу\nОбработка капчи работает только в режиме одного токена!!\n>>> ").split('.com/')[1]
    if not userId or userId == '0':
        return 0
    if type(config['token']) == type([1,2,3]):
        token = config['token'][0]
    else:
        token = config['token']
    return vk_api.VkApi(token=token).get_api().users.get(user_ids=userId)[0]['id']


def login():
    while True:
        token = input("Введи токен от страницы. Если хочешь использовать несколько токенов, впиши их, разделив знаком ;\n\n>>> ")
        if ';' in token:
            tokens = token.replace(' ', '').split(';')
            success = []
            for token in tokens:
                try:
                    vk = vk_api.VkApi(token=token).get_api()
                    vk.wall.get()
                    success.append(token)
                except vk_api.exceptions.VkApiError as e:
                    if e.error['error_msg'] == 'Group authorization failed: method is unavailable with group auth.':
                        pass
                    else:
                        print(f'{Fore.RED}Неверный токен. {token}')
                        continue
                try:
                    user = vk.users.get()[0]
                    name = '{} {}'.format(user['first_name'], user['last_name'])
                    print(f'{Fore.YELLOW} Успешная авторизация как {name} !\n')
                except IndexError:
                    print(f'{Fore.YELLOW} Успешная авторизация токеном паблика {token}')
            return success
        else:
            try:
                user = vk_api.VkApi(token=token).get_api().users.get()[0]
                name = '{} {}'.format(user['first_name'], user['last_name'])
                print(f'{Fore.YELLOW} Успешная авторизация как {name} !')
                return token

            except vk_api.exceptions.VkApiError:
                print(f'{Fore.RED}Неверный токен.')
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

def answerCaptcha():
    a = input("Если хочешь вставить новый АЙДИ чата для капчи, введи любой символ, иначе нажми ENTER, оставив поле пустым.\n\n>>> ")
    if a:
        config['captchaTo'] = newCaptchaUserId()
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

if not config.get('captchaTo', None):
    config['captchaTo'] = newCaptchaUserId()
    with open('config.json', 'w') as f:
        json.dump(config, f, indent = 4)
else:
    answerCaptcha()

def sendCaptcha(vk, captcha):
    r = open("captcha.jpg", "wb")
    r.write(get(captcha.url).content)
    r.close()
    load = upload.VkUpload(vk)
    captchaPhoto = load.photo_messages(peer_id=config['captchaTo'], photos='captcha.jpg') 
    vk.messages.send(peer_id = config['captchaTo'], random_id = 0, message = 'Отправьте код с картинки следующим образом:\n!get 123code', attachment = 'photo' + str(captchaPhoto[0]['owner_id']) + '_' + str(captchaPhoto[0]['id']))
    return

def processCaptcha(token, captcha):
    vk_session = vk_api.VkApi(token=token)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    sendCaptcha(vk, captcha)
    startCaptcha = int(time.time())
    while True:
        for event in longpoll.listen():
            if time.time() - startCaptcha == 900:
                print("Ответа на капчу не было получено.")
                return
            if event.type == VkEventType.MESSAGE_NEW:
                if '!get' in event.text and not event.from_me:
                    print("Ответ на капчу принят, код:" + event.text.replace('!get ', ''))
                    return captcha.try_again(event.text.replace('!get ', ''))



def multiTokenSupport():
    
    post_id = vk_api.VkApi(token=config['token'][0]).get_api().wall.get()['items'][0]['id']
    user_id = vk_api.VkApi(token=config['token'][0]).get_api().users.get()[0]['id']
    start = time.time()
    commentList = config['comments']
    print(f'\n\n{Fore.MAGENTA}Начинаю накрутку...')
    while True:
        checkUpdateNotification()
        for token in config['token']:
            data:dict = loadData()
            if token in data['tokensOnDelay']:
                if time.time() - data['tokenDelays'][token] > TOKEN_DELAY:
                    data['tokensOnDelay'].remove(token)
                    data['tokenDelays'].pop(token)
                    print(f'{Fore.GREEN}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.GREEN}] {token} out from delay!')
                    dumpData(data)
                else:
                    continue
            vk = vk_api.VkApi(token=token).get_api()
            msg = choice(commentList)
            try:
                vk.wall.createComment(post_id = post_id, message = msg, owner_id = user_id)
                print(f'{Fore.GREEN}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.GREEN}] Comment added: "{msg}" comment count: ' + str(vk.wall.get(owner_id = user_id)['items'][0]['comments']['count']))
            except vk_api.exceptions.Captcha as captcha:
                
                # captchaTries += 1
                # if captchaTries < 3:
                #     captchaTries = 0
                #     print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: CAPTCHA. wait captcha answer...')
                #     processCaptcha(token)
                #     pass
                print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: CAPTCHA. set {TOKEN_DELAY}s delay...')
                data['tokensOnDelay'].append(token)
                data['tokenDelays'][token] = int(time.time())
                dumpData(data)
                continue
            except vk_api.exceptions.ApiError as e:
                print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: ' + e.error['error_msg'] + f'. trying to sleep 300s... (token: {token})')

def singleTokenSupport():


    vk = vk_api.VkApi(token=config['token']).get_api()
    post_id = vk.wall.get()['items'][0]['id']

    start = time.time()
    commentList = config['comments']
    print(f'\n\n{Fore.MAGENTA}Начинаю накрутку...')
    captchaTries = 0
    while True:
        checkUpdateNotification()
        msg = choice(commentList)
        try:
            vk.wall.createComment(post_id = post_id, message = msg)
            captchaTries = 0
            print(f'{Fore.GREEN}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.GREEN}] Comment added: "{Fore.CYAN}{msg}{Fore.GREEN}" comment count: ' + str(vk.wall.get()['items'][0]['comments']['count']))
        except vk_api.exceptions.Captcha as captcha:
            if not config['captchaTo'] or config['captchaTo'] == '0':
                print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: CAPTCHA. trying to sleep 300s...')
                time.sleep(300)
                continue
            captchaTries += 1
            if captchaTries >= 3:
                print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: Капча отправлена в выбранный чат, ожидаю ответа 900сек...')
                if not processCaptcha(config['token'], captcha):
                    continue
                else:
                    captchaTries = 0
                    continue
            print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: CAPTCHA. trying to sleep 300s...')
            time.sleep(300)
        except vk_api.exceptions.ApiError as e:
            print(f'{Fore.RED}[{Fore.YELLOW}' + str(round(time.time() - start, 3)) + f'{Fore.RED}] Comment error: ' + e.error['error_msg'] + f'. trying to sleep 300s...')

def startFunc():
    if type(config['token']) == type([1,2,3]):
        multiTokenSupport()
    else:
        singleTokenSupport()


startFunc()




