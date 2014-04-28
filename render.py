import Tkinter
import game
import rg
import time

def millis():
    return int(time.time() * 1000)

def rgb_to_hex(r, g, b, normalized=True):
    if normalized:
        return '#%02x%02x%02x' % (r*255, g*255, b*255)
    else:
        return '#%02x%02x%02x' % (r, g, b)

def blend_colors(color1, color2, weight):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 * weight + r2 * (1-weight)
    g = g1 * weight + g2 * (1-weight)
    b = b1 * weight + b2 * (1-weight)
    return (r, g, b)

class HighlightSprite:
    def __init__(self, loc, target, render):
        self.location = loc
        self.target = target
        self.renderer = render
        self.hlt_square = None
        self.target_square = None

    def clear(self):
        self.renderer.remove_object(self.hlt_square)
        self.renderer.remove_object(self.target_square)
        self.hlt_square = None
        self.target_square = None

    def animate(self, delta=0):
        # blink like a cursor
        if self.location is not None:
            if delta < 0.5:
                if self.hlt_square is None:
                    color = rgb_to_hex(*self.renderer._settings.highlight_color)
                    self.hlt_square = self.renderer.draw_grid_object(self.location, fill=color, layer=2, width=0)
                if self.target is not None and self.target_square is None:
                    color = rgb_to_hex(*self.renderer._settings.target_color)
                    self.target_square = self.renderer.draw_grid_object(self.target, fill=color, layer=2, width=0)
            else:
                self.clear()

class RobotSprite:
    def __init__(self, action_info, render):
        self.location = action_info['loc']
        self.location_next = action_info['loc_end']
        self.action = action_info['name']
        self.target = action_info['target']
        self.hp = max(0, action_info['hp'])
        self.hp_next = max(0, action_info['hp_end'])
        self.id = action_info['player']
        self.renderer = render
        self.animation_offset = (0, 0)

        # Tkinter objects
        self.square = None
        self.overlay = None
        self.text = None

    def animate(self, delta=0):
        """Animate this sprite

           delta is between 0 and 1. it tells us how far along to render (0.5 is halfway through animation)
                this allows animation logic to be separate from timing logic
        """
        # fix delta to between 0 and 1
        delta = max(0, min(delta, 1))
        bot_color = self.compute_color(self.id, self.hp)
        # if spawn, fade in
        if self.action == 'spawn':
            bot_color = blend_colors(bot_color, self.renderer._settings.normal_color, delta)
        # if dying, fade out
        elif self.hp_next <= 0:
            bot_color = blend_colors(bot_color, self.renderer._settings.normal_color, 1-delta)
        bot_color = rgb_to_hex(*bot_color)
        x, y = self.location
        self.animation_offset = (0, 0)
        if self.action == 'move':
            # if normal move, start at bot location and move to next location
            # (note that first half of all move animations is the same)
            if delta < 0.5 or self.location_next == self.target:
                x, y = self.location
                tx, ty = self.target
            # if we're halfway through this animation AND the movement didn't succeed, reverse it (bounce back)
            else:
                # starting where we wanted to go
                x, y = self.target
                # and ending where we are now
                tx, ty = self.location
            dx = tx - x
            dy = ty - y
            off_x = dx*delta*self.renderer._blocksize
            off_y = dy*delta*self.renderer._blocksize
            self.animation_offset = (off_x, off_y)
        elif self.action == 'attack':
            if self.overlay is None and self.renderer.show_arrows.get():
                offset = (self.renderer._blocksize/2, self.renderer._blocksize/2)
                self.overlay = self.renderer.draw_line(self.location, self.target, layer=4, fill='orange', offset=offset, width=3.0, arrow=Tkinter.LAST)
            elif self.overlay is not None and not self.renderer.show_arrows.get():
                self.renderer.remove_object(self.overlay)
                self.overlay = None
        elif self.action == 'guard':
            pass
        elif self.action == 'suicide':
            pass
        self.draw_bot(delta, (x, y), bot_color)
        self.draw_bot_hp(delta, (x, y))

    def compute_color(self, player, hp):
        max_hp = float(self.renderer._settings.robot_hp + 20)
        r, g, b = self.renderer._settings.colors[player]
        hp = float(hp + 20)
        r *= hp / max_hp
        g *= hp / max_hp
        b *= hp / max_hp
        r = max(r, 0)
        g = max(g, 0)
        b = max(b, 0)
        return (r, g, b)

    def draw_bot(self, delta, loc, color):
        x, y = self.renderer.grid_to_xy(loc)
        rx, ry = self.renderer.square_bottom_corner((x, y))
        ox, oy = self.animation_offset
        if self.square is None:
            self.square = self.renderer.draw_grid_object(self.location, type="circle", layer=3, fill=color, width=0)
        self.renderer._win.itemconfig(self.square, fill=color)
        self.renderer._win.coords(self.square, (x+ox, y+oy, rx+ox, ry+oy))

    def draw_bot_hp(self, delta, loc):
        x, y = self.renderer.grid_to_xy(loc)
        ox, oy = self.animation_offset
        tex_color = "#888"
        val = int(self.hp * (1-delta) + self.hp_next * delta)
        if self.text is None:
            self.text = self.renderer.draw_text(self.location, val, tex_color)
        self.renderer._win.itemconfig(self.text, text=val)
        self.renderer._win.coords(self.text, (x+ox+10, y+oy+10))

    def clear(self):
        self.renderer.remove_object(self.square)
        self.renderer.remove_object(self.overlay)
        self.renderer.remove_object(self.text)
        self.square = None
        self.overlay = None
        self.text = None

