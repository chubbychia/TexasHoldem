#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=all


import json
import pprint
import traceback
import time
from collections import defaultdict
from termcolor import cprint
from action import *
from pokereval.hand_evaluator import get_score, get_rank, evaluate_stage_winrate
from websocket import create_connection
from holdem.card import Card
import event as EVENTNAME
import hashlib

#server = "ws://poker-battle.vtr.trendnet.org:3001"
server = "ws://poker-training.vtr.trendnet.org:3001"
#server = "ws://poker-dev.wrs.club:3001"
RETRY = 5
ws = create_connection(server)

class GameOverException(Exception):
    pass


class PokerClient(object):
    #CLIENT_NAME = "35b50b7d6d6a41c7a51625d76cc5abc2"

    CLIENT_NAME = "jojotrain"
    def __init__(self):
        self._name_hash = None
        self._chips = 0

        self._big_blind = None
        self._small_blind = None

        self.bet = 0
        self.minBet = 0
        self.totalBet = 0
        # 0: deal, 1:flop, 2:turn, 3:river
        self._roundSeq = 0
        self.raiseCount = [0, 0, 0, 0]
        self.betCount = [0, 0, 0, 0]
        self.myBet = [0, 0, 0, 0]
        self.cardRanking = [0, 0, 0, 0]
        self._needBet = [False, False, False, False]
        # do i call or check
        self.iscall = [0, 0, 0, 0]

        self._cards = []
        self._board = []

        # record the user behavior
        self.thisRoundUserBehavior = {}
        self.thisRoundUserBehavior_for_predict = {}

        # play result
        self.game_count = 0
        self.game_chips = 0

        self.trainingMode = False

    def new_game(self):
        self.minBet = 0
        self.totalBet = 0
        self.myBet = [0, 0, 0, 0]
        self.raiseCount = [0, 0, 0, 0]
        self.betCount = [0, 0, 0, 0]
        self.cardRanking = [0, 0, 0, 0]
        self._needBet = [False, False, False, False]
        self.iscall = [0, 0, 0, 0]

        self.cards = []
        self.board = []
        self._roundSeq = 0
        self.thisRoundUserBehavior = {}
        self.thisRoundUserBehavior_for_predict = {}

    @property
    def name_hash(self):
        if not self._name_hash:
            m = hashlib.md5()
            m.update(self.CLIENT_NAME.encode('utf-8'))
            self._name_hash = m.hexdigest()
        return self._name_hash

    ##### Useful information for prediction
    @property
    def is_pair(self):
        return self.cards[0][0] == self.cards[1][0]

    @property
    def cards(self):
        return self._cards

    @cards.setter
    def cards(self, value):
        self._cards = [card[:1] + card[1:].lower() for card in value]

    @property
    def board(self):
        return self._board

    @board.setter
    def board(self, value):
        self._board = [card[:1] + card[1:].lower() for card in value]

    @property
    def roundSeq(self):
        if self._roundSeq == "Deal":
            return Round.DEAL
        elif self._roundSeq == "Flop":
            return Round.FLOP
        elif self._roundSeq == "Turn":
            return Round.TURN
        elif self._roundSeq == "River":
            return Round.RIVER
        return 0

    @roundSeq.setter
    def roundSeq(self, value):
        self._roundSeq = value

    @property
    def needBet(self):
        if self.roundSeq == 0 and not self.is_big_blind:
            return True

        iscall = self.iscall[self.roundSeq]
        if self.is_big_blind and iscall > 0:
            iscall -= 1

        # user action possible losts from server, use iscall instead
        return self._needBet[self.roundSeq] or iscall

    @property
    def big_blind_amount(self):
        if not self._big_blind:
            return None
        return self._big_blind.get("amount", None)

    @property
    def is_big_blind(self):
        if not self._big_blind:
            return False
        return self._big_blind.get("playerName", None) == self.name_hash

    @property
    def is_small_blind(self):
        if not self._small_blind:
            return False
        return self._small_blind.get("playerName", None) == self.name_hash

    @property
    def my_card_ranking(self):
        if not all([self.cards, self.board]):
            print "Cards: board:%s, mine:%s" % (self.board, self.cards)
            return -1  # worst

        cprint("My cards: %s, %s" % (self.board, self.cards), "cyan")
        return Card.get_card_suite(self.board, self.cards)

    @property
    def board_ranking(self):
        if not len(self.board) == 5:
            return 0

        return Card.get_card_suite(self.board[:3], self.board[3:])

    @property
    def is_almost_straight(self):
        return Card.is_almost_straight(self.board, self.cards)

    @property
    def is_almost_flush(self):
        return Card.is_almost_flush(self.board, self.cards)

    @property
    def is_almost_lose(self):
        if not self.chips:
            return False
        elif not self.big_blind_amount:
            return False
        return self.chips < self.big_blind_amount * 2

    ################################################

    def _send_event(self, event_name, data=None):
        retry = 0
        payload = {"eventName": event_name}
        if data:
            payload["data"] = data
        global ws
        if not ws:
            ws = create_connection(server)
        while 1:
            try:
                ws.send(json.dumps(payload))
                return True
            except BaseException as err:
                print "send event error: {} try times: {}".format(err, retry)
                retry += 1
                ws = create_connection(server)
                if retry < RETRY:
                    continue
                else:
                    return False

    def search(self, players):
        for p in players:
            if p['playerName'] == self.name_hash:
                return p

    def join(self):
        print "%s tries to join.." % self.CLIENT_NAME
        return self._send_event(EVENTNAME.JOIN, {"playerName": self.CLIENT_NAME})

    def reload(self):
        return self._send_event(EVENTNAME.RELOAD)

    def reset(self):
        pass

    ##### action function ########
    def _act_new_peer(self, action, data):
        print "Game Stat: {}".format(action)

    def _act_new_round(self, action, data):
        print "Game Stat: {}".format(action)
        # print "New Round: {}".format(data)
        self.new_game()

        if not self.trainingMode:
            p = self.search(data["players"])
            self.cards = p.get("cards", [])
            self.chips = p["chips"]
            t = data["table"]
            self._small_blind = t["smallBlind"]
            self._big_blind = t["bigBlind"]
            cprint("Start a new round(%s) in Table(%s)" % (t["roundCount"], t["tableNumber"]), "yellow")
        else:
            self.cards = []
            self.chips = 0

        self.reset()

    def _act_end_round(self, action, data):
        print "Game Stat: {}".format(action)
        if not self.trainingMode:
            p = self.search(data["players"])
            if p["winMoney"]:
                cprint("win the money:%s, my chips:%s" % (p["winMoney"], p["chips"]), 'magenta')
            else:
                cprint("lose the money:%s, my chips:%s" % (sum(self.myBet), p["chips"]), 'red')
        else:
            cprint("round end", 'white')

    def _act_game_over(self, action, data):
        print "Game Stat: {}".format(action)

        if not self.trainingMode:
            p = self.search(data["players"])

            self.game_count += 1
            self.game_chips += p["chips"]

            if p["chips"]:
                cprint("I am the winner:%s, played %s games, AVG: %s" % (
                    p["chips"], self.game_count, self.game_chips / self.game_count), 'cyan')
            else:
                cprint(
                    "I am the loser, played %s games, AVG: %s" % (self.game_count, self.game_chips / self.game_count),
                    'red')
        else:
            cprint("game over", 'white')

        raise GameOverException("Game over!")

    def _act_deal(self, action, data):
        print "Game Stat: {}".format(action)
        print "Table info: %s" % data["table"]

        t = data["table"]
        self.board = t["board"]
        self.roundSeq = t["roundName"]

        if self.roundSeq != Round.DEAL:
            self.cardRanking[self.roundSeq] = self.my_card_ranking
            print "Cards are dealt, current ranking:%s" % self.cardRanking

    def _act_action(self, do_act, bet_times=1,champ=0, my_score=0):

        a = {"action": 'fold', "amount": self.minBet}

        bet_mound = max(self._big_blind.get("amount", 0) * bet_times, 120 * bet_times,
                        self.minBet) if self._big_blind else self.minBet

        #If it's the last fight, make sure you win
        if self.chips < 2 * bet_mound:
            if not champ and my_score < 0.95:
                do_act = FOLD
                cprint("Max? %s My Score: %s My chips: %s. It's too risky to bet, use FOLD instead" % (champ, my_score,self.chips), "yellow")

        if do_act == RAISE and self.big_blind_amount and self.minBet / self.big_blind_amount > 10:
            cprint("The minBet(%s) is too much to raise, use CALL instead" % self.minBet, "yellow")
            do_act = CALL

        if do_act == FOLD:
            a = {"action": 'fold', "amount": bet_mound}
        elif do_act == CHECK:
            a = {"action": 'check', "amount": bet_mound}
        elif do_act == BET:
            a = {"action": 'bet', "amount": bet_mound}
        elif do_act == RAISE:
            a = {"action": 'raise', "amount": bet_mound}
        elif do_act == CALL:
            a = {"action": 'call', "amount": bet_mound}
        else:
            a = {"action": 'allin', "amount": bet_mound}

        cprint("Action: %s" % ACT_STR[do_act], "cyan")

        if do_act in (CHECK, BET, RAISE, CALL, ALL_IN):
            self.iscall[self.roundSeq] += 1

        return self._send_event(EVENTNAME.ACTION, a)

    def _act_show_action(self, action, data):
        t = data["table"]
        name = t["roundName"]
        self.totalBet = t["totalBet"]
        player_action = data["action"]

        self._record_player_action(player_action, data)

        if self.roundSeq in Round.ALL:
            self.raiseCount[self.roundSeq] = t["raiseCount"]
            self.betCount[self.roundSeq] = t["betCount"]
            if not self.trainingMode:
                self.myBet[self.roundSeq] = self.search(data["players"])["bet"]
            else:
                self.board = t["board"]
            if player_action["action"] in ('allin', 'bet', 'call', 'raise'):
                cprint("%s %s: %s" % (player_action["playerName"], player_action["action"], player_action["amount"]),
                       'yellow')
                self._needBet[self.roundSeq] = True

        print "==Game update== {0} round({5}): player({7}) do {8}, raiseCount({1}), betCount({2}), " \
              "totalBet({3}), myBet({4}), ranking({6})".format(
                name,
                self.raiseCount,
                self.betCount,
                self.totalBet,
                self.myBet,
                self.roundSeq,
                self.cardRanking,
                player_action["playerName"],
                player_action["action"]
        )

    def _record_player_action(self, player_action, show_action):
        # "action" : {
        #     "action" : "call",
        #     "playerName" : "alex(MD5 Hash)",
        #     "amount" : 10,
        #     "chips" : 500
        # },
        # round features:
        #  0~3: Fold:0, 0, 0, 0
        #    4:  
        #  call_t, bet_t, raise_t, bet_a, all_in, chips, pot, survived
        #  5~12: preflop
        #  13~20: flop
        #  21~28: turn
        #  29:36: river
        #  label: score
        features = self.thisRoundUserBehavior.get(player_action["playerName"], [0] * 38)
        
        if player_action["action"] == 'fold':
            self.thisRoundUserBehavior_for_predict.pop(player_action["playerName"], None)
            features[self.roundSeq] = 1
        elif player_action["action"] == 'call':
            features[8 * self.roundSeq + 5] += 1
        elif player_action["action"] == 'bet':
            features[8 * self.roundSeq + 6] += 1
        elif player_action["action"] == 'raise':
            features[8 * self.roundSeq + 7] += 1
        elif player_action["action"] == 'bet' and player_action["amount"]:
            if self.minBet > 0:
                features[8 * self.roundSeq + 8] += round(float(player_action["amount"])/self.minBet,2)
            else:
                features[8 * self.roundSeq + 8] += round(float(player_action["amount"])/self.bet,2)
        elif player_action["action"] == 'allin':
            features[8 * self.roundSeq + 9] += 1

        # chips 
        features[8 * self.roundSeq + 10] = round(float(player_action["chips"])/3000,2)
        # table pot 
        features[8 * self.roundSeq + 11] = round(float(show_action["table"]["totalBet"])/1000,2)
        # survivor count
        features[8 * self.roundSeq + 12] = self._get_survivor_count(show_action)

        self.thisRoundUserBehavior[player_action["playerName"]] = features
  
        if player_action["playerName"] != self.name_hash:
            self.thisRoundUserBehavior_for_predict[player_action["playerName"]] = features

        #print '*** ShowAction: Round(%d) => %s : %s' % (self.roundSeq, player_action["playerName"], features)
      

    def _get_survivor_count(self, show_action):
        count = 0
        for player in show_action['players']:
            if player["isSurvive"] and not player["folded"]:
                count += 1
        return count

    def _get_predicion_data(self, features, seq):
        boundary = seq * 8 + 13
        pre_boundary = 5
        if seq:
            pre_boundary = (seq - 1) * 8 + 13
        feature_temp = features[0:5]         
        feature_temp += features[pre_boundary:boundary]  #Only 13 values. Omit label
        feature_temp[4] = seq
        return feature_temp
        
        
    #players = round_end players data
    def _get_player_training_data(self, players):
        if not players:
            return
        elif not self.board:
            return

        round_train_data = defaultdict(list)
       
        # use real card rank to train
        user_rank = defaultdict(list)
        for player in players:
            h_cards = player["cards"]
            user_rank[player["playerName"]].append([get_rank(h_cards, self.board[:c]) for c in (0, 3, 4, 5)])
        
        #print '*** user_rank: %s' %user_rank
        
        for player in players:
            features = self.thisRoundUserBehavior.get(player["playerName"], None)
            if not features:
                continue            
           
            # Origianl simulation way
            # h_cards = player["cards"]
            # user_score = [get_score(h_cards, self.board[:c]) for c in (0, 3, 4, 5)]

            #Ex: if one wins in flop, marking the succeeding rounds score to 1
            others_rank = [value[0] for key, value in user_rank.iteritems() if key !=player["playerName"]]
            user_score = evaluate_stage_winrate(user_rank[player["playerName"]][0], others_rank)
            if player["winMoney"]:
                i = self.roundSeq
                while i < len(Round.ALL):
                    user_score[i] = 1
                    i += 1
            #print 'Round (%s) Player %s' % (self.roundSeq, player["playerName"])
            
            #print '*** User %s score: %s' % (player["playerName"],user_score)
            for seq, score in enumerate(user_score):
                boundary = seq * 8 + 13
                pre_boundary = 5
                if seq:
                    pre_boundary = (seq - 1) * 8 + 13
                feature_temp = features[0:5] # folding info + round
                # masking the features per round
                feature_temp += features[pre_boundary:boundary]
                feature_temp += [0] * (14 - len(feature_temp))
                feature_temp[4] = seq
                feature_temp[13] = score
                # skip nonsence data  
                valid = [x for x in feature_temp[5:13] if x]
                if len(valid) > 0:
                    round_train_data[player["playerName"]].append(feature_temp)
                
                # the user is fold, stop training the following round
                if features[seq] == 1:
                    break

        # for player, data in round_train_data.iteritems():
        #     for i, round_data in enumerate(data):
        #         print '*** Round(%s) Player %s training features: %s' %(i, player, round_data)

        return round_train_data

    #############override#################

    def predict(self, data=None):
        """
        the cation must be predicted in this function
        """
        return FOLD

    ##############################

    def takeAction(self, action, data):
        try:
            if action == EVENTNAME.NEW_PEER:
                self._act_new_peer(action, data)

            elif action in EVENTNAME.NEW_ROUND:
                self._act_new_round(action, data)

            elif action == EVENTNAME.DEAL:
                self._act_deal(action, data)

            elif action in (EVENTNAME.ACTION, EVENTNAME.BET):
                # __action -> bet > 0
                # __bet -> minBet > 0
                self.minBet = data['self']['minBet']
                self.bet = data['self']['bet']
                self.chips = data['self']['chips']
                # reconnection the cards is empty
                if not self.cards:
                    self.cards = data['self']['cards']

                action = self.predict(data)

                if isinstance(action, tuple):
                    return self._act_action(action[0], action[1], action[2], action[3])

                return self._act_action(action)

            elif action == EVENTNAME.START_RELOAD:
                if not self.trainingMode:
                    p = self.search(data["players"])
                    if p["chips"] == 0:
                        self.reload()

            elif action == EVENTNAME.SHOW_ACTION:
                # print "Game Stat: {}".format(action)
                self._act_show_action(action, data)

            elif action == EVENTNAME.ROUND_END:
                self._act_end_round(action, data)

            elif action == EVENTNAME.GAME_OVER:
                self._act_game_over(action, data)

            else:
                print "Not Handle state : {}".format(action)

        except GameOverException:
            raise

        except BaseException as err:
            print "action error: %s, %s" % (err, traceback.print_exc())
            pprint.pprint(
                {
                    "event": action,
                    "data": data,
                }
            )

    def doListen(self):
        global ws
        try:
            # ws.send(json.dumps({
            #     "eventName": "__join",
            #     "data": {
            #         "playerName": "player1"
            #     }
            # }))

            if self.join():
                print "connected!!"
            else:
                print "connecton fail!!"

            while 1:
                result = ws.recv()
                msg = json.loads(result)
                event_name = msg["eventName"]
                data = msg["data"]

                # pprint.pprint(
                #         {
                #             "event": event_name,
                #             "data":data,
                #         }
                #     )
                self.takeAction(event_name, data)

        except Exception as e:
            print e
            time.sleep(10)
            self.doListen()


if __name__ == '__main__':
    pc = PokerClient('server.log')
    pc.doListen()
