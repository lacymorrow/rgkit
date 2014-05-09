import rg, random, pickle, os.path
# 
### TODO
# re-enable multiprocessing
# Create getbit function
# Punish for attacking nothing or attacking friend
#  REPRESENT DIFFERENT TYPES OF STATES ( {BesideLeftWall: moveright+2, EnemyLeft: attackleft + 4})
# Q Learning Agent

# Activate EXPERT learning features
EXPERT = True
GAMMA = .9
THRESHOLD = 10  # active learner

# REWARD
ATTACK_SUCCESS = False
ATTACK_RECEIVED = False
HEALTH = True
INVALID = False
PRIOR = False
REPEAT = False
SPAWN = False
SPAWN_MOVE = False
SUICIDE = True




class Robot:
    previous = {-1: [-1, [], -1]}
    saved = False
    loaded = False
    def act(self, game):
        # GLOBALS
        global EXPERT

        # LOCALS
        state = self.getState(game)
        actions = [
            ['move', rg.toward(self.location, (self.location[0], self.location[1]-1))],
            ['move', rg.toward(self.location, (self.location[0]+1, self.location[1]))],
            ['move', rg.toward(self.location, (self.location[0], self.location[1]+1))],
            ['move', rg.toward(self.location, (self.location[0]-1, self.location[1]))],
            ['attack', rg.toward(self.location, (self.location[0], self.location[1]-1))],
            ['attack', rg.toward(self.location, (self.location[0]+1, self.location[1]))],
            ['attack', rg.toward(self.location, (self.location[0], self.location[1]+1))],
            ['attack', rg.toward(self.location, (self.location[0]-1, self.location[1]))],
            ['guard'],
            #['suicide']
        ]
        if self.robot_id not in self.previous.keys():
            self.previous[self.robot_id] = (state, ['current', self.location], self.hp)
        
            # Valid actions
        if EXPERT:
            valid = valid_moves = []
            for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                valid_moves = valid_moves + [['move', loc]]
            valid = valid_moves + [['guard'], ['suicide']]
            for loc, bot in game['robots'].iteritems():
                if bot.player_id != self.player_id:
                    if rg.wdist(loc, self.location) <= 1:
                        valid = valid + [['attack', loc]]

                    # EXPERT LEARNING. Attack hit!
                    if ATTACK_SUCCESS and 'attack' in self.previous[self.robot_id][1][0] and loc == self.previous[self.robot_id][1][1]:
                        self.utility = self.rx(str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1]), +10)
        # Avoid invalid moves ***
        # actions = valid

        # EXPERT LEARNING
        if EXPERT:
            # Lost Health!
            if ATTACK_RECEIVED and self.hp < self.previous[self.robot_id][2] and 'guard' not in self.previous[self.robot_id][1]:
                self.utility = self.rx(str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1]), -10)
            # Account for standing on spawn on turn 10
            if SPAWN and 'spawn' in rg.loc_types(self.location):
                if (game.turn) % 10 == 0 or 'guard' in self.previous[self.robot_id][1]:
                    print "I'm fucked"
                    # MOVE DUMMY
                    # On a spawn at turn 10n? You're fucked. On a spawn and guarding? You're dumb.
                    self.utility = self.rx(str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1]), -10)
            # Dont make the same mistake move twice
            if REPEAT and self.previous[self.robot_id][0] != -1:
                if 'move' in self.previous[self.robot_id][1] and self.previous[self.robot_id][1][1] != self.location:
                    self.utility = self.rx(str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1]), -10)

        # Select random action
        next_action = actions[random.randrange(0, len(actions))]

        # Select highest self.utility action
        th = False
        for action in actions:
            if th == False and (str(state) + str(action)) in self.utility.keys():
                if (str(state) + str(next_action)) in self.utility.keys():
                    if self.utility[str(state) + str(action)][0] > self.utility[str(state) + str(next_action)][0]:
                        next_action = action
                # Learn until threshold
                if self.utility[str(state) + str(action)][1] < THRESHOLD:
                    next_action = action
                    th = True
            elif th == False:
                next_action = action
                th = True

        # Q-LEARNING AGENT
        if (str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1])) in self.utility.keys() and str(state) + str(next_action) in self.utility.keys():
        	state_action = str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1])
        	cur = self.utility[state_action][0]
        	nxt = self.utility[str(state) + str(next_action)][0]
        	self.utility = self.rx(state_action, cur + GAMMA * (nxt - cur))

        # EXPERT LEARNING
        if EXPERT:
            # NEXT MOVE Calculate negative self.utility of move. (suicide, invalid)
            if SUICIDE and 'suicide' in next_action:
                val = -50
                # If beside enemies
                if ((state&(1<<0))!=0):
                    val = val + 20
                if ((state&(1<<1))!=0):
                    val = val + 20
                if ((state&(1<<2))!=0):
                    val = val + 20
                if ((state&(1<<3))!=0):
                    val = val + 20
                self.utility = self.rx(str(state) + str(next_action), val)
            if SPAWN_MOVE and 'spawn' in rg.loc_types(self.location) and (game.turn) % 10 == 0:
                # GET OUT OF THE WAY!!
                next_action = valid_moves[random.randrange(0, len(valid_moves))]
            # Don't make invalid moves
            if INVALID and next_action not in valid:
                self.utility = self.rx(str(state) + str(next_action), -10)
                next_action = ['guard']

        # DONE CHOOSING ACTION. Set previous
        self.previous[self.robot_id] = (state, next_action, self.hp)

        # Game Over, Calculate utilities.
        if game.turn == rg.settings.max_turns - 1:
            self.rxEnd(game)

        # Update s_a util
        self.utility = self.rx(str(state) + str(next_action), 0)

        # Execute action
        #print "P" + str(self.player_id) + " Robot #" + str(self.robot_id) + " @ " + str(self.location) + " HP: " + str(self.hp) + " Utils: " + str(len(self.utility)) + " Next: " + str(next_action)
        # self.stats(state, next_action)
        return next_action
