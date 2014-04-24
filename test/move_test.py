import base
from bots import *
from rgkit import game
from rgkit.settings import settings

class TestMove(base.BaseTestCase):
    def test_move_no_collision(self):
        [bot1], [bot2] = self.simulate(
            [RobotMoveRight, RobotMoveLeft],
            [(10, 10)], [(11, 10)],
            [(8, 10)], [(7, 10)])

        assert(not self._game.robot_at_loc((10, 10)))
        assert(not self._game.robot_at_loc((8, 10)))
        self.assertEqual(bot1.hp, settings['robot_hp'])
        self.assertEqual(bot2.hp, settings['robot_hp'])

    def test_basic_collision(self):
        [bot1], [bot2] = self.simulate(
            [RobotMoveRight, RobotMoveLeft],
            [(8, 10)], [(8, 10)],
            [(10, 10)], [(10, 10)])

        self.assertEqual(bot1.hp, settings['robot_hp'] - settings['collision_damage'])
        self.assertEqual(bot2.hp, settings['robot_hp'] - settings['collision_damage'])

    def test_try_invalid_move(self):
        [bot1], [bot2] = self.simulate(
            [RobotMoveInvalid, RobotMoveInvalid],
            [(10, 10)], [(10, 10)],
            [(8, 10)], [(8, 10)])

        self.assertEqual(bot1.hp, settings['robot_hp'])
        self.assertEqual(bot2.hp, settings['robot_hp'])

    def test_move_train(self):
        [bot1, bot2, bot3], _ = self.simulate(
            [RobotMoveLeft, RobotMoveLeft],
            [(10, 10), (11, 10), (12, 10)], [(9, 10), (10, 10), (11, 10)],
            [], [])

        assert(not self._game.robot_at_loc((12, 10)))
        assert(bot1)
        assert(bot2)
        assert(bot3)

    def test_train_collision(self):
        [bot1, bot2, bot3], [bot4] = self.simulate(
            [RobotMoveLeft, RobotMoveRight],
            [(10, 10), (11, 10), (12, 10)], [(10, 10), (11, 10), (12, 10)],
            [(8, 10)], [(8, 10)])

        self.assertEqual(bot1.hp, settings['robot_hp'] - settings['collision_damage'])
        self.assertEqual(bot2.hp, settings['robot_hp'])
        self.assertEqual(bot3.hp, settings['robot_hp'])
        self.assertEqual(bot4.hp, settings['robot_hp'] - settings['collision_damage'])

    def test_try_swap(self):
        [bot1], [bot2] = self.simulate(
            [RobotMoveLeft, RobotMoveRight],
            [(9, 9)], [(9, 9)],
            [(8, 9)], [(8, 9)])

        # they shouldn't have swapped
        self.assertEqual(bot1.player_id, 0)
        self.assertEqual(bot2.player_id, 1)

    def test_try_move_in_circle(self):
        [bot1, bot2], [bot3, bot4] = self.simulate(
            [RobotMoveInCircle, RobotMoveInCircle],
            [(9, 9), (8, 8)], [(9, 9), (8, 8)],
            [(8, 9), (9, 8)], [(8, 9), (9, 8)])

        self.assertEqual(bot1.player_id, 0)
        self.assertEqual(bot2.player_id, 0)
        self.assertEqual(bot3.player_id, 1)
        self.assertEqual(bot4.player_id, 1)

    def test_infinite_recursion(self):
        [bot1, bot2], [bot3] = self.simulate(
            [RobotMoveInCircle, RobotMoveUp],
            [(12, 6), (13, 6)], [(12, 6), (13, 6)],
            [(13, 7)], [(13, 7)])

        self.assertEqual(bot1.player_id, 0)
        self.assertEqual(bot2.player_id, 0)
        self.assertEqual(bot3.player_id, 1)

    def test_overlapping_from_collision(self):
        [bot1, bot2], [bot3, bot4] = self.simulate(
            [RobotMoveRight, RobotMoveUp],
            [(9, 10), (10, 10)], [(9, 10), (10, 10)],
            [(11, 11), (11, 12)], [(11, 11), (11, 12)])

        assert(bot1)
        assert(bot2)
        assert(bot3)
        assert(bot4)

    def test_double_collision(self):
        [bot1], [bot2, bot3] = self.simulate(
            [RobotMoveRight, RobotMoveUp],
            [(9, 10)], [(9, 10)],
            [(9, 11), (10, 11)], [(9, 11), (10, 11)])

        assert(bot1.hp == 40)
        assert(bot2.hp == 45)
        assert(bot3.hp == 45)