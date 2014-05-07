import rg, random
class Robot:
    def act(self, game):
    	
        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
            valid = valid + [['move', loc]]

        # Choose a random action
        next_action = valid[random.randrange(0, len(valid))]

        return next_action
