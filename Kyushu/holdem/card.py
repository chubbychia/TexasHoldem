from deuces import Evaluator
from deuces import Card as deucesCard
from itertools import groupby
from pokereval.hand_evaluator import get_score

CHAR_SUIT = {
    's' : 0, # spades
    'h' : 1, # hearts
    'd' : 2, # diamonds
    'c' : 3 # clubs
}

CHAR_STR = {
    "A": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13
}

evaluator = Evaluator()


class Card(object):

    def __init__(self, card):
        self.card = card

    @property
    def serial(self):
        if self.card == '-':
            return -1
        return CHAR_SUIT[self.card[1]] * 13 +  CHAR_STR[self.card[0]]

    @property
    def one_hot_encode(self):
        one_hot = [0] * 52
        if self.card != '-':
            one_hot[self.serial - 1] = 1
        return one_hot

    @staticmethod
    def get_card_suite(board, hand):
        if not (all(hand) and all(board)):
            return -1
        elif '-' in hand or '-' in board:
            return -1
        board = [deucesCard.new(c) for c in board]
        hand = [deucesCard.new(c) for c in hand]
        return evaluator.evaluate(board, hand)

    @staticmethod
    def get_card_score(hand, board):
        return get_score(hand, board)

    @staticmethod
    def get_merge_one_hot(one_hot_list):
        merge_list = [0] * 52
        for one_hot in one_hot_list:
            merge_list = [k | l for k, l in zip(merge_list, one_hot)]
        return merge_list

    @staticmethod
    def is_almost_straight(board, hand):
        if not board:
            return 0

        card_serial = set([CHAR_STR[c[0]] for c in (board + hand)])
        one_hot = [0] * 14
        for i in card_serial:
            one_hot[i-1] = 1
            if i == 1:
                one_hot[13] = 1

        for i in xrange(10):
            # two cards
            if one_hot[i:i+6] == [0, 1, 1, 1, 1, 0]:
                if len(board) == 3:
                    return 3
                return 2
            # one card
            elif one_hot[i:i+5] in ([0, 1, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 1], [1, 1, 1, 1, 0]):
                if len(board) == 3:
                    return 2
                return 1
        return 0

    @staticmethod
    def is_almost_flush(board, hand):
        if not board:
            return 0

        suit_serial = sorted([CHAR_SUIT[c[1]] for c in (board + hand)])
        suit_serial = [len(list(group)) for key, group in groupby(suit_serial)]

        if 4 in suit_serial:
            if len(board) == 3:
                return 2
            elif len(board) == 4:
                return 1
        return 0


if __name__ == '__main__':
    print Card('As').serial
    print Card('Kc').serial
    print Card('As').one_hot_encode
    print Card('Kc').one_hot_encode

    print Card.get_card_suite(["Kh", "Ah", "Th"], ["As", "2c"])
    print Card.get_merge_one_hot([Card('As').one_hot_encode, Card('Kc').one_hot_encode])
    print Card.get_merge_one_hot([])

    assert Card.is_almost_straight(["Kh", "Ah", "Th"], ["As", "2c"]) == 0
    assert Card.is_almost_straight(["Kh", "Ah", "Th"], ["Qs", "2c"]) == 2
    assert Card.is_almost_straight(["3h", "2h", "5h"], ["As", "2c"]) == 2
    assert Card.is_almost_straight(["3h", "2h", "6h"], ["As", "2c"]) == 0
    assert Card.is_almost_straight(["3h", "4h", "6h"], ["5s", "8c"]) == 3

    assert Card.is_almost_flush(["3h", "4h", "6h"], ["5s", "8c"]) == 0
    assert Card.is_almost_flush(["3h", "4h", "6h"], ["5h", "8c"]) == 2
    assert Card.is_almost_flush(["3h", "4h", "6h", "3s"], ["5h", "8c"]) == 1
    assert Card.is_almost_flush(["3h", "4h", "6h", "3s"], ["5h", "8s"]) == 1
    assert Card.is_almost_flush(["3h", "4h", "6h", "3s"], ["5s", "8c"]) == 0
    assert Card.is_almost_flush(["3h", "4h", "6h", "3s", "9s"], ["5h", "8c"]) == 0