### END MAIN
    def stats(self, state, next_action):
        ### DEBUG *** PRINT ###
        print "*************\nP" + str(self.player_id) + " Robot #" + str(self.robot_id) + " @ " + str(self.location) + " HP: " + str(self.hp) + " U: " + str(len(self.utility))
        print "Previous:  " + str(self.previous[self.robot_id])
        if self.hp < self.previous[self.robot_id][2]:
            print "Took damage!"
        if ((state&(1<<0))!=0):
            print "Enemy top"
        if ((state&(1<<1))!=0):
            print "Enemy right"
        if ((state&(1<<2))!=0):
            print "Enemy bottom"
        if ((state&(1<<3))!=0):
            print "Enemy left"
        if ((state&(1<<4))!=0):
            print "Friend top"
        if ((state&(1<<5))!=0):
            print "Friend right"
        if ((state&(1<<6))!=0):
            print "Friend bottom"
        if ((state&(1<<7))!=0):
            print "Friend left"
        print "Next: " + str(next_action)

        
    def rx(self, state_action, value):
        if state_action in self.utility.keys():
            self.utility[state_action] = ((self.utility[state_action][0] + value), (self.utility[state_action][1] + 1))
        else:
            self.utility[state_action] = (value, 1)
        return self.utility

    def rxEnd(self, game):
        # Simple. Most bots wins.
        e = f = 0
        state_action = str(self.previous[self.robot_id][0]) + str(self.previous[self.robot_id][1])
        for loc, bot in game.get('robots').items():
            # Enemy
            if bot.player_id != self.player_id: 
                e = e + 1
            else:
                f = f + 1
        if state_action in self.utility:
            if f > e:
                self.utility[state_action] = ((self.utility[state_action][0] + 1000), (self.utility[state_action][1] + 1))
            else:
                self.utility[state_action] = ((self.utility[state_action][0] - 1000), (self.utility[state_action][1] + 1))
        else:
            if f > e:
                self.utility[state_action] = (1000, 1)
            else:
                self.utility[state_action] = (-1000, 1)


    def getState(self, game):
        state = 0
        # Other bots
        for loc, bot in game.get('robots').items():
            # Enemy
            if bot.player_id != self.player_id: 
                if loc[1] == self.location[1] - 1 and loc[0] == self.location[0]:
                    # Up
                    state = state + (1<<0)
                elif loc[0] == self.location[0] + 1 and loc[1] == self.location[1]:
                    # Right
                    state = state + (1<<1)
                elif loc[1] == self.location[1] + 1 and loc[0] == self.location[0]:
                    # Down
                    state = state + (1<<2)
                elif loc[0] == self.location[0] - 1 and loc[1] == self.location[1]:
                    # Left
                    state = state + (1<<3)
            #Friend
            else:
                if loc[1] == self.location[1] - 1 and loc[0] == self.location[0]:
                    # Up
                    state = state + (1<<4)
                elif loc[0] == self.location[0] + 1 and loc[1] == self.location[1]:
                    # Right
                    state = state + (1<<5)
                elif loc[1] == self.location[1] + 1 and loc[0] == self.location[0]:
                    # Down
                    state = state + (1<<6)
                elif loc[0] == self.location[0] - 1 and loc[1] == self.location[1]:
                    # Left
                    state = state + (1<<7)

        # Surrounding types
        for loc in rg.locs_around(self.location):
            lt = rg.loc_types(loc)
            if loc[1] == self.location[1] - 1:
                # Up
                if 'invalid' in lt:
                    state = state + (1<<8)
                elif 'spawn' in lt:
                    state = state + (1<<9)
                elif 'obstacle' in lt and ((state&(1<<0))!=0):
                    state = state + (1<<10)
            elif loc[0] == self.location[0] + 1:
                # Right
                if 'invalid' in lt:
                    state = state + (1<<11)
                elif 'spawn' in lt:
                    state = state + (1<<12)
                elif 'obstacle' in lt and ((state&(1<<1))!=0):
                    state = state + (1<<13)
            elif loc[1] == self.location[1] + 1:
                # Down
                if 'invalid' in lt:
                    state = state + (1<<14)
                elif 'spawn' in lt:
                    state = state + (1<<15)
                elif 'obstacle' in lt and ((state&(1<<2))!=0):
                    state = state + (1<<16)
            elif loc[0] == self.location[0] - 1:
                # Left
                if 'invalid' in lt:
                    state = state + (1<<17)
                elif 'spawn' in lt:
                    state = state + (1<<18)
                elif 'obstacle' in lt and ((state&(1<<3))!=0):
                    state = state + (1<<19)
        # SAVE LOCATION - 5 bits per x, y
        state = state + (self.location[0]<<20)
        state = state + (self.location[1]<<25)

        # On a spawn point
        if 'spawn' in rg.loc_types(self.location):
        	state = state + (1<<30) 

        if EXPERT and HEALTH:
            # Account for HP below 50%
            if self.hp < rg.settings.robot_hp/2:
                state = state + (1<<31)



        return state
