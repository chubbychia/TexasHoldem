import deuces
from pokereval.hand_evaluator import HandEvaluator
from pokereval.card import Card
import random

def getCard(card):
    card_type = card[1].lower()
    cardnume_code = card[0]
    card_num = 0
    card_num_type = 0
    if card_type == 's':
        card_num_type = 1
    elif card_type == 'h':
        card_num_type = 2
    elif card_type == 'd':
        card_num_type = 3
    else:
        card_num_type = 4

    if cardnume_code == 'T':
        card_num = 10
    elif cardnume_code == 'J':
        card_num = 11
    elif cardnume_code == 'Q':
        card_num = 12
    elif cardnume_code == 'K':
        card_num = 13
    elif cardnume_code == 'A':
        card_num = 14
    else:
        card_num = int(cardnume_code)

    return Card(card_num,card_num_type)

def _pick_unused_card(card_num, used_card):    
    used = [getCardID(card) for card in used_card]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]
    choiced = random.sample(unused, card_num)
    return [genCardFromId(card_id) for card_id in choiced]

def getCardID(card):
    rank=card.rank
    suit=card.suit
    suit=suit-1
    id=(suit*13)+rank
    return id

def genCardFromId(cardID):
    if int(cardID)>13:
        rank=int(cardID)%13
        if rank==0:
            suit=int((int(cardID)-rank)/13)
        else:
            suit = int((int(cardID) - rank) / 13) + 1

        if(rank==0):
            rank=14
        else:
            rank+=1
        return Card(rank,suit)
    else:
        suit=1
        rank=int(cardID)
        if (rank == 0):
            rank = 14
        else:
            rank+=1
        return Card(rank,suit)
   

def run():
    SUIT_TO_STRING = {
        1: "s",
        2: "h",
        3: "d",
        4: "c"
    }
  
    RANK_TO_STRING = {
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "T",
        11: "J",
        12: "Q",
        13: "K",
        14: "A"
    }

    hole_cards = ['4s','Qh']
    board_cards = ['Jc','6c','9h']
    #board_cards = []
    
    eval_hand = [getCard(card) for card in (hole_cards)]
    print eval_hand.__repr__()
    eval_board = [getCard(card) for card in (board_cards)]
    print eval_board.__repr__()
    d_hands = [deuces.Card.new(card) for card in hole_cards]
    
    evaluator = deuces.Evaluator()
    
    sim_num = 15000
    win = 0
    succeeded_sample = 0
    num_players = 6
    
    for i in range(sim_num):
        board_cards_to_draw = 5 - len(eval_board)
        e_board_sample = eval_board + _pick_unused_card(board_cards_to_draw, eval_board+eval_hand) # exclude my cards and community cards
        unused_cards = _pick_unused_card((num_players-1)*2, eval_hand + e_board_sample)
        e_opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]

        d_oppo_sample = []
        d_oppo_set = []
        d_board_sample = []        
        for evalcard in e_board_sample: # pokereval Card type
            s_hand = str(RANK_TO_STRING[evalcard.rank])+str(SUIT_TO_STRING[evalcard.suit])
            d_board_card = deuces.Card.new(s_hand)
            d_board_sample.append(d_board_card)
            #print ("Community : "+s_hand)

        for evalcardset in e_opponents_hole:
            d_oppo_set = []
            for e_card in evalcardset:
                s_hand = str(RANK_TO_STRING[e_card.rank])+str(SUIT_TO_STRING[e_card.suit])
                d_oppo_card = deuces.Card.new(s_hand)
                d_oppo_set.append(d_oppo_card)
                #print ("Opponents hands : "+s_hand)
            d_oppo_sample.append(d_oppo_set)           
            

        try:
            my_rank = pow(evaluator.evaluate(d_hands, d_board_sample), num_players)
            rival_rank = [pow(evaluator.evaluate(opp_hole, d_board_sample), num_players) for opp_hole in d_oppo_sample]
            #print str(my_rank) +" versus "+str(rival_rank)
        except:
            continue
        if my_rank <= min(rival_rank):
            win += 1
        succeeded_sample += 1
    print "==== Sampling result ==== win : %d, total : %d" % (win, succeeded_sample)
    win_one_prob = win/float(succeeded_sample)
    print "==== Win probability ==== " + str(win_one_prob)


if __name__ == '__main__':
    run()

