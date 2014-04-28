import rg, random, pickle, os.path
# 
### TODO
# re-enable multiprocessing
# account for spawn on turn 10
# Punish for attacking nothing or attacking friend
# Should we normalize the RX functions? IE self.utility[state_action] = (self.utility[state_action] - 100)/2
# 

# Activate EXPERT learning features
EXPERT = True

class Robot:
    previous = (-1, [])
    utility = {}
    def act(self, game):
        # GLOBALS
        global EXPERT

        # LOCALS
        state = self.getState(game)
        actions = [
            ['move', rg.toward(self.location, (self.location[0], self.location[1]+1))],
            ['move', rg.toward(self.location, (self.location[0]+1, self.location[1]))],
            ['move', rg.toward(self.location, (self.location[0], self.location[1]-1))],
            ['move', rg.toward(self.location, (self.location[0]-1, self.location[1]))],
            ['attack', rg.toward(self.location, (self.location[0], self.location[1]+1))],
            ['attack', rg.toward(self.location, (self.location[0]+1, self.location[1]))],
            ['attack', rg.toward(self.location, (self.location[0], self.location[1]-1))],
            ['attack', rg.toward(self.location, (self.location[0]-1, self.location[1]))],
            ['guard'],
            ['suicide']
        ]
        
        # First turn, load utils
        if game.turn == 1:
            self.utility = self.rxLoad()
        
        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
            valid = valid + [['move', loc]]
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= 1:
                    valid = valid + [['attack', loc]]
        valid = valid + [['guard'], ['suicide']]

        # EXPERT LEARNING
        if EXPERT:
            # Avoid invalid moves ***
            # actions = valid
            # Account for standing on spawn on turn 10
            if (game.turn + 1) % 10 == 0 and 'spawn' in rg.loc_types(self.location):
                # On a spawn at turn 10n? You're fucked.
                self.utility = self.rx(str(self.previous[0]) + str(self.previous[1]), -1)
            # Dont make the same mistake move twice
            if self.previous[0] != -1:
                if 'move' in self.previous[1] and self.previous[1][1] != self.location:
                    print "CHOSE " + str(self.previous) + "  *  " + str(valid)
                    self.utility = self.rx(str(self.previous[0]) + str(self.previous[1]), -1)

        # Select random action
        next_action = actions[random.randrange(0, len(actions))]

        # Select highest self.utility action
        for action in actions:
            if (str(state) + str(action)) in self.utility.keys() and (str(state) + str(next_action)) in self.utility.keys():
                if self.utility[str(state) + str(action)] > self.utility[str(state) + str(next_action)]:
                    next_action = action
            elif (str(state) + str(action)) in self.utility.keys() and self.utility[str(state) + str(action)] > 0:
                next_action = action

        # EXPERT LEARNING
        if EXPERT:
            # NEXT MOVE Calculate negative self.utility of move. (suicide, invalid)
            if 'suicide' in next_action:
                val = -1
                # If beside enemies
                if ((state&(1<<0))!=0):
                    val = val + 1
                if ((state&(1<<1))!=0):
                    val = val + 1
                if ((state&(1<<2))!=0):
                    val = val + 1
                if ((state&(1<<3))!=0):
                    val = val + 1
                self.utility = self.rx(str(state) + str(next_action), val)
            
            # Don't make invalid moves
            if next_action not in valid:
                self.utility = self.rx(str(state) + str(next_action), -1)
                next_action = ['guard']

        # DONE CHOOSING ACTION. Set previous
        self.previous = (state, next_action)

        # Game Over, Calculate utilities.
        if game.turn == rg.settings.max_turns - 1:
            self.rxEnd(game)

        # Execute action
        print "P" + str(self.player_id) + " Robot @ " + str(self.location) + " HP: " + str(self.hp) + " Utils: " + str(len(self.utility)) + " Next: " + str(next_action)
        # self.stats(state, next_action)
        # return ['guard']
        return next_action
### END MAIN
    def stats(self, state, next_action):
        ### DEBUG *** PRINT ###
        print "*************\nP" + str(self.player_id) + " Robot @ " + str(self.location) + " HP: " + str(self.hp)
        print "Previous:  " + str(self.previous)
        print "Utilities: " + str(len(self.utility))
        if ((state&(1<<0))!=0):
            print "Enemy top"
        if ((state&(1<<1))!=0):
            print "Enemy right"
        if ((state&(1<<2))!=0):
            print "Enemy bottom"
        if ((state&(1<<3))!=0):
            print "Enemy left"
        if ((state&(1<<0))!=0):
            print "Friend top"
        if ((state&(1<<1))!=0):
            print "Friend right"
        if ((state&(1<<2))!=0):
            print "Friend bottom"
        if ((state&(1<<3))!=0):
            print "Friend left"
        print "Next: " + str(next_action)

        
    def rx(self, state_action, value):
        if state_action in self.utility.keys():
            self.utility[state_action] = self.utility[state_action] + value
        else:
            self.utility[state_action] = value
        return self.utility

    def rxEnd(self, game):
        # Simple. Most bots wins.
        e = f = 0
        state_action = str(self.previous[0]) + str(self.previous[1])
        for loc, bot in game.get('robots').items():
            # Enemy
            if bot.player_id != self.player_id: 
                e = e + 1
            else:
                f = f + 1
        if state_action in self.utility:
            if f > e:
                self.utility[state_action] = self.utility[state_action] + 100
            elif f < e:
                self.utility[state_action] = self.utility[state_action] - 100
        else:
            if f > e:
                self.utility[state_action] = 100
            elif f < e:
                self.utility[state_action] = -100
        # Save utility file
        with open('utility.pickle', 'wb') as handle:
            pickle.dump(self.utility, handle)

    def rxLoad(self):
        util = {}
        if os.path.isfile('utility.pickle'):
            with open('utility.pickle', 'rb') as handle:
                util = pickle.load(handle)
        return util



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
            if loc[1] == self.location[1] - 1:
                # Up
                if 'invalid' in loc:
                    state = state + (1<<8)
                elif 'spawn' in loc:
                    state = state + (1<<9)
                elif 'obstacle' in loc and ((state&(1<<0))!=0):
                    state = state + (1<<10)
            elif loc[0] == self.location[0] + 1:
                # Right
                if 'invalid' in loc:
                    state = state + (1<<11)
                elif 'spawn' in loc:
                    state = state + (1<<12)
                elif 'obstacle' in loc and ((state&(1<<1))!=0):
                    state = state + (1<<13)
            elif loc[1] == self.location[1] + 1:
                # Down
                if 'invalid' in loc:
                    state = state + (1<<14)
                elif 'spawn' in loc:
                    state = state + (1<<15)
                elif 'obstacle' in loc and ((state&(1<<2))!=0):
                    state = state + (1<<16)
            elif loc[0] == self.location[0] - 1:
                # Left
                if 'invalid' in loc:
                    state = state + (1<<17)
                elif 'spawn' in loc:
                    state = state + (1<<18)
                elif 'obstacle' in loc and ((state&(1<<3))!=0):
                    state = state + (1<<19)

        if EXPERT:
            # Account for HP below 50%
            if self.hp < rg.settings.robot_hp/2:
                state = state + (1<<20)



        return state