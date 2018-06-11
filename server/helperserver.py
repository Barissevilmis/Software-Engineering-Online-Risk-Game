from flask import Flask, render_template, request, make_response, session
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import random
import json
from flask_socketio import SocketIO, emit, send
from User import User
PORT = 5000
client = MongoClient("mongodb://keremyldrr:risk@ds155218.mlab.com:55218/risk")
db = client['risk']
onlinelist = []
howMany = 0
app = Flask(__name__)
app.config['SECRET_KEY'] = "katmer"
socketio = SocketIO(app)
CORS(app)
userlist = []
user_limit = 0
countries = []
color = ["#2ccce4", "#f47373", "FCB900", "00D084", "FFEB3B", "#ba68c8"]
turn = 0
firstTurnFinished = False
cycle = False
nonDisconnectors = []
voteCount = 0
votedYes = 0
loaded = ""
@app.route('/login', methods=['GET', 'POST'])
def login():
    print("in")
    users = db.users
    user = json.loads(request.data.decode('utf-8'))

    login_user = users.find_one({'name': user["username"]})
    print(userlist)
    password = user['password'].encode('utf-8')
    if userlist.count(user["username"]) == 0:
        if login_user and (len(userlist) <= 6):
            if bcrypt.hashpw(password, login_user['password']) == login_user['password']:
                print(user["username"])
                userlist.append(user["username"])
                return "True"

    return 'False'


def convertJson(mylist):
    jsons = []
    for item in mylist:
        jsons.append({"name": item.name})
    print(jsons)
    return jsons


@socketio.on('addUsers')
def handle_message(message):
    for user in message:
        userlist.append(User(user))
    tobesent = convertJson(userlist)
    emit('game', tobesent)


@socketio.on('login')
def handle_lobby(uname):
    socketio.emit('uname', uname, )


@socketio.on('unitAdded')
def addUnit(item):
    print("you sent smthing")
    print(item)
    socketio.emit('unitAdded', item)


@app.route('/register', methods=['POST', 'GET'])
def check_register():
    print("registerinng")
    users = db.users
    print("TRYING")
    user = json.loads(request.data.decode('utf-8'))

    print(request.data)
    existing_user = users.find_one({'name': user['username']})

    if existing_user is None:
        hashy = bcrypt.hashpw(user['password'].encode('utf-8'), bcrypt.gensalt())
        users.insert({'name': user['username'], 'password': hashy, 'wins': 0})
        session['username'] = user['username']

        return "True"

    return 'False'

@socketio.on('saveGame')
def startVote(e):
	global voteCount,votedYes
	print("saving game")
	emit('message',e + "started a vote for saving the game.")
	voteCount+=1
	votedYes+=1
@socketio.on('savedState')
def saved_State(map):
	global loaded
	loaded = map
	print("loaded this : " +map)


@socketio.on('newClient')
def newClient(item):
    print(userlist)

    emit('newClient', userlist, broadcast=True)
    evaluate()


"""
@socketio.on('Username')
def userName():
    emit('Username', session['username'])"""


@socketio.on('howMany')
def many_many(num):
    user_limit = num
    print("game size is :", num)
    emit('howMany', "True")


def evaluate():
    print("evaluating")
    if len(onlinelist) == user_limit:
        emit('evaluate', "True")
    else:
        emit('evaluate', "False")

@socketio.on("message")
def msg(e):
	print("msg:",e)
	emit('message',e,broadcast=True)
@socketio.on('countries')
def assign(e):
    global countries
    if len(countries) == 0:
        iter = int(42 / len(userlist))
        for i in userlist:
            for it in range(iter):
                countries.append(i)
        random.shuffle(countries)
        offset = len(countries) - iter * len(userlist)
        for i in range(offset):
            countries.append(userlist[i])
        emit('yallah', "go", broadcast=True)
        turner("lol")
    if loaded  != "":
        print("sending loaded state")
        emit("load",loaded)


@socketio.on('ownerAssignServer')
def oo(e):
    print(e)
    emit('ownerAssign', countries)


@socketio.on('hiddenturn')
def turner(e=None):
    global turn, firstTurnFinished, cycle, nonDisconnectors, userlist,loaded
    to_be_deleted = []

    if len(nonDisconnectors) != 0:
        print("userlist_before", userlist)
        for i in range(len(userlist)):
            if nonDisconnectors.count(userlist[i]) == 0:
                to_be_deleted.append(userlist[i])
        for temp in to_be_deleted:
            userlist.remove(temp)
        print("userlist_now", userlist)
        if turn == len(userlist):
            turn = 0
    print("PLAY ", userlist[turn])
    msg = ""
    if cycle == True:
        msg = "no" + userlist[turn]
    else:
        msg = "ye" + userlist[turn]
    emit('hidden', msg, broadcast=True)
    print(msg, len(userlist), turn)
    turn = (turn + 1)  # % len(userlist)
    if turn == len(userlist):
        turn = 0
        cycle = True

@socketio.on('setCountries')
def setCountry(item):
    print('Setting Countries', item)
    emit('setCountriesBro', item, broadcast=True)


@socketio.on('unitMove')
def unitMover(e):
    print("in", e)
    emit("unitMoved", e, broadcast=True)


@socketio.on('reset')
def resettter():
    print("RESETTING")
    global userlist, countries, turn, cycle
    userlist = []
    countries = []
    turn = 0
    cycle = False


@socketio.on('unitAttack')
def attack(item):
    print(item)
    emit('unitAttacked', item, broadcast=True)


@socketio.on("disconnect")
def disconnect():
    global nonDisconnectors
    print("disconnected")
    emit("discon", "opucuk", broadcast=True)
    nonDisconnectors = []


@socketio.on("check")
def check(name):
    global nonDisconnectors

    if name != None:
        print(name)
        nonDisconnectors.append(name)

@socketio.on("ready")
def ready(e):
    print("git burdan")
    emit("go","git burdan")
if __name__ == "__main__":
    print("running")
    socketio.run(app, host='0.0.0.0', port=PORT)
    # app.run(host='0.0.0.0')
