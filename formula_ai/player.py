#! /usr/bin/env python
# -*- coding:utf-8 -*-

import time
import json
import hashlib
from websocket import create_connection

import sys
sys.path.insert(0, "holdem_calc")
import holdem_calc
import deuces

# pip install websocket-client

ws = ""
pot = 0
my_bet = 0
action_taken = False
my_round_action = dict()
allin_count = dict()
raise_count = dict()
bet_count = dict()
player_count = {
    "Deal" : 0,
    "Flop" : 0,
    "Turn" : 0,
    "River" : 0
}

card_to_score = {
    "2" : 2,
    "3" : 3,
    "4" : 4,
    "5" : 5,
    "6" : 6,
    "7" : 7,
    "8" : 8,
    "9" : 9,
    "T" : 10,
    "J" : 11,
    "Q" : 12,
    "K" : 13,
    "A" : 14
}

def take_action(action="check", amount=0):
    """
    Take an action
    """
    global action_taken
    global my_round_action

    if ("bet" in my_round_action or "raise" in my_round_action) \
        and action in ["bet", "raise"]:
            action = "call"

    message = {
        "eventName": "__action",
        "data": {}
    }
    message["data"]["action"] = action
    message["data"]["amount"] = int(amount)

    print "==== Take Action ==== : %s %s" % (action, str(amount))
    ws.send(json.dumps(message))
    action_taken = True

def expected_value(win_prob, min_bet):
    """
    Compute expacted value to attend next stage
    """
    global pot
    EV = (((pot + min_bet) * win_prob) - min_bet)
    print "==== Expected value ==== %d" % EV
    return (((pot + min_bet) * win_prob) - min_bet)

def hole_cards_score(hole_cards):
    """
    Calculate a score for hole cards
    Return high score if we got high cards/pair/possible straight/possible flush
    """
    high_card = 0
    same_suit = 0
    possible_straight = 0
    pair = 0

    base_score = card_to_score[hole_cards[0][0]] + card_to_score[hole_cards[1][0]]
    if base_score > 20:
        high_card =  base_score - 20

    if hole_cards[0][1] == hole_cards[1][1]:
        same_suit = 2

    value_diff = card_to_score[hole_cards[0][0]] - card_to_score[hole_cards[1][0]]
    if value_diff in [-4, 4]:
        possible_straight = 1
    if value_diff in [-3, 3]:
        possible_straight = 2
    if value_diff in [-2, -1, 1, 2]:
        possible_straight = 3
    if value_diff == 0:
        pair = 10

    return (pair + same_suit + high_card + possible_straight ) * base_score

def update_player_count(data):
    """
    Update active player count of current stage
    """
    global player_count
    count = 0
    for player in data["players"]:
        if player["isSurvive"] and not player["folded"]:
            count += 1
    player_count[data["table"]["roundName"]] = count

def player_statistics(players):
    """
    Return the statistics of current players in this round
    """
    global player_count
    global allin_count
    global raise_count
    global bet_count
    playing = 0
    p_stat = {}
    p_stat["v_bet"] = sum(bet_count.values())
    p_stat["v_raise"] = sum(raise_count.values())
    p_stat["v_allin"] = sum(allin_count.values())
    for player in players:
        if not player["playerName"] == my_md5 \
            and not player["folded"]:
            playing += 1
            if player["allIn"]:
                p_stat["v_allin"] += 2
            if player["playerName"] in bet_count:
                p_stat["v_bet"] += bet_count[player["playerName"]]
            if player["playerName"] in raise_count:
                p_stat["v_raise"] += raise_count[player["playerName"]]

    if player_count["Flop"] > 0:
        p_stat["base_line"] = max(player_count["Flop"] - 1, playing)
    else:
        p_stat["base_line"] = max(player_count["Deal"] - 1, playing)

    return p_stat

def virtual_player_count(data):
    """
    Return virtual player count
    Except real player count also considering the bet/raise/allin in this round
    """
    players_stat = player_statistics(data["game"]["players"])
    v_players = int(players_stat["base_line"]
            + players_stat["v_bet"]
            + players_stat["v_raise"]
            + players_stat["v_allin"])
    print "==== Virtual player count ==== %d  = %d + %d + %d + %d" \
            % (v_players,
               players_stat["base_line"],
               players_stat["v_bet"],
               players_stat["v_raise"],
               players_stat["v_allin"])
    return v_players

