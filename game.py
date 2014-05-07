import inspect
import random
import sys
import traceback
import imp
###
import rg
import defaultrobots
from settings import settings, AttrDict

utility = {}
def init_settings(map_data):
    global settings
    settings.spawn_coords = map_data['spawn']
    settings.obstacles = map_data['obstacle']
    settings.start1 = map_data['start1']
    settings.start2 = map_data['start2']
    rg.set_settings(settings)

class Player:
    def __init__(self, code=None, robot=None):
        if code is not None:
            self._mod = imp.new_module('usercode%d' % id(self))
            exec code in self._mod.__dict__
            self._robot = None
        elif robot is not None:
            self._mod = None
            self._robot = robot
        else:
            raise Exception('you need to provide code or a robot')

    def get_robot(self):
        if self._robot is not None:
            return self._robot

        mod = defaultrobots
        if self._mod is not None:
            if hasattr(self._mod, 'Robot'):
                if inspect.isclass(getattr(self._mod, 'Robot')):
                    mod = self._mod

        self._robot = getattr(mod, 'Robot')()
        return self._robot

class InternalRobot:
    def __init__(self, location, hp, player_id, robot_id, field, instance_id=None, util={}):
        self.location = location
        self.hp = hp
        self.player_id = player_id
        self.robot_id = robot_id
        self.field = field
        self.instance_id = instance_id
        self.utility = util

    def __repr__(self):
        return '<%s: player: %d, hp: %d>' % (
            self.location, self.player_id, self.hp
        )

    @staticmethod
    def parse_command(action):
        return (action[0], action[1:])

    def is_valid_action(self, action):
        global settings

        cmd, params = InternalRobot.parse_command(action)
        if not cmd in settings.valid_commands:
            return False

        if cmd == 'move' or cmd == 'attack':
            if not self.movable_loc(params[0]):
                return False

        return True

    def issue_command(self, action, actions):
        cmd, params = InternalRobot.parse_command(action)
        if cmd == 'move' or cmd == 'attack':
            getattr(self, 'call_' + cmd)(params[0], actions)
        if cmd == 'suicide':
            self.call_suicide(actions)

    def get_robots_around(self, loc):
        locs_around = rg.locs_around(loc, filter_out=['obstacle', 'invalid'])
        locs_around.append(loc)

        robots = [self.field[x] for x in locs_around]
        return [x for x in robots if x not in (None, self)]

    def movable_loc(self, loc):
        good_around = rg.locs_around(
            self.location, filter_out=['invalid', 'obstacle'])
        return loc in good_around

    def is_collision(self, loc, robot, cmd, params, actions, move_exclude):
        if cmd == 'suicide':
            return False
        if cmd != 'move':
            return robot.location == loc
        if params[0] == loc:
            return robot not in move_exclude
        elif robot.location == loc:
            if params[0] == self.location:
                return True
            move_exclude = move_exclude | set([robot])
            return (len(self.get_collisions(params[0], actions, move_exclude)) > 0)
        return False

    def get_collisions(self, loc, action_table, move_exclude=None):
        if move_exclude is None:
            move_exclude = set()

        collisions = []
        nearby_robots = self.get_robots_around(loc)
        nearby_robots = set(nearby_robots) - move_exclude

        for robot in nearby_robots:
            cmd, params = InternalRobot.parse_command(action_table[robot])
            if self.is_collision(loc, robot, cmd, params, action_table, move_exclude):
                collisions.append((robot, cmd, params))
        return collisions

    @staticmethod
    def damage_robot(robot, damage):
        robot.hp -= int(damage)

    def call_move(self, loc, action_table):
        global settings

        loc = tuple(map(int, loc))
        collisions = self.get_collisions(loc, action_table)

        for robot, cmd, params in collisions:
            if robot.player_id != self.player_id:
                if cmd != 'guard':
                    InternalRobot.damage_robot(robot, settings.collision_damage)
                if cmd != 'move':
                    InternalRobot.damage_robot(self, settings.collision_damage)

        if len(collisions) == 0:
            self.location = loc

    # should only be called after all robots have been moved
    def call_attack(self, loc, action_table, damage=None):
        global settings

        damage = int(damage or random.randint(*settings.attack_range))

        robot = self.field[loc]
        if not robot or robot.player_id == self.player_id:
            return

        cmd, params = InternalRobot.parse_command(action_table[robot])
        InternalRobot.damage_robot(robot,
                                   damage if cmd != 'guard' else damage / 2)

    def call_suicide(self, action_table):
        self.hp = 0
        self.call_attack(self.location, action_table, damage=settings.suicide_damage)
        for loc in rg.locs_around(self.location):
            self.call_attack(loc, action_table, damage=settings.suicide_damage)

# just to make things easier
class Field:
    def __init__(self, size):
        self.field = [[None for x in range(size)] for y in range(size)]

    def __getitem__(self, point):
        try:
            return self.field[int(point[1])][int(point[0])]
        except TypeError:
            print point[1], point[0]

    def __setitem__(self, point, v):
        try:
            self.field[int(point[1])][int(point[0])] = v
        except TypeError:
            print point[1], point[0]

