
from flask import Flask, render_template, request, make_response, session
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import random
import json
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import smtplib
from sendMail import send_mail

PORT = 5555

client = MongoClient("mongodb://keremyldrr:risk@ds155218.mlab.com:55218/risk")
db = client['risk']
from Game import RiskGame

app = Flask(__name__)
app.config['SECRET_KEY'] = "katmer"
socketio = SocketIO(app)
CORS(app)
userlist = []
runningGames = []
gameID = 0


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("in")
    users = db.users
    user = json.loads(request.data.decode('utf-8'))

    login_user = users.find_one({'name': user["username"]})
    password = user['password'].encode('utf-8')
    if userlist.count(user["username"]) == 0:
        if login_user and (len(userlist) <= 6):
            if bcrypt.hashpw(password, login_user['password']) == login_user['password']:
                print(user["username"] + "logged in")
                userlist.append(user["username"])
                print("current users" + str(userlist))

                return "True"

    return 'False'


def gameFinder(gID):
    global runningGames
    for gm in runningGames:
        if gID == gm.gID:
            return gm


@socketio.on('unitAdded')
def addUnit(item, gID):
    print("units added")
    gm = gameFinder(gID)
    msg = gm.addUnit(item)
    emit('unitAdded', msg, broadcast=True)


@app.route('/register', methods=['POST', 'GET'])
def check_register():
    print("registerinng")
    users = db.users
    print("TRYING")
    user = json.loads(request.data.decode('utf-8'))

    print(request.data)
    existing_user = users.find_one({'name': user['username']})
    avatar = user["avatar"]
    av = avatar["value"]

    if existing_user is None:
        hashy = bcrypt.hashpw(user['password'].encode('utf-8'), bcrypt.gensalt())
        users.insert(
            {'name': user['username'], 'password': hashy, 'email': user['email'], 'wins': 0, "avatar": av, "EXP": "0",
             "LEVEL": "1"})
        session['username'] = user['username']

        return "True"

    return 'False'

@socketio.on('availableGames')
def gamelist(e):
	tempy = []
	for gm  in runningGames:
		if gm.state == "Pending":
			tempy.append(gm.gID)
	emit('getGames',tempy)
	print("attim")

@socketio.on('createOrJoin')
def createOrJoin(uname):
    global gameID, runningGames
    tempy = RiskGame(gameID)
    gameID += 1
    print(uname)
    tempy.userlist.append(uname)
    runningGames.append(tempy)
    emit('changeCreateOrJoin', [tempy.gID, "Changed create to join or vice versa"])
    emit('renkVer',[tempy.gID,tempy.userlist],broadcast=True)

########################
@socketio.on('join')
def join(data):
    df = data.split(' ')
    user = df[0]

    print(df[0], df[1])

########################
@socketio.on('leave')
def leave(data):
    df = data.split(' ')
    user = df[0]
    room = df[1]
    leave_room(room)
    emit('leave', user + " has left the room.", room=room)

########################
@socketio.on('savedState')
def saved_State(name, map, uname, gID):
    gm = gameFinder(gID)
    obj = gm.saved_State(name, map, uname)
    emit('startVote', obj, broadcast=True)


@socketio.on('vote')
def voting(e, gID):
    gm = gameFinder(gID)
    res = gm.vote(e)
    if str(res) != "None":
    	if not res[1]:
        	emit('message', [res[0], 'Voting conflict. Game not saved'], broadCast=True)
    	else:
        	emit('message', [res[0], 'Game saved.'], broadCast=True)
        	db.Saved_Games.insert_one(res[1])
        	print("game saved")


@socketio.on('loadFromLobby')
def loaderLobby(e, gID):
    gm = gameFinder(gID)
    print(e)
    gm.isLoading = True
    game = ""
    #	testy = sorted(userlist)
    for theGame in db.Saved_Games.find():
        userss = theGame["userlist"]
        if sorted(userss) == sorted(gm.userlist):
            game = theGame
            gm.turn = theGame["turn"]
            delID = theGame["_id"]
            gm.loaded = game["mapState"]

            gm.userlist = userss
            break

    emit('yallah', [gm.gID, "go"], broadcast=True)
    gm.state="Playing"
    turner(gm.gID)  #### DO NOT FORGETTTTTTT
    db.Saved_Games.remove({"_id": delID})


@socketio.on('newNewClient')
def newNewlient(item, gID):
	if str(gID) == "None":
		emit('newClient',"nullgeldi")
	else:
		gm = gameFinder(gID)
		print("in new client")
		print(gm.userlist)
		emit('newClient', [gID, gm.userlist], broadcast=True)


@socketio.on("message")
def msg(mssg, gID):
    gm = gameFinder(gID)
    print("msg:", mssg)
    test =mssg.find(':')
    test2 =mssg.find('@')
    name = mssg[test+1:test+3]
    print(name)
    if name == "/w":
        print("whisper",mssg[test +1:test2])
        emit('message', [gID, "Whisper from " + mssg[0:test-1] +":  " +  mssg[test2+1:],mssg[test+3:test2]], broadcast=True)
    else:
        emit('message', [gID, mssg,0], broadcast=True)