def calc_win_prob_by_sampling(hole_cards, board_cards, data):
    """
    Calculate the probability to win current players by sampling unknown cards
    Compute the probability to win one player first
    And then take the power of virtual player count
    """
    evaluator = deuces.Evaluator()
    o_hole_cards = []
    o_board_cards = []
    for card in hole_cards:
        o_hole_card = deuces.Card.new(card)
        o_hole_cards.append(o_hole_card)
    for card in board_cards:
        o_board_card = deuces.Card.new(card)
        o_board_cards.append(o_board_card)

    n = 1000
    win = 0
    succeeded_sample = 0
    for i in range(n):
        deck = deuces.Deck()
        board_cards_to_draw = 5 - len(o_board_cards)

        o_board_sample = o_board_cards + deck.draw(board_cards_to_draw)
        o_hole_sample = deck.draw(2)

        try:
            my_rank = evaluator.evaluate(o_board_sample, o_hole_cards)
            rival_rank = evaluator.evaluate(o_board_sample, o_hole_sample)
        except:
            continue
        if my_rank <= rival_rank:
            win += 1
        succeeded_sample += 1
    print "==== sampling result ==== win : %d, total : %d" % (win, succeeded_sample)
    win_one_prob = win/float(succeeded_sample)

    win_all_prob = win_one_prob ** virtual_player_count(data)
    print "==== Win probability ==== " + str(win_all_prob)
    return win_all_prob

def calc_win_prob(hole_cards, board_cards, data):
    """
    Calculate the probability to win current players.
    Compute the probability to win one player first
    And then take the power of virtual player count
    """
    cards_to_evaluate = hole_cards + ["?", "?"]
    exact_calc = True
    verbose = True
    # claculate probability to win a player
    win_one_prob = holdem_calc.calculate(board_cards, exact_calc, 1, None, cards_to_evaluate, verbose)

    win_all_prob = (win_one_prob[0] + win_one_prob[1]) ** virtual_player_count(data)
    print "==== Win probability ==== " + str(win_all_prob)
    return win_all_prob

def evaluate_river(hole_cards, board_cards, data):
    """
    Decide action in river stage
    """
    win_all_prob = calc_win_prob(hole_cards, board_cards, data)
    ev = expected_value(win_all_prob, data["self"]["minBet"])

    if win_all_prob >= 0.9:
        take_action("allin")
    elif win_all_prob >= 0.6:
        amount = min(ev, 0.1 * data["self"]["chips"] + data["self"]["minBet"])
        take_action("bet", amount)
    elif win_all_prob >= 0.4:
        take_action("call")
    elif ev >= 0 and win_all_prob >= 0.2:
        take_action("check")
    else:
        take_action("fold")

def evaluate_turn(hole_cards, board_cards, data):
    """
    Decide action in turn stage
    """
    win_all_prob = calc_win_prob(hole_cards, board_cards, data)
    ev = expected_value(win_all_prob, data["self"]["minBet"])

    if win_all_prob >= 0.8:
        amount = 0.2 * data["self"]["chips"] + data["self"]["minBet"]
        take_action("bet", amount)
    elif win_all_prob >= 0.5:
        amount = min(ev, 0.1 * data["self"]["chips"] + data["self"]["minBet"])
        take_action("bet", amount)
    elif win_all_prob >= 0.4:
        amount = min(ev, 0.05 * data["self"]["chips"] + data["self"]["minBet"])
        take_action("bet", amount)
    elif ev >= 0 and win_all_prob >= 0.15:
        take_action("check")
    else:
        take_action("fold")

def evaluate_flop(hole_cards, board_cards, data):
    """
    Decide action in flop stage
    """
    win_all_prob = calc_win_prob_by_sampling(hole_cards, board_cards, data)
    ev = expected_value(win_all_prob, data["self"]["minBet"])

    if win_all_prob >= 0.8:
        amount = min(ev, 0.1 * data["self"]["chips"] + data["self"]["minBet"])
        take_action("bet", amount)
    elif win_all_prob >= 0.5:
        take_action("raise")
    elif win_all_prob >= 0.3:
        amount = min(ev, 0.05 * data["self"]["chips"] + data["self"]["minBet"])
        take_action("bet", amount)
    elif ev >= 0 and win_all_prob >= 0.15:
        take_action("check")
    else:
        take_action("fold")

# Can change to Chen formula
def evaluate_deal(hole_cards, data):
    """
    Decide action in deal(preflop) stage
    """
    # Accumulate the bet/raise/allin count for each alived players. Find base line(survived players) for each stage
    v_players = virtual_player_count(data)
    score = hole_cards_score(hole_cards) * (9/float(v_players))

    basic_win_porb = 1/float(v_players)
    ev = expected_value(basic_win_porb, data["self"]["minBet"])

    if score > min(hole_cards_score(["As", "Js"]), hole_cards_score(["Qs", "Qh"])):
        print "==== Judgement is bet ==== score : " + str(score)
        amount = 2 * (data["self"]["minBet"] + 10)
        take_action("bet", amount)
    elif score > min(hole_cards_score(["As", "9s"]), hole_cards_score(["7s", "7h"])):
        print "==== Judgement is bet ==== score : " + str(score)
        amount = 1.5 * (data["self"]["minBet"] + 10)
        take_action("bet", amount)
    elif ev >= 0 or data["self"]["minBet"] <= 20:
        print "==== Judgement is call ==== score : %d ,EV : %d" % (score, ev)
        take_action("call")
    else:
        print "==== Judgement is fold ==== score : " + str(score)
        take_action("fold")

