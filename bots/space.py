import rg

class Robot:
    def act(self, game):
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
        cloc ( 1000, 1000)
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= rg.wdist(cloc, self.location):
                    cloc = loc
	 
        
        # if enemy closer than center, move towards
		if rg.wdist(closestE, self.location) < rg.wdist(self.location, rg.CENTER_POINT):
			return ['move', rg.toward(self.location, closestE)]
        '''
    	if 'obstacle' in rg.loc_types(rg.toward(self.location, rg.CENTER_POINT)):
			return ['guard']
		# move toward the center
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