@socketio.on('countries')
def assign(e, gID):
    gm = gameFinder(gID)
    if len(gm.countries) == 0:
        gm.assign(e)
        emit('yallah', [gm.gID, "go"], broadcast=True)
        gm.state="Playing"
        turner(gID)  #### DO NOT FORGETTTTTTT#### DO NOT FORGETTTTTTT#### DO NOT FORGETTTTTTT


@socketio.on('ownerAssignServer')
def ownerAssignServer(e, gID):
    gm = gameFinder(gID)
    emit('ownerAssign', [gm.gID, gm.countries])
    print("sending loaded state")

    if gm.isLoading == True and str(gm.loaded) != "None":
        emit("load", [gm.gID, gm.loaded], broadcast=True)


@socketio.on('hiddenturn')
def turner(gID):
    gm = gameFinder(gID)
    obj = gm.turner()
    emit('hidden', obj, broadcast=True)


@socketio.on('setCountries')
def setCountry(item, gID):
    gm = gameFinder(gID)
    print('Setting Countries', item)
    emit('setCountriesBro', [gm.gID, item], broadcast=True)


@socketio.on('unitMove')
def unitMover(e, gID):
    gm = gameFinder(gID)
    obj = gm.unitMover(e)
    emit("unitMoved", obj, broadcast=True)


@socketio.on('reset')
def resettter(gID):
    print("RESETTING")
    gm = gameFinder(gID)
    for us in gm.userlist:
        userlist.remove(us)
    gm.reset()


@socketio.on('unitAttack')
def attack(item, gID):
    gm = gameFinder(gID)
    print(item)
    obj = gm.attack(item)
    print(obj)
    emit('unitAttacked', obj, broadcast=True)


@socketio.on("disconnect")
def discoct():
	print("disconnected")

#@socketio.on("check")
def check(name):
    global nonDisconnectors

    if name != None:
        print(name)
        nonDisconnectors.append(name)


@socketio.on('unitNuke')
def send_nukes(attackVals, gID):
    print("Someone is nuking")
    gm = gameFinder(gID)
    obj = gm.unitNuke(attackVals)
    emit('unitNuked', obj, broadcast=True)


@socketio.on('unitWololo')
def wololooo(wololos,gID):
    print("WOLOLOOOOOOO")
    gm = gameFinder(gID)
    obj = gm.wololooo(wololos)
    emit('unitWololoed', obj, broadcast=True)


@socketio.on('paratrooperLanding')
def parapara(paras,gID):
    print("paraaaaaa")
    gm = gameFinder(gID)
    obj = gm.parapara(paras)
    emit('paratrooperLanded', obj, broadcast=True)


@socketio.on("ready")
def ready(e, gID):
    print("git burdan")
    emit("go", [gID, "git burdan"], broadcast=True)


@socketio.on('giveMeUsers')
def give_me_users(e):
    tempy_listy = []
    print("giving users")
    users = db.users
    for user in users.find():
        obj = {"name": user["name"], "avatar": user["avatar"]}
        tempy_listy.append(obj)
    emit('receiveUserList', (tempy_listy))


@socketio.on('gameIsFinish')
def finished(e, gID):
    gm = gameFinder(gID)
    gm.reset()
    usrr = db.users.find_one({"name":e})
    exp = int(usrr["EXP"]) + 100
    win = int(usrr["wins"]) + 1
    db.users.update({ "name" :e },{ "$set": { "EXP" : exp } })
    db.users.update({ "name" :e },{ "$set": { "wins" : win } })

    emit('gameIsFinished', [gm.gID, 'Winner is ' + e], broadcast=True)

@socketio.on('takeMe')
def takeme(uname,gID):
	gm = gameFinder(int(gID))
	gm.userlist.append(uname)
	print("taking you")
	emit('iTookU',"")
	emit('message',[gID,uname + " joined the game"],broadcast=True)
	emit('renkVer',[gm.gID,gm.userlist],broadcast=True)

@socketio.on('callToArm')
def callToAtm(item,gID):
	gm = gameFinder(gID)
	obj = [gID,item]
	emit('callToArmed',obj,broadcast = True)
@socketio.on("roulette")
def rulette(item,gID):
	gm =gameFinder(gID)
	obj = [gID,item]
	emit("rouletted",obj,broadcast = True)
@socketio.on('avatarVerAllam')
def avatatrt(uname):
	print("veriyom")
	user =  db.users.find_one({"name":uname})
	print(user)
	avatar = user["avatar"]
	exp = user["EXP"]
	win = user["wins"]
	print(avatar)
	emit("avatarVer",[avatar,exp,win])




@socketio.on('inviteRequest')
def sendy(uname,gID):
	usr = db.users.find_one({"name":uname})
	print(usr)
	mail = usr["email"]
	send_mail(mail,"We are playing, come immediately!.\n Game ID is is "+str(gID))
	print("sent")
if __name__ == "__main__":
    print("running on " + str(PORT))
    socketio.run(app, host='0.0.0.0', port=PORT)
    # app.run(host='0.0.0.0')