def convert_card_format(card):
    """
    Convert card format so that we could use
    library to evaluate cards
    """
    if len(card) != 2:
        print "Wrong card format"
        return
    return card[0] + card[1].lower()

def evaluate(data):
    """
    Make decision of each stage
    """

    hole_cards  = [convert_card_format(c) for c in data["self"]["cards"]] # ['7C', '5D']
    board_cards = [convert_card_format(c) for c in data["game"]["board"]] # []
    print "==== my cards ==== " + str(hole_cards)  #['7c', '5d']
    print "==== board ==== " + str(board_cards)
    print "==== Current pot ==== %d" % (pot)

    # Action strategy for each stage
    if data["game"]["roundName"] == "Deal": #Preflop
        evaluate_deal(hole_cards, data)
    elif data["game"]["roundName"] == "Flop":
        evaluate_flop(hole_cards, board_cards, data)
    elif data["game"]["roundName"] == "Turn":
        evaluate_turn(hole_cards, board_cards, data)
    elif data["game"]["roundName"] == "River":
        evaluate_river(hole_cards, board_cards, data)

def react(event, data):
    """
    React to events
    """
    global bet_count
    global raise_count
    global allin_count
    global my_round_action
    global player_count
    global my_bet
    global pot
    global action_taken
    action_taken = False

    if event == "__new_peer":
        pass
    elif event == "__new_peer_2":
        pass
    elif event == "_join":
        pass
    # Broadcast opponent's action or BB/BS's amount 
    elif event == "__show_action":
        if data["action"]["playerName"] == my_md5:
            if "amount" in data["action"]: # if true, it means BB or SB amount
                my_bet += data["action"]["amount"]

        pot = data["table"]["totalBet"]
        if data["action"]["action"] == "allin":
            if data["action"]["playerName"] in allin_count:
                allin_count[data["action"]["playerName"]] += 1
            else:
                allin_count[data["action"]["playerName"]] = 1
        if data["action"]["action"] == "raise":
            if data["action"]["playerName"] in raise_count:
                raise_count[data["action"]["playerName"]] += 1
            else:
                raise_count[data["action"]["playerName"]] = 1
        if data["action"]["action"] == "bet":
            if data["action"]["playerName"] in bet_count:
                bet_count[data["action"]["playerName"]] += 1
            else:
                bet_count[data["action"]["playerName"]] = 1
    # When community cards are dealt, reset my_round_action, count the survived players number
    elif event == "__deal":
        my_round_action = dict()
        update_player_count(data)
        print "==== Player count in %s ==== %d" % (data["table"]["roundName"], player_count[data["table"]["roundName"]])
    # Reload chip for bot
    elif event == "__start_reload":
        ws.send(json.dumps({"eventName" : "__reload"}))
    # Sent all players' statuses after a round is completed, including private cards and the winning money  
    elif event == "__round_end":
        for player in data["players"]:
            if player["playerName"] == my_md5:
                if player["winMoney"] > 0:
                    print "==== Round end : Win money!! ==== %d" % ( player["winMoney"])
                else:
                    print "==== Round end : Cheer up! ==== Loss bet : %d" % (my_bet)
    # Reset my accumulating bet, pot, player count in every stage, and every actions count
    elif event == "__new_round":
        my_bet = 0
        pot = 0
        allin_count = dict()
        raise_count = dict()
        bet_count = dict()
        player_count = {
            "Deal" : 0,
            "Flop" : 0,
            "Turn" : 0,
            "River" : 0
        }
    # In bet, calculate winning prob    
    elif event == "__bet":
        #time.sleep(2)
        evaluate(data)
        if not action_taken :
            take_action("bet", 10)
     # In action, calculate winning prob    
    elif event == "__action":
        #time.sleep(2)
        evaluate(data)
        if not action_taken :
            take_action("check")
    elif event == "__game_over":
        max_chips = 0
        my_chips = 0
        for winner in data["winners"]:
            if winner["chips"] > max_chips:
                max_chips = winner["chips"]
            if winner["playerName"] == my_md5:
                my_chips = winner["chips"]
        if my_chips == max_chips:
            print "==== Game over : YOU ARE THE WINNER!! ==== Final chips %d" % max_chips
        else:
            print "==== Game over : So close... ==== %d vs %d" % (my_chips, max_chips)
    else:
        print "==== unknown event ==== : " + event


def doListen():
    try:
        global ws
        ws = create_connection("ws://poker-dev.wrs.club:3001")
        ws.send(json.dumps({
            "eventName": "__join",
            "data": {
                "playerName": my_id
            }
        }))
        while 1:
            result = ws.recv()
            msg = json.loads(result)
            event_name = msg["eventName"]
            data = msg["data"]
            print event_name
            print data
            react(event_name, data)
    except Exception, e:
        print e.message
        doListen()


if __name__ == '__main__':

    my_id = "trybot3"
    my_md5 = hashlib.md5(my_id).hexdigest()
    print my_md5
    doListen()
