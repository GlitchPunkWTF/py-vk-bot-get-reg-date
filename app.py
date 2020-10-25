from flask import Flask, request, json
import vk
import random
import requests
import datetime

confirmation_token = "token"
group_id_const = 0
secret_const = "token"
access_token = "token"

nkb = {'buttons':[],'one_time':True}

kb = {
'one_time': False,
'buttons':
    [
        [
            {
                'action': {
                    'type': 'text',
                    'payload': '{"command": "placeholder"}',
                    'label': 'Узнать дату регистрации'
                },
                'color': 'primary'
            }
        ],
        [
            {
                'action': {
                    'type': 'text',
                    'payload': '{"command": "datareg"}',
                    'label': 'меня'
                },
                'color': 'positive'
            },
            {
                'action': {
                    'type': 'text',
                    'payload': '{"command": "datafriend"}',
                    'label': 'друга'
                },
                'color': 'negative'
            }
        ]
    ]
}

msgtemp = '''Пользователь: {0}
Аккаунт зарегистрирован: {1} в {2} (по МСК)

Аккаунт существует примерно {3} лет {4} месяцев {5} дней
С точностью до недель: {6} лет {7} недель {8} дней
{9} часов {10} минут {11} секунд'''

app = Flask(__name__)

session = vk.Session(access_token=access_token)
api = vk.API(session, v='5.103')

def regday(var_id):
    url = 'https://vk.com/foaf.php?id='+str(var_id)
    headers = {"Accept-Language": "ru-RU,ru;q=0.75"}
    response = requests.get(url, headers=headers)
    text = response.text
    name = text[text.find('<foaf:name>')+11:text.find('</foaf:name>')]
    num = text.find('<ya:created')
    text = text[(num+21):(num+46)]
    dt = datetime.datetime.strptime(text[:19], '%Y-%m-%dT%H:%M:%S')
    dtn = datetime.datetime.utcnow()

    offset = datetime.timedelta(hours=int(text[21:22]))

    if text[19] == '+':
        dt -= offset
    elif text[19] == '-':
        dt += offset
    else:
        return "Ошибка"

    time = dtn - dt
    all_days = time.days
    secs = time.seconds
    years = round(all_days//365.25)
    weeks = round(all_days%365.25//7)
    days  = round(all_days%365.25%7)
    hours = round(secs//3600)
    minutes = round(secs%3600//60)
    seconds = round(secs%3600%60)

    monr = round(all_days%365.25//30.4375)
    dayr = round(all_days%365.25%30.4375)

    return msgtemp.format(name, dt.date(),dt.time(),
        years,monr,dayr,years, weeks,days,hours,minutes,seconds)

def msgsend(peer_id, text, keyboard):
    api.messages.send(peer_id=peer_id, message=text,
                random_id=random.randint(0,0x7fffffffffffffff), keyboard=json.dumps(keyboard))

def getid(url):
    name = url[url.find('vk.com/')+7:]
    if '[id' in url:
        uid = url[url.find('[id')+3:]
        return uid[:url.find('|@')]
    return api.users.get(user_ids=name, fields='id')[0]['id']

def msg_hndlr(obj):
    msg = obj.get('message')
    if msg:
        msg_id = msg['id']
        peer_id = msg['peer_id']
        txt = msg['text']
        text = 'Бот пришлет дату регистрации во ВКонтакте'
        attachments = msg.get('attachments')
        if attachments:
            mtype = attachments[0].get('type')
            uid = []
            if mtype == 'link':
                url = attachments[0]['link']['url']
                uid = getid(url)
            elif mtype == 'wall':
                uid = attachments[0]['wall']['from_id']
            elif mtype == 'photo':
                uid = attachments[0]['photo']['owner_id']
            elif mtype == 'audio':
                audio = attachments[0]['audio'].get('url')
                if audio:
                    msgsend(peer_id, audio, kb)
                else:
                    msgsend(peer_id, 'Ссылка не существует', kb)
                return
            else:
                api.messages.markAsRead(start_message_id=msg_id, peer_id=peer_id)
                return
            if uid:
                msgsend(peer_id, regday(uid), kb)
                return
        fwd = msg.get('fwd_messages')
        if fwd:
            uid = fwd[0].get('from_id')
            if uid:
                msgsend(peer_id, regday(uid), kb)
                return
        payload = msg.get('payload')
        if payload:
            payload = json.loads(payload)
            cmd = payload.get('command')
            if cmd == 'start':
                text = 'Стааартуем'
            elif cmd == 'placeholder':
                return
            elif cmd == 'datareg':
                msgsend(peer_id, regday(peer_id), kb)
                return
            elif cmd == 'datafriend':
                text = 'Пришли ссылку на страницу друга, nametag или перешли его сообщение или пост'
        if not(text):
            text = 'Высылаю клавиатуру'
        if txt.lower() == 'удали':
            msgsend(peer_id, 'Клавиатура удалена', nkb)
        elif ('vk.com/' in txt.lower()) or ('[id' in txt.lower()):
            msgsend(peer_id, regday(getid(txt.lower())), kb)
        else:
            msgsend(peer_id, text, kb)

@app.route('/')
def hello_world():
    return 'Hello world!'

@app.route('/handler', methods=['POST', 'GET'])
def main():
    if request.is_json:
        content = request.get_json()
#        with open('/home/progbot/mysite/flask.txt', 'w') as f:
#            f.write(str(content))
        rtype = content.get('type')
        group_id = content.get('group_id')
        secret = content.get('secret')
        if rtype:
            if group_id == group_id_const and secret == secret_const:
                if rtype == 'confirmation':
                    return confirmation_token
                elif rtype == 'message_new':
                    msg_hndlr(content.get('object'))
                    return 'ok'
                else:
                    return 'invalid type'
        else:
            return 'null'
    else:
        return 'Error 404'

#@app.route('/log')
#def logdata():
#    with open('/home/progbot/mysite/flask.txt', 'r') as f:
#            return f.read()
#    return 'Hello world!'
