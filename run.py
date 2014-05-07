#!/usr/bin/env python2

import os
import ast
import argparse
import itertools
import pickle

_is_multiprocessing_supported = False
try:
    from multiprocessing import Pool
except ImportError:
    _is_multiprocessing_supported = False  # the OS does not support it. See http://bugs.python.org/issue3770

###
import game
from settings import settings
util = {}
parser = argparse.ArgumentParser(description="Robot game execution script.")
parser.add_argument("usercode1",
                    help="File containing first robot class definition.")
parser.add_argument("usercode2",
                    help="File containing second robot class definition.")
parser.add_argument("-m", "--map", help="User-specified map file.",
                    default=os.path.join(os.path.dirname(__file__), 'maps/default.py'))
parser.add_argument("-H", "--headless", action="store_true",
                    default=False,
                    help="Disable rendering game output.")
parser.add_argument("-c", "--count", type=int,
                    default=1,
                    help="Game count, default: 1")
parser.add_argument("-A", "--no-animate", action="store_false",
                    default=True,
                    help="Disable animations in rendering.")

def make_player(fname):
    with open(fname) as player_code:
        return game.Player(player_code.read())

def play(players, print_info=True, animate_render=True):
    global util
    util = {}
    if os.path.isfile('util.pickle'):
        f = open('util.pickle', 'rb')
        util = pickle.load(f)
        f.close()
    g = game.Game(*players, record_turns=True, util=util)
    for i in xrange(settings.max_turns):
        if print_info:
            print (' running turn %d ' % (g.turns + 1)).center(70, '-')
        g.run_turn()

    #global utility
    util = g.util
    f = open('util.pickle','wb')
    pickle.dump(util, f)
    f.close()
    if print_info:
        # only import render if we need to render the game;
        # this way, people who don't have tkinter can still
        # run headless
        import render

        render.Render(g, game.settings, animate_render)
        print g.history

    return g.get_scores()

def test_runs_sequentially(args):
    players = [make_player(args.usercode1), make_player(args.usercode2)]
    scores = []
    for i in xrange(args.count):
        scores.append(
            play(players, not args.headless, args.no_animate)
        )
        print scores[-1]
        print len(util)
    return scores

def task(data):
    usercode1, usercode2, headless, no_animate = data
    result = play(
        [
            make_player(usercode1),
            make_player(usercode2)
        ],
        not headless,
        no_animate,
    )
    print result
    return result

def test_runs_concurrently(args):
    data = itertools.repeat(
        [
            args.usercode1,
            args.usercode2,
            args.headless,
            args.no_animate,
        ],
        args.count
    )
    return Pool().map(task, data, 1)

if __name__ == '__main__':

    args = parser.parse_args()

    map_name = os.path.join(args.map)
    map_data = ast.literal_eval(open(map_name).read())
    game.init_settings(map_data)

    runner = test_runs_sequentially
    if _is_multiprocessing_supported and args.count > 1:
        runner = test_runs_concurrently
    scores = runner(args)

    if args.count > 1:
        p1won = sum(p1 > p2 for p1, p2 in scores)
        p2won = sum(p2 > p1 for p1, p2 in scores)
        print [p1won, p2won, args.count - p1won - p2won]
