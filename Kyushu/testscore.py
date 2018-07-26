if __name__ == '__main__':
   
    user_rank = {"a_player": [3245,6435,1345,6543],"b_player":[9324,4632,2345,5643],"c_player":[6453,1453,1225,1002]}    
    
    others_rank = [value for key, value in user_rank.iteritems() if key !="a_player" ]

    print others_rank

    me = user_rank["a_player"]
    opponents = [[6453, 1453, 1225, 1002], [9324, 4632, 2345, 5643]]
    opp_count = len(list(opponents))
    stage_score = []
    # Rank comparison in preflop, flop, turn,river
    for stg in range(4):
        me_win = 0
        for opp_index in range(opp_count): 
            if me[stg] < opponents[opp_index][stg]:
                    # you beat this opponent
                me_win += 1
            elif me[stg] == opponents[opp_index][stg]:
                me_win += 0.5           
        stage_score.insert(stg, float(me_win) / opp_count)
    print  stage_score

    for seq, score in enumerate(stage_score):
        print "%d, %f" %(seq, score)
        


    #print str(others_rank[0][0])+"--"+str(others_rank[1][0])



