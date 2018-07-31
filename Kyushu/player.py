#! /usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import division
import os
import time
import traceback
import numpy as np
import eval7
import pickle
import datetime

from termcolor import cprint
from talker.client import PokerClient
from talker.action import *
from holdem.card import Card
from pokereval.hand_evaluator import get_score, HandEvaluator, getCardID, genCardFromId, pick_unused_card, getCard
from score_evaluator import Player

DUMMY_PLAYER = 'XXXX'
current_folder = os.path.dirname(os.path.abspath(__file__))
class RefereePlayer(PokerClient):
    #CLIENT_NAME = os.environ.get("TABLE", "") + "35b50b7d6d6a41c7a51625d76cc5abc2"
    #CLIENT_NAME = u"新店小栗旬"

    CLIENT_NAME = os.environ.get("TABLE", "") + "jojotrain"
    
    def save_append_training_data(self, behavior):        
        now = datetime.datetime.now()
        TRAINDATA_PATH = os.path.join(current_folder, 'training/'+ str(now)[:10] + '.pkl')
        directory = os.path.dirname(TRAINDATA_PATH)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        if os.path.exists(directory):
            with open(TRAINDATA_PATH,'a') as f:
                # Pickle dictionary using protocol 0.
                #print '*** Save %s' %behavior
                pickle.dump(behavior, f)

    # override end round to train the user's behavior
    def _act_end_round(self, action, data):

        super(RefereePlayer, self)._act_end_round(action, data)
        # the training data for user behavior
        user_behaviors = self._get_player_training_data(data["players"])
        if user_behaviors:
            for player_name, behavior in user_behaviors.iteritems():
                #player = Player(player_name)
                player = Player(DUMMY_PLAYER)
                self.save_append_training_data(behavior)
                player.train(behavior)
                if player.is_bluffing_guy is not None:
                    cprint("player(%s) is a(n) %s guy" % (
                        player_name, ("bluffing" if player.is_bluffing_guy else "honest")), "cyan")
                #player = Player(DUMMY_PLAYER)
                #player.train(behavior)

    def behavior_predict(self, data=None):
        my_score = get_score(self.cards, self.board)
        predict_values = {}
        simulate_score = 0
        dummyplayer = Player(DUMMY_PLAYER)
        for player_name, behavior in self.thisRoundUserBehavior_for_predict.iteritems():
            simulate_score = dummyplayer.predict(behavior[:37], self.roundSeq)
            if np.math.isnan(simulate_score):
                simulate_score = self.simulation(data, 10000)
            predict_values[player_name] = simulate_score
        
        is_large_bet = self.minBet / self.big_blind_amount > 10 if self.big_blind_amount else False

        the_pred_values = sorted(filter(None, predict_values.values()), reverse=True)
        print "***behavior predict:%s, my_score(%s)" % (predict_values.values(), my_score)

        if is_large_bet:
            if my_score > max(the_pred_values):
                return CALL
            return FOLD

        elif the_pred_values:
            #if len(the_pred_values) >= 4: #5~10 players (will provide auto dummy) 
                if data["game"]["roundName"] == "Deal":  # Preflop
                    if my_score > max(the_pred_values):
                        return (BET, 3)
                    elif my_score > min(the_pred_values):
                        return CALL   
                    # never fold    
                elif data["game"]["roundName"] == "Flop":
                    if my_score > max(the_pred_values):
                        return (BET, 3)
                    elif my_score > the_pred_values[1]:
                        return (BET, 1)
                    elif my_score > min(the_pred_values):
                        return CALL 
                    else:
                        return FOLD    
                elif data["game"]["roundName"] == "Turn":    
                    if my_score > max(the_pred_values) and my_score > 0.85:
                        return (BET, 8)
                    elif my_score > max(the_pred_values):
                        return (BET, 5)
                    elif my_score > the_pred_values[1]:
                        return (BET, 3)
                    elif my_score > the_pred_values[int(len(the_pred_values)/2)]:
                        return (BET, 1)  
                    #elif my_score > min(the_pred_values):
                        #return CALL    
                    else:
                        return FOLD  
                elif data["game"]["roundName"] == "River":    
                    if my_score > max(the_pred_values) and my_score > 0.85:
                        return (BET, 8)
                    elif my_score > max(the_pred_values):
                        return (BET, 5)
                    elif my_score > the_pred_values[1]:
                        return (BET, 3)
                    elif my_score > the_pred_values[int(len(the_pred_values)/2)]:
                        return CALL
                    else:
                        return FOLD      
        return CHECK


    def predict(self, data=None):
        act = self.behavior_predict(data)
        return act

    def simulation(self, my_score, data, sim_num=1000):

        return self.calc_win_prob_by_sampling_eval7(self.cards, self.board, data, sim_num)

        eval_hand = getCard(self.cards)
        eval_board = getCard(self.board)
        evaluator = HandEvaluator()
        win = 0
        sampling = 0
        for _ in range(sim_num):
            board_cards_to_draw = 5 - len(eval_board)
            board_sample = eval_board + pick_unused_card(board_cards_to_draw, eval_hand + eval_board)

            unused_cards = pick_unused_card(2, eval_hand + board_sample)
            opponents_hole = unused_cards[0:2]
            try:
                opponents_score = evaluator.evaluate_hand(opponents_hole, board_sample)
                if opponents_score > my_score:  # opponent win probability
                    win += 1
                sampling += 1
            except Exception:
                continue

        return win / float(sampling)

    def exclude_impossible_rivals_lookup(self, deck, board_cards_to_draw, rivals_count):
        iteration = 0
        threshold = 0.55
        while 1:
            iteration += 1
            simulate_cards = deck.sample(board_cards_to_draw + 2 * rivals_count)
            if threshold > 0:
                all_nice_cards = all([HandEvaluator.evaluate_hand(
                    getCard([str(hand) for hand in simulate_cards[i:i + 2]])) >= threshold for i
                                      in range(board_cards_to_draw, board_cards_to_draw + 2 * rivals_count, 2)])
                if all_nice_cards is True:
                    # print('Takes {} iteration to get possible rivals\' hand cards'.format(iteration))
                    return simulate_cards, iteration
            else:
                return simulate_cards, iteration

    def get_rivals_count(self, data):
        count = 0
        for player in data['game']['players']:
            if player["isSurvive"] and not player["folded"]:
                count += 1
        return count

    def calc_win_prob_by_sampling_eval7(self, hole_cards, board_cards, data, sim_num):
        """
        Calculate the probability to win current players by sampling unknown cards
        Compute the probability to win one player first
        And then take the power of virtual player count
        """

        o_hole_cards = []
        o_board_cards = []
        deck = eval7.Deck()
        # remove hole cards and board cards from deck
        for card in hole_cards:
            card = eval7.Card(card)
            o_hole_cards.append(card)
            deck.cards.remove(card)
        board_cards_to_draw = 5
        for card in board_cards:
            board_cards_to_draw -= 1
            card = eval7.Card(card)
            o_board_cards.append(card)
            deck.cards.remove(card)
        # vpc_weighted = virtual_player_count_weighted()
        rivals_count = 1  # self.get_rivals_count(data)
        win = 0
        succeeded_sample = 0
        start = time.time()
        # TODO: Remove small rivals
        if board_cards_to_draw:
            n = sim_num
            index = 10
            for iteration in range(n // rivals_count):
                simulate_cards, _ = self.exclude_impossible_rivals_lookup(deck, board_cards_to_draw, rivals_count)
                o_board_sample = o_board_cards + simulate_cards[:board_cards_to_draw]
                my_rank = eval7.evaluate(o_board_sample + o_hole_cards)
                won = True
                for i in range(board_cards_to_draw, board_cards_to_draw + 2 * rivals_count, 2):
                    if my_rank < eval7.evaluate(o_board_sample + simulate_cards[i:i + 2]):
                        won = False
                        break
                if won:
                    win += 1
                succeeded_sample += 1
                if iteration == index:
                    print("==== sampling result ==== win : %d, total : %d, probability : %f, takes: %f seconds" %
                          (win, succeeded_sample, win / succeeded_sample, time.time() - start))
                    index *= 10
        else:
            my_rank = eval7.evaluate(o_board_cards + o_hole_cards)
            n = sim_num
            index = 10
            for iteration in range(n // rivals_count):
                won = True
                simulate_cards, _ = self.exclude_impossible_rivals_lookup(deck, 0, rivals_count)
                # simulate_cards = deck.sample(2 * rivals_count)
                for i in range(0, 2 * rivals_count, 2):
                    if my_rank < eval7.evaluate(o_board_cards + simulate_cards[i:i + 2]):
                        won = False
                        break
                if won:
                    win += 1
                succeeded_sample += 1
                if iteration == index:
                    print("==== sampling result ==== win : %d, total : %d, probability : %f, takes: %f seconds" %
                          (win, succeeded_sample, win / succeeded_sample, time.time() - start))
                    index *= 10
        print("==== sampling result ==== win : %d, total : %d, probability : %f, takes: %f seconds" %
              (win, succeeded_sample, win / succeeded_sample, time.time() - start))
        return win / succeeded_sample


import re, json
import talker.event as EVENTNAME


def parse(file):
    with open(file) as fp:
        content = fp.read()
        parse_round(content)


def parse_content(content):
    return re.findall('\[INFO\] .* - .*: >>> ((.*) >>> (.*))', content)


def parse_round(content):
    matches = parse_content(content)
    for res in matches:
        if len(res) == 3:
            if res[1] == 'event SHOW_ACTION':
                jsonData = json.loads(res[2])
                table_num = jsonData["data"]["table"]['tableNumber']
                return EVENTNAME.SHOW_ACTION, table_num, jsonData["data"]
            elif res[1] == 'event ROUND_END':
                jsonData = json.loads(res[2])
                table_num = jsonData["data"]["table"]['tableNumber']
                return EVENTNAME.ROUND_END, table_num, jsonData["data"]
            elif 'table' in res[1] and 'new round' in res[2]:
                table_num = res[1].split()[1]
                round_num = res[2].split()[3]
                return EVENTNAME.NEW_ROUND, table_num, None
    return None, None, None


if __name__ == '__main__':
    training_mode = os.environ.get('TRAINING_MODE', "False").lower() == "true"
    if not training_mode:
        pc = RefereePlayer()
        pc.doListen()
    else:
        logfile = 'server.log'
        pcs = dict()

        with open(logfile) as fp:
            for content in fp:
                # content = fp.read()
                action, table_num, data = parse_round(content)
                if action:
                    if not pcs.get(table_num):
                        pc = RefereePlayer()
                        pc.trainingMode = True
                        pcs[table_num] = pc
                    else:
                        pc = pcs[table_num]
                    pc.takeAction(action, data)
