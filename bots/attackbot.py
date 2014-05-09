import rg
class Robot:
    def act(self, game):

        # find closest enemy
        CLOSESTE = (1000, 1000)
        for loc, bot in game.get('robots').items():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= rg.wdist(CLOSESTE, self.location):
                    CLOSESTE = loc
        
        # if there are enemies around, attack them
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]
                    
        # move towards enemy
        return ['move', rg.toward(self.location, CLOSESTE)]
