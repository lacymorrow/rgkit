import rg, random
class Robot:
    def act(self, game):

        # Valid actions
        valid = []
        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
            valid = valid + [['move', loc]]

        # move toward the center
        if ['move', rg.toward(self.location, rg.CENTER_POINT)] in valid:
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]

        # Guard
        return ['guard']
