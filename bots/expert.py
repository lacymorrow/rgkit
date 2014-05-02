import rg, random
class Robot:
    def act(self, game):
        ### CALCUlATE HELPER VARS ###
        # find closest enemy
        CLOSESTE = (1000, 1000)
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= rg.wdist(CLOSESTE, self.location):
                    CLOSESTE = loc
        CLOSESTF = (1000, 1000)
        for loc, bot in game.get('robots').items():
            if bot.player_id == self.player_id:
                if rg.wdist(loc, self.location) <= rg.wdist(CLOSESTF, self.location):
                    CLOSESTF = loc

        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
            valid = valid + [['move', loc]]
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= 1:
                    valid = valid + [['attack', loc]]
        valid = valid + [['guard'], ['suicide']]

        
        ### DEBUG *** PRINT ###
        print "P" + str(self.player_id) + " Robot #" + str(self.robot_id) + " @ " + str(self.location) + " HP: " + str(self.hp)
        print "ClosestE: " + str(CLOSESTE)
        print "ClosestF: " + str(CLOSESTF)
        print "Possible: " + str(valid)
        

        # Choose a random action
        next_action = valid[random.randrange(0, len(valid))]

        # if there are 3+ enemies around, suicide!
        aroundE = 0
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
					aroundE += 1
        if aroundE >= 3:
        	return ['suicide']

        # 3+ friends around, guard
        aroundF = 0
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
					aroundF += 1
        if aroundF >= 3:
            return ['guard']
        	
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']
        
        # if there are enemies around, attack them
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]
                    
        # if enemy closer than center, move towards
        if rg.wdist(CLOSESTE, self.location) < rg.wdist(self.location, rg.CENTER_POINT):
            return ['move', rg.toward(self.location, CLOSESTE)]

        # move toward the center
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
