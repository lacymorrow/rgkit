# rgkit -- Testing kit for [robot game](http://robotgame.net) [![Build Status](https://travis-ci.org/brandonhsiao/rgkit.png?branch=master)](https://travis-ci.org/brandonhsiao/rgkit) #

_Artificial Intelligence_  
_Q-Learning Agents in Robotgame.net_

![Robotgame](http://lacymorrow.com/images/github/robotgame.gif)

### For my thesis I created a Q-Learning agent to learn to play and eventually win the Python programming game at robotgame.net.

#### Robotgame is an online multiplayer programming game in the Python language. Users write code for the logic of a robot which is shared by every robot on their team. The board is made up of a 19x19 grid of squares of either 'normal', 'spawn', or 'wall' types. The default game board is a walled open circle, with spawn points making up the outermost border. The game is played with two opposing teams and a series of 100 turns. On the first and every 10 turns following, 5 robots from each team are generated in random places on spawn points. Each robot begins with 50 health. The player with the most robots at the end of 100 turns, regardless of health. If a robot is located at a spawn point when a spawn occurs, that robot dies immediately. Every turn, every robot on the playing field runs the programmed code and is able to execute one of the following actions:

* Move : N, S, E, W – moves in one direction, range one
* Attack : N, S, E, W – does damage in one direction, with range one
* Guard : Attacks do less damage
* Suicide : Inflicts small amount of splash damage to enemies with range three

The majority of robots submitted to robotgame.net, and indeed all of my previous submissions, use an expert learning method to compete. Actions are hard-coded based on the different possible states the individual robots may be in. My goal was to win against one of my very simple previous expert robots, of the following designs:


* Fleebot : Always moves to an open space, avoiding enemies, walls, and spawns
* Attackbot : Moves to the closest enemy and attacks
* Defendbot : Moves as far as possible towards center then defends
* Guardbot : Moves off of spawn and guards
* Suicidebot : Moves to closest enemy and suicides
* Expertbot :
    * If there are three surrounding enemies, suicide
    * If there are three surrounding friends, guard
    * If there is an enemy around, attack it
    * If an enemy is closer than the center, move towards it
    * else if able to move towards center, do so
    * else do a random valid action

To build the Q-Learning robot logic, dubbed 'ibot', no expert learning methods were used. States are visited, and based upon actions from those states the learner assigns a value which represents that state/action pair's desirability. For the purpose of this writing, I will refer to every learned state-action-value as a utility. In Robotgame, every turn each live robot runs it's 'logic' method called `act()`; every robot on a team uses the same `act()` method. In my Q-learner, actions are chosen based upon the highest utility value for a current state/action pair, with the exception that a state that has been visited less than N amount of times takes priority over highest utility. For every state visited, it's previous state/action utility is updated with the following formula:

    utility[previous] = utility[previous] + α * ( utility[current] – utility[previous )

This differs slightly from the regular Q-Learning formula in that it does not account for a reward.

Since 50 robots total are generated per team per game (5 per 10 turns), each bot shares the same logic. This gave me the advantage during development of having my learner run 50 times per game, instead of just one. By taking advantage of Python's global variables, the robots also are able to share the same utility file, which means that each learns from each others' actions turn-by-turn. Each robot also keeps track of the previous state and previous action taken, and the number of times it has taken each action from a given state in order to compare to the threshold. The robots began with a threshold (N value) of 10, taking each action from each state at least that many times before beginning to use the utility to choose actions. States are represented using a binary integer, every bit corresponding to a single flag indicating some detail about the state. 

##### Possible flags are:

* Enemy north
* Enemy east
* Enemy south
* Enemy west
* Friend north
* Friend east
* Friend south
* Friend west
* Wall north
* Wall east
* Wall south
* Wall west
* Spawn north
* Spawn east
* Spawn south
* Spawn west
* Currently in spawn location
* Currently below 50% health
* X-position
* Y-position

The development library was provided by the creator of Robotgame.net and is called rgkit, it consists of a Game object which creates the map, spawns the respective 50 'bots per turn and runs each live robot's `act()` method once for 100 turns, and a Run object which handles loading the game object, rendering game animations and running multiple games if necessary. It also has the ability to run “headless” - without animations. 

The API provided includes the following:
* `rg.dist(loc1, loc2)`:   
  Returns the mathematical distance between two locations.

* `rg.wdist(loc1, loc2)`:  
  Returns the walking difference between two locations. Since robots can't move diagonally, this is dx + dy.
* `rg.loc_types(loc)`:  
  Returns a list of the types of locations that loc is. Possible values are: 
        * invalid — out of bounds (e.g. (-1, -5) or (23, 66))
        * normal — on the grid
        * spawn — spawn point
        * obstacle — somewhere you can't walk (all the gray squares)
  This method has no contextual information about the game—obstacle, for example, doesn't know if there's an enemy robot standing on a square, for example. All it knows is whether a square is a map obstacle. The returned list may contain a combination of these, like `['normal', 'obstacle']`

* `rg.locs_around(loc[, filter_out=None)`:  
  Returns a list of adjacent locations to loc. You can supply a list of location types to filter out as filter_out. For example, `rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))` would give you a list of all locations you can move into.

* `rg.toward(current_loc, dest_loc)`:  
  Returns the next point on the way from current_loc to dest_loc.

* _constant_ `rg.CENTER_POINT`:  
  The location of the center of the board.

### AttrDict `rg.settings`
A special type of dict that can be accessed via attributes that holds game settings.

* `rg.settings.spawn_every`
  how many turns pass between robots being spawned
* `rg.settings.spawn_per_player`
  how many robots are spawned per player
* `rg.settings.robot_hp`
  default robot HP
* `rg.settings.attack_range`
  a tuple (minimum, maximum) holding range of damage dealt by attacks
* `rg.settings.collision_damage`
  damage dealt by collisions
* `rg.settings.suicide_damage`
  damage dealt by suicides
* `rg.settings.max_turns`
  number of turns per game

The Game file was slightly edited in order to provide the global utility object and save it for use by future iterations after every game. This is the largest of the speed bottlenecks of running the 'bot. A few others are: Looping (3 times) through every 'bot's surrounding location to generate the state, looping through every possible action to choose the one with the highest utility (or lowest threshold), and bubbling and saving state/action data. As the amount of utilities grows, so does the amount of time required to execute one game. To compensate, some games were run with half as many turns to speed up the learning process.

After 20,000 consecutive games over two days, my laptop burnt out, but I was able to download all of the data and utility file. With 35,000 utilities in the “brain”, the 'bots no longer suicide often or remain on spawn points long enough to die. My bot as of now is usually able to win against Suicidebot.

### All of the files used for this project can be found at https://github.com/lacymorrow/robotgame/  .
To run the AI against a dummy 'bot:
* `cd` into the directory
* run `python run.py bots/ai.py bots/guard.py`

##### Requirements: 
* Python – 'sudo apt-get install python'
* Tinker – 'sudo apt-get install python-tk'

Please see this [link](http://robotgame.net/kit) for the instructions.


Lacy Morrow  
CS 4440  
M. Parry  
5 – 7 – 2014  
Artificial Intelligence  
Q-Learning Agents in Robotgame.net
