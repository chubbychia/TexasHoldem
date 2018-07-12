# Texas Poker AI for Allhands

## Basic rules

### Deal Stage

* Take action base on score of our hole cards
  * Only play with strong cards
    * sum of values
    * pair
    * possible straight
    * some suit (possible flush)
  * Play if expected value >= 0
  * Consider current players
    * less players more aggressive 

### Flop Stage

* Take action base on win probability
  * calculate probability to win one player by simulation
    * exact calculation take too much time
    * sampling next two board cards and another player's hole cards
    * use this module : [deuces](https://github.com/worldveil/deuces)
  * evaluate final win probability by win_one_prob ** (# virtual players)

### Turn Stage and River Stage

* Take action base on our win probability (similar to flop round)
  * use this module[holdem_calc](https://github.com/ktseng/holdem_calc) to calculate prob to win one player :
    * Calculate exact win probability
    * Monte Carlo simulation
  * evaluate final win probability by win_one_prob ** (# virtual players)

### Virutal players count

* Base line + historical(bet + raise + allin) + current_player_historical(bet + raise + allin)
  * Base line
    * Players in Flop stage (for Flop/Turn/River)
    * Players in Deal stage (for Deal)
    * Current players if the information not found
* Exclude myself
