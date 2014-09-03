import rg, random
class Robot:
    def act(self, game):

        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
            valid = valid + [['move', loc]]

        next_action = valid[range(0,len(valid))]
        # Move off of spawn
        if 'spawn' in rg.loc_types(sef.location):
            return next_action

        # Guard
        return ['guard']
