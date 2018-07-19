import os
import traceback
import numpy as np
from termcolor import cprint

from talker.client import PokerClient
from talker.action import *
from holdem.card import Card
from pokereval.hand_evaluator import get_score, HandEvaluator, getCardID, genCardFromId, pick_unused_card, getCard
from score_evaluator import Player


class RefereePlayer(PokerClient):
    #CLIENT_NAME = os.environ.get("TABLE", "") + "35b50b7d6d6a41c7a51625d76cc5abc2"
    CLIENT_NAME = os.environ.get("TABLE", "") + "jojotrain"

    # override end round to train the user's behavior
    def _act_end_round(self, action, data):

        super(RefereePlayer, self)._act_end_round(action, data)

        # the training data for user behavior
        user_behaviors = self._get_player_training_data(data["players"])
        if user_behaviors:
            for player_name, behavior in user_behaviors.iteritems():
                player = Player(player_name)
                player.train(behavior)
                if player.is_bluffing_guy is not None:
                    cprint("player(%s) is a(n) %s guy" % (player_name, ("bluffing" if player.is_bluffing_guy else "honest")), "cyan")

    def behavior_predict(self):
        my_score = get_score(self.cards, self.board)
        predict_values = {}
        for player_name, behavior in self.thisRoundUserBehavior_for_predict.iteritems():
            player = Player(player_name)
            if player.is_known_guy:
                predict_values[player_name] = player.predict(behavior[:25], self.roundSeq)
            else: #If it's not a known opponent, the model will highly be inaccurate, train it but not use it for prediction
                predict_values[player_name] = self.simulation(my_score, 5000)
                
        is_large_bet = self.minBet / self.big_blind_amount > 10 if self.big_blind_amount else False

        the_pred_values = sorted(filter(None, predict_values.values()), reverse=True)
        print "***behavior predict:%s, my_score(%s)" % (predict_values.values(), my_score)

        if is_large_bet:
            if my_score > max(the_pred_values):
                return CALL
            return FOLD

        elif the_pred_values:
            if len(the_pred_values) > 4:
                if my_score > max(the_pred_values):
                    return (BET, 5)
                elif my_score > the_pred_values[1]:
                    return (BET, 3)
                elif my_score > the_pred_values[2]:
                    return (BET, 2)
                elif my_score > the_pred_values[3]:
                    return (BET, 1)
            elif my_score > min(the_pred_values):
                return CALL
            return FOLD

        return CHECK


    def predict(self, data=None):
        act = self.behavior_predict()
        return act

    def simulation(self, my_score, sim_num=1000):
        eval_hand = getCard(self.cards)
        eval_board = getCard(self.board)
        evaluator = HandEvaluator()
        win = 0
        sampling = 0
        for _ in range(sim_num):
            board_cards_to_draw = 5 - len(eval_board)  
            board_sample = eval_board + pick_unused_card(board_cards_to_draw,  eval_hand + eval_board)

            unused_cards = pick_unused_card(2, eval_hand + board_sample)
            opponents_hole = unused_cards[0:2]
            try:
                opponents_score = evaluator.evaluate_hand(opponents_hole, board_sample)
                if opponents_score > my_score: # opponent win probability
                    win += 1
                sampling += 1
            except Exception:
                continue
       
        return win/float(sampling)

if __name__ == '__main__':
    pc = RefereePlayer()
    pc.doListen()
