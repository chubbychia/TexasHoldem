if __name__ == '__main__':
   
    user_rank = {
        '8aacbe2a9e59196c86938da4c4b1db59': [
            [0.39517345399698345, 7296, 7294, 7294]
        ], 'c1cc24d28bbbdbb3f158e170a7d0ee3b': [
            [0.5535444947209653, 7086, 7084, 7084]
        ], 'bb89bb34a222e6983815dcff10336a17': [
            [0.9049773755656109, 4085, 4083, 4083]
        ], '20f9fbdc77c8285b5e0f25ff74f27c3a': [
            [0.36500754147812975, 7305, 7303, 7303]
        ], '3fa8356250ae69cab8a68dd45f26d359': [
            [0.942684766214178, 6385, 6383, 6383]
        ]
    }

    others_rank = [value[0] for key, value in user_rank.iteritems() if key !="8aacbe2a9e59196c86938da4c4b1db59"]
    #print others_rank

   
    me = user_rank["8aacbe2a9e59196c86938da4c4b1db59"][0]
    opponents = others_rank
    opp_count = len(list(opponents))
    rounds = len(me)
    stage_score = []
    # Rank comparison in preflop, flop, turn,river
    for stg in range(rounds):
        me_win = 0
        for opp_index in range(opp_count):
            #Watch out for hand card exception 9999
            if me[stg] != 9999:
                if stg == 0: # Chen formula: 0~1. Bigger prob win. 
                    if me[stg] > opponents[opp_index][stg] or opponents[opp_index][stg] == 9999:
                        me_win += 1
                        #print 'me > opp: %s > %s' %(str(me[stg]),str(opponents[opp_index][stg]))
                    elif me[stg] == opponents[opp_index][stg]:
                        me_win += 0.5   
                        #print 'me = opp: %s > %s' %(str(me[stg]),str(opponents[opp_index][stg]))
                else:  
                    if me[stg] < opponents[opp_index][stg]:
                        # you beat this opponent
                        me_win += 1
                        #print 'me > opp: %s > %s' %(str(me[stg]),str(opponents[opp_index][stg]))
                    elif me[stg] == opponents[opp_index][stg]:
                        me_win += 0.5
                        #print 'me = opp: %s > %s' %(str(me[stg]),str(opponents[opp_index][stg]))           
        
        stage_score.insert(stg, float(me_win) / opp_count)
    print '*** stage score %s' % str(stage_score)

    # for seq, score in enumerate(stage_score):
    #     print "%d, %f" %(seq, score)
        


    #print str(others_rank[0][0])+"--"+str(others_rank[1][0])



