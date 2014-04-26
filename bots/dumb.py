import rg
previous = (0,0)
class Robot:
    def act(self, game):
        global previous
        ### CALCUlATE HELPER VARS ###
        # find closest enemy
        cloc = ( 1000, 1000)
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if rg.wdist(bot.location, self.location) <= rg.wdist(cloc, self.location):
                    cloc = loc

        valid = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
        
        ### DEBUG *** PRINT ###
        print "Possible: " + str(valid)
        print "Previous: " + str(previous)


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
        '''
        # if enemy closer than center, move towards
        if rg.wdist(closestE, self.location) < rg.wdist(self.location, rg.CENTER_POINT):
            return ['move', rg.toward(self.location, closestE)]
        
        # if obstacle in the way, guard
        if rg.toward(self.location, rg.CENTER_POINT) not in valid:
            print "Guarding"
            return ['guard']

        
        # move toward the enemy
        if rg.toward(self.location, cloc) in valid:
            previous = self.location
            return ['move', rg.toward(self.location, cloc)]
        '''
        for i in valid:
            print "prev: " + str(previous)
            print "i: " + str(i)
            if i != previous:
                previous = self.location
                return ['move', rg.toward(self.location, i)]
        return ['move', rg.toward(self.location, previous)]
        # move toward the center
        # return ['move', rg.toward(self.location, rg.CENTER_POINT)]