class Render:
    def __init__(self, game_inst, settings, animations, block_size=25):
        self._settings = settings
        self.animations = animations
        self._blocksize = block_size
        self._winsize = block_size * self._settings.board_size + 40
        self._game = game_inst
        self._paused = True
        self._layers = {}

        self._master = Tkinter.Tk()
        self._master.title('Robot Game')

        width = self._winsize
        height = self._winsize + self._blocksize * 11/4
        self._win = Tkinter.Canvas(self._master, width=width, height=height)
        self._win.pack()

        self.prepare_backdrop(self._win)
        self._label = self._win.create_text(
            self._blocksize/2, self._winsize + self._blocksize/2,
            anchor='nw', font='TkFixedFont', fill='white')

        self.create_controls(self._win, width, height)

        self._turn = 1

        self._highlighted = None
        self._highlighted_target = None

        # Animation stuff (also see #render heading in settings.py)
        self._sprites = []
        self._highlight_sprite = None
        self._t_paused = 0
        self._t_frame_start = 0
        self._t_next_frame = 0
        self.slider_delay = 0
        self.update_frame_timing()

        self.draw_background()
        self.update_title()
        self.update_sprites_new_turn()
        self.paint()

        self.callback()
        self._win.mainloop()

    def remove_object(self, obj):
        if obj is not None:
            self._win.delete(obj)

    def change_turn(self, turns):
        self._turn = min(max(self._turn + turns, 1), self._game.turns)
        self.update_title()
        self._highlighted = None
        self._highlighted_target = None
        self.update_sprites_new_turn()
        self.paint()

    def toggle_pause(self):
        self._paused = not self._paused
        print "paused" if self._paused else "unpaused"
        self._toggle_button.config(text=u'\u25B6' if self._paused else u'\u25FC')
        now = millis()
        if self._paused:
            self._t_paused = now
        else:
            if self._t_paused != 0:
                self.update_frame_timing(now - (self._t_paused - self._t_frame_start))
            else:
                self.update_frame_timing(now)

    def update_frame_timing(self, tstart=None):
        if tstart is None:
            tstart = millis()
        self._t_frame_start = tstart
        self._t_next_frame = tstart + self.slider_delay

    def create_controls(self, win, width, height):
        def change_turn(turns):
            if not self._paused:
                self.toggle_pause()
            self.change_turn(turns)

        def prev():
            change_turn(-1)

        def next():
            change_turn(+1)

        def restart():
            change_turn((-self._turn)+1)

        def pause():
            self.toggle_pause()

        def onclick(event):
            x = (event.x - 20) / self._blocksize
            y = (event.y - 20) / self._blocksize
            loc = (x, y)
            if loc[0] >= 0 and loc[1] >= 0 and loc[0] < self._settings.board_size and loc[1] < self._settings.board_size:
                if loc == self._highlighted:
                    self._highlighted = None
                else:
                    self._highlighted = loc
                action = self._game.get_robot_actions(self.current_turn()).get(loc)
                if action is not None:
                    self._highlighted_target = action.get("target", None)
                else:
                    self._highlighted_target = None
                self.update_highlight_sprite()
                self.update_title()

        self._master.bind("<Button-1>", lambda e: onclick(e))
        self._master.bind('<Left>', lambda e: prev())
        self._master.bind('<Right>', lambda e: next())
        self._master.bind('<space>', lambda e: pause())

        self.show_arrows = Tkinter.BooleanVar()

        frame = Tkinter.Frame()
        win.create_window(width, height, anchor=Tkinter.SE, window=frame)

        arrows_box = Tkinter.Checkbutton(frame, text="Show Arrows", variable=self.show_arrows, command=self.paint)
        arrows_box.pack()

        self._toggle_button = Tkinter.Button(frame, text=u'\u25B6', command=self.toggle_pause)
        self._toggle_button.pack(side='left')

        prev_button = Tkinter.Button(frame, text='<', command=prev)
        prev_button.pack(side='left')

        next_button = Tkinter.Button(frame, text='>', command=next)
        next_button.pack(side='left')

        restart_button = Tkinter.Button(frame, text='<<', command=restart)
        restart_button.pack(side='left')

        self._time_slider = Tkinter.Scale(frame,
                                          from_=-self._settings.turn_interval/2,
                                          to_=self._settings.turn_interval/2,
                                          orient=Tkinter.HORIZONTAL, borderwidth=0)
        self._time_slider.pack(fill=Tkinter.X)
        self._time_slider.set(0)

    def prepare_backdrop(self, win):
        self._win.create_rectangle(0, 0, self._winsize, self._winsize + self._blocksize, fill='#555', width=0)
        self._win.create_rectangle(0, self._winsize, self._winsize, self._winsize + self._blocksize * 15/4, fill='#333', width=0)
        for x in range(self._settings.board_size):
            for y in range(self._settings.board_size):
                rgb = self._settings.normal_color if "normal" in rg.loc_types((x, y)) else self._settings.obstacle_color
                self.draw_grid_object((x, y), fill=rgb_to_hex(*rgb), layer=1, width=0)

    def draw_grid_object(self, loc, type="square", layer=0, **kargs):
        layer_id = 'layer %d' % layer
        self._layers[layer_id] = None
        tags = kargs.get("tags", [])
        tags.append(layer_id)
        kargs["tags"] = tags
        x, y = self.grid_to_xy(loc)
        rx, ry = self.square_bottom_corner((x, y))
        if type == "square":
            item = self._win.create_rectangle(
                x, y, rx, ry,
                **kargs)
        elif type == "circle":
            item = self._win.create_oval(
                x, y, rx, ry,
                **kargs)
        return item

    def update_layers(self):
        for layer in self._layers:
            self._win.tag_raise(layer)

    def draw_text(self, loc, text, color=None):
        layer_id = 'layer %d' % 9
        self._layers[layer_id] = None
        x, y = self.grid_to_xy(loc)
        item = self._win.create_text(
            x+10, y+10,
            text=text, font='TkFixedFont', fill=color, tags=[layer_id])
        return item

    def draw_line(self, src, dst, offset=(0, 0), layer=0, **kargs):
        layer_id = 'layer %d' % layer
        self._layers[layer_id] = None
        tags = kargs.get("tags", [])
        tags.append(layer_id)
        kargs["tags"] = tags
        ox, oy = offset
        srcx, srcy = self.grid_to_xy(src)
        dstx, dsty = self.grid_to_xy(dst)

        item = self._win.create_line(srcx+ox, srcy+oy, dstx+ox, dsty+oy, **kargs)
        return item

    def current_turn(self):
        return min(self._settings.max_turns-1, self._turn)

    def update_title(self):
        turns = self.current_turn()
        max_turns = self._settings.max_turns
        red = len(self._game.history[0][self._turn - 1])
        green = len(self._game.history[1][self._turn - 1])
        info = ''
        currentAction = ''
        if self._highlighted is not None:
            squareinfo = self.get_square_info(self._highlighted)
            if 'obstacle' in squareinfo:
                info = 'Obstacle'
            elif 'bot' in squareinfo:
                actioninfo = squareinfo[1]
                hp = actioninfo['hp']
                team = actioninfo['player']
                info = '%s Bot: %d HP' % (['Red', 'Green'][team], hp)
                if actioninfo.get('name') is not None:
                    currentAction += 'Current Action: %s' % (actioninfo['name'],)
                    if self._highlighted_target is not None:
                        currentAction += ' to %s' % (self._highlighted_target,)

        lines = [
            'Red: %d | Green: %d | Turn: %d/%d' % (red, green, turns, max_turns),
            'Highlighted: %s; %s' % (self._highlighted, info),
            currentAction
        ]
        self._win.itemconfig(
            self._label, text='\n'.join(lines))

    def get_square_info(self, loc):
        if loc in self._settings.obstacles:
            return ['obstacle']

        all_bots = self._game.get_robot_actions(self.current_turn())
        if loc in all_bots:
            return ['bot', all_bots[loc]]

        return ['normal']

    def update_slider_value(self):
        v = -self._time_slider.get()
        if v > 0:
            v = v * 20
        self.slider_delay = self._settings.turn_interval + v

    def callback(self):
        self.update_slider_value()
        self.tick()
        self._win.after(int(1000.0 / self._settings.FPS), self.callback)

    def tick(self):
        now = millis()
        # check if frame-update
        if not self._paused:
            if now >= self._t_next_frame:
                self.change_turn(1)
                if self._turn >= self._settings.max_turns:
                    self.toggle_pause()
                else:
                    self.update_frame_timing(self._t_next_frame)
        subframe = float((now - self._t_frame_start) % self.slider_delay) / float(self.slider_delay)
        if self.animations:
            self.paint(subframe)
        else:
            self.paint(0)

    def determine_bg_color(self, loc):
        if loc in self._settings.obstacles:
            return rgb_to_hex(*self._settings.obstacle_color)
        return rgb_to_hex(*self._settings.normal_color)

    def draw_background(self):
        # draw squares
        for y in range(self._settings.board_size):
            for x in range(self._settings.board_size):
                loc = (x, y)
                self.draw_grid_object(loc, fill=self.determine_bg_color(loc), layer=1, width=0)
        # draw text labels
        for y in range(self._settings.board_size):
            self.draw_text((y, 0), str(y), '#888')
            self.draw_text((0, y), str(y), '#888')

    def update_sprites_new_turn(self):
        for sprite in self._sprites:
            sprite.clear()
        self._sprites = []

        self.update_highlight_sprite()
        bots_activity = self._game.get_robot_actions(self._turn)
        try:
            for bot_data in bots_activity.values():
                self._sprites.append(RobotSprite(bot_data, self))
        except:
            print bots_activity
            raw_input()

    def update_highlight_sprite(self):
        need_update = self._highlight_sprite is not None and self._highlight_sprite.location != self._highlighted
        if self._highlight_sprite is not None or need_update:
            self._highlight_sprite.clear()
        self._highlight_sprite = HighlightSprite(self._highlighted, self._highlighted_target, self)

    def paint(self, subframe=0):
        for sprite in self._sprites:
            sprite.animate(subframe if not self._paused else 0)
        if self._highlight_sprite is not None:
            self._highlight_sprite.animate(subframe)
        self.update_layers()

    def grid_to_xy(self, loc):
        x, y = loc
        return (x * self._blocksize + 20, y * self._blocksize + 20)

    def square_bottom_corner(self, square_topleft):
        x, y = square_topleft
        return (x + self._blocksize - 3, y + self._blocksize - 3)
