
import random


class RiskGame:
    def __init__(self, id):
        self.gID = id
        self.saveGameName = ""
        self.userlist = []
        self.countries = []
        self.turn = 0
        self.firstTurnFinished = False
        self.cycle = False
        self.nonDisconnectors = []
        self.voteCount = 0
        self.votedYes = 0
        self.loaded = ""
        self.isLoading = False
        self.state = "Pending"
    def addUnit(self, item):
        print("units added")
        arr = [self.gID, item]
        return arr

    def saved_State(self, name, map, uname):

        self.loaded = map
        self.savedGameName = name

        print("map received with name " + str(name))
        return [self.gID, uname]

    def vote(self, e):

        print("Milli irade")
        if e == "yes":
            self.votedYes += 1
        self.voteCount += 1

        if self.votedYes == len(self.userlist):
            self.votedYes = 0
            self.voteCount = 0
            saveObj = {"mapState": self.loaded,
                       "userlist": self.userlist,
                       "turn": self.turn,
                       "name": self.savedGameName}
            return [self.gID, saveObj]

        elif self.voteCount == len(self.userlist):

            self.votedYes = 0
            self.voteCount = 0
            return [self.gID, False]

    def assign(self, e):
        itery = int(42 / len(self.userlist))
        for i in self.userlist:
            for it in range(itery):
                self.countries.append(i)
        random.shuffle(self.countries)
        offset = len(self.countries) - itery * len(self.userlist)
        for i in range(offset):
            self.countries.append(self.userlist[i])

    def turner(self):

        to_be_deleted = []

        if len(self.nonDisconnectors) != 0:
            print("userlist_before", self.userlist)
            for i in range(len(self.userlist)):
                if self.nonDisconnectors.count(self.userlist[i]) == 0:
                    to_be_deleted.append(self.userlist[i])
            for temp in to_be_deleted:
                self.userlist.remove(temp)
            print("userlist_now", self.userlist)
            if self.turn == len(self.userlist):
                self.turn = 0
        print("PLAY ", self.userlist[self.turn])
        msg = ""
        if self.cycle == True:
            msg = "no" + self.userlist[self.turn]
        else:
            msg = "ye" + self.userlist[self.turn]

        self.turn = (self.turn + 1)  # % len(userlist)
        if self.turn == len(self.userlist):
            self.turn = 0
            self.cycle = True
        return [self.gID, msg]

    def reset(self):
        self.userlist = []
        self.countries = []
        self.turn = 0
        self.cycle = False

    def unitMover(self, e):
        return [self.gID, e]

    def attack(self, e):
        return [self.gID, e]

    def unitNuke(self, e):
        return [self.gID, e]

    def wololooo(self, wololos):
        return [self.gID, wololos]

    def parapara(self, paras):
        return [self.gID, paras]
