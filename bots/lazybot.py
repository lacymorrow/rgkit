import rg, random
class Robot:
    def act(self, game):

        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
            valid = valid + [['move', loc]]
        
        next_action = valid[range(0,len(valid))]
        
        # if there are enemies around, move
        for loc, bot in game['robots'].iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return next_action
        
        # Move off of spawn
        if 'spawn' in rg.loc_types(sef.location):
            return next_action

        # Guard
        return ['guard']