class Game:
    def __init__(self, player1, player2, record_turns=False, unit_testing=False, util={}):
        self._players = (player1, player2)
        self.turns = 0
        self._robots = []
        self._field = Field(settings.board_size)
        self._unit_testing = unit_testing
        self._id_inc = 0
        self.util = util

        self._record = record_turns
        if self._record:
            self.history = [[] for i in range(2)]
            self.action_at = dict((x, dict()) for x in range(settings.max_turns))
            self.last_locs = {}
            self.last_hps = {}

        self.spawn_starting()

    def get_robot_id(self):
        ret = self._id_inc
        self._id_inc += 1
        return ret

    def spawn_starting(self):
        global settings
        for coord in settings.start1:
            self.spawn_robot(0, coord)
        for coord in settings.start2:
            self.spawn_robot(1, coord)

    def build_game_info(self):
        global settings
        return AttrDict({
            'robots': dict((
                y.location,
                AttrDict(dict(
                    (x, getattr(y, x)) for x in
                    (settings.exposed_properties + settings.player_only_properties)
                ))
            ) for y in self._robots),
            'turn': self.turns,
        })

    def build_players_game_info(self):
        game_info_copies = [self.build_game_info(), self.build_game_info()]

        for i in range(2):
            for loc, robot in game_info_copies[i].robots.iteritems():
                if robot.player_id != i:
                    for property in settings.player_only_properties:
                        del robot[property]
        return game_info_copies

    def make_robots_act(self):
        global settings

        game_info_copies = self.build_players_game_info()
        actions = {}

        for robot in self._robots:
            user_robot = self._players[robot.player_id].get_robot()
            user_robot.utility = self.util
            for prop in settings.exposed_properties + settings.player_only_properties:
                setattr(user_robot, prop, getattr(robot, prop))
            try:
                next_action = user_robot.act(game_info_copies[robot.player_id])
                if not robot.is_valid_action(next_action):
                    raise Exception('Bot %d: %s is not a valid action from %s' % (robot.player_id + 1, str(next_action), robot.location))
            except Exception:
                traceback.print_exc(file=sys.stdout)
                next_action = ['guard']
            actions[robot] = next_action
            self.util = user_robot.utility

        commands = list(settings.valid_commands)
        commands.remove('guard')
        commands.remove('move')
        commands.insert(0, 'move')

        self.last_locs = {}
        self.last_hps = {}
        for cmd in commands:
            for robot, action in actions.iteritems():
                if action[0] != cmd:
                    continue

                old_loc = robot.location
                self.last_hps[old_loc] = robot.hp  # save hp before actions are processed
                try:
                    robot.issue_command(action, actions)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    actions[robot] = ['guard']
                if robot.location != old_loc:
                    if self._field[old_loc] is robot:
                        self._field[old_loc] = None
                        self.last_locs[robot.location] = old_loc
                    self._field[robot.location] = robot
                else:
                    self.last_locs[robot.location] = robot.location
        return actions

    def robot_at_loc(self, loc):
        return self._field[loc]

    def spawn_robot(self, player_id, loc, instance_id=None):
        if self.robot_at_loc(loc) is not None:
            return False
        robot_id = self.get_robot_id()
        robot = InternalRobot(loc, settings.robot_hp, player_id, robot_id, self._field, random.randrange(1,10+1), self.util)
        self._robots.append(robot)
        self._field[loc] = robot
        if self._record:
            self.action_at[self.turns][loc] = {
                'name': 'spawn',
                'target': None,
                'hp': robot.hp,
                'hp_end': robot.hp,
                'loc': loc,
                'loc_end': loc,
                'player': player_id
            }
        return True

    def spawn_robot_batch(self):
        global settings

        locs = random.sample(settings.spawn_coords, settings.spawn_per_player * 2)
        for player_id in (0, 1):
            for i in range(settings.spawn_per_player):
                self.spawn_robot(player_id, locs.pop())

    def clear_spawn_points(self):
        for loc in settings.spawn_coords:
            if self._field[loc] is not None:
                self._robots.remove(self._field[loc])
                self._field[loc] = None
                if self._record:
                    old_loc = self.last_locs.get(loc, loc)
                    # simulate death by making this robot end with 0 HP in the actions log
                    self.action_at[self.turns][old_loc] = {'hp_end': 0}

    def remove_dead(self):
        to_remove = [x for x in self._robots if x.hp <= 0]
        for robot in to_remove:
            self._robots.remove(robot)
            if self._field[robot.location] == robot:
                self._field[robot.location] = None

    def make_history(self, actions):
        global settings

        robots = [[] for i in range(2)]
        for robot in self._robots:
            robot_info = []
            for prop in settings.exposed_properties:
                if prop != 'player_id':
                    robot_info.append(getattr(robot, prop))
            if robot in actions:
                robot_info.append(actions[robot])
            robots[robot.player_id].append(robot_info)
        return robots

    def run_turn(self):
        global settings

        actions = self.make_robots_act()

        self.remove_dead()

        if not self._unit_testing:
            if self.turns % settings.spawn_every == 0:
                self.clear_spawn_points()
                self.spawn_robot_batch()

        if self._record:
            round_history = self.make_history(actions)
            for i in (0, 1):
                self.history[i].append(round_history[i])

            for robot, action in actions.iteritems():
                loc = self.last_locs.get(robot.location, robot.location)
                log_action = self.action_at[self.turns].get(loc, {})
                hp_start = self.last_hps.get(loc, robot.hp)
                log_action['name'] = log_action.get('name', action[0])
                log_action['target'] = action[1] if len(action) > 1 else None
                log_action['hp'] = log_action.get('hp', hp_start)
                log_action['hp_end'] = log_action.get('hp_end', robot.hp)
                log_action['loc'] = log_action.get('loc', loc)
                log_action['loc_end'] = log_action.get('loc_end', robot.location)
                log_action['player'] = log_action.get('player', robot.player_id)
                self.action_at[self.turns][loc] = log_action

        self.turns += 1

    def get_scores(self):
        scores = [0, 0]
        for robot in self._robots:
            scores[robot.player_id] += 1
        return scores

    def get_robot_actions(self, turn):
        global settings
        if turn in self.action_at:
            return self.action_at[turn]
        elif turn <= 0:
            return self.action_at[1]
        else:
            return self.action_at[settings.max_turns-1]
