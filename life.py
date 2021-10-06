import argparse
import curses
from curses.textpad import rectangle
import numpy as np
import time

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

def rowString(r):
    s = ''
    for c in r:
        if c: s += "O"
        else: s += " "
    return s

class Life:

    def __init__(self, args, screen):
        self.args = args
        self.screen = screen
        h, w = screen.getmaxyx()
        g_w = w - 10
        g_h = h - 10
        mid_w = int(w/2)
        mid_h = int(h/2)
        top_l = (mid_w-int(g_w/2), mid_h-int(g_h/2))
        self.game_window = curses.newwin(g_h, g_w, top_l[0], top_l[1])
        p_h, p_w = self.game_window.getmaxyx()
        self.plane = np.zeros((p_h-2, p_w-2), dtype=bool)
        self.edit_pos = None

    def run(self):

        game_tick = False
        ms = 100 #time to wait between updates
        while True:
            events = self.get_events(ms) #get event queue
            if ord("q") in events: break
            if ord("e") in events: self.edit_mode()
            if ord("r") in events: game_tick = True
            if ord("p") in events: game_tick = False
            if ord("g") in events: ms = clamp(ms-10, 30, 5000)
            if ord("h") in events: ms = clamp(ms+10, 30, 5000)
            if game_tick: self.game_update()

            self.screen.addstr(0, 0, "Conway's Game of Life, Presented by Jacob Smith")
            self.screen.addstr(2, 0, "Press e to enter edit mode, press r to start the game, p to pause, q to quit.")
            self.draw_game()
            #curses.napms(ms)

    def get_events(self, time_window):
        """loop for time_window time and collect events"""
        start_time = time.time()*1000
        elapsed_time = 0
        events = []
        while time_window > elapsed_time:
            new_event = self.screen.getch()
            events.append(new_event)
            current_time = time.time()*1000
            elapsed_time = current_time - start_time
        curses.flushinp() #clear the buffer
        return events

    def game_update(self):
        max_h = self.plane.shape[0]
        max_w = self.plane.shape[1]
        next_plane = np.copy(self.plane)
        for i, row in enumerate(self.plane):
            for j, item in enumerate(row):
                test = self.plane[clamp(i-1, 0, max_h):clamp(i+2, 0, max_h),
                                  clamp(j-1, 0, max_w):clamp(j+2, 0, max_w)]
                n = np.count_nonzero(test == True) - 1
                if not item and n == 2: next_plane[i][j] = True
                elif item and n < 2: next_plane[i][j] = False
                elif item and n > 3: next_plane[i][j] = False
                elif item and not (n == 2 or n == 3): next_plane[i][j] = False
        self.plane = np.copy(next_plane)

    def draw_game(self):
        mask_y, mask_x = self.game_window.getmaxyx()
        self.game_window.clear()
        self.game_window.box()
        view_mask = self.plane[0:mask_y-2, 0:mask_x-2]
        for i, row in enumerate(view_mask):
            self.game_window.addstr(1 + i, 1, rowString(row))
        self.game_window.refresh()

    def edit_mode(self):
        h, w = self.plane.shape
        if not self.edit_pos: self.edit_pos = [int(h/2),int(w/2)]
        ms = 50
        while True:
            events = self.get_events(ms)
            curses.flushinp()
            if ord("q") in events: break
            for dir in [ord("w"), ord("s"), ord("a"), ord("d")]:
                if dir in events: self.handle_directional(dir, self.edit_pos, 0, w -1, 0, h -1, 1) #not sure why the need to -1
            if ord("z") in events: self.plane[self.edit_pos[0]][self.edit_pos[1]] = True
            if ord("x") in events: self.plane[self.edit_pos[0]][self.edit_pos[1]] = False
            if ord("f") in events: self.plane.fill(True)
            if ord("c") in events: self.plane.fill(False)
            if ord("n") in events: self.plane = np.random.randint(0, 2, (h, w))
            if ord("o") in events: self.save()
            if ord("l") in events: self.load()
            self.draw_game()
            curses.napms(50)
            self.game_window.addstr(self.edit_pos[0] + 1,self.edit_pos[1] + 1, "▉")
            self.game_window.refresh()
            self.screen.addstr(0, 0, "Conway's Game of Life, Presented by Jacob Smith")
            self.screen.addstr(1, 0, "Edit Mode.")
            self.screen.addstr(2, 0, "Move with w s a d keys, press z to create a cell, x to clear a cell, f to fill all and c to clear all.")
            self.screen.addstr(3, 0, "Press o to output the current cell pattern to a file, l to load a saved pattern, and q to exit.")
            self.screen.addstr(4, 0, "Press n to fill the screen randomly.")
            self.screen.refresh()
        self.screen.clear()

    def save(self):
        self.screen.nodelay(0)
        curses.echo()
        self.screen.clear()
        self.screen.addstr(1, 0, "Save as: ")
        input = str(self.screen.getstr(1, 10), encoding='utf-8')
        with open(input, 'wb') as f:
            np.save(f, self.plane)
        self.screen.clear()
        self.screen.addstr(1, 0, "Saved pattern as: " + input)
        self.screen.refresh()
        curses.napms(3000)
        self.screen.clear()
        self.screen.nodelay(1)
        curses.noecho()

    def load(self):
        self.screen.nodelay(0)
        curses.echo()
        self.screen.clear()
        self.screen.addstr(1, 0, "Load file: ")
        input = str(self.screen.getstr(1, 11), encoding='utf-8')
        self.screen.clear()
        self.screen.refresh()
        try:
            new_plane = np.load(input)
            self.screen.addstr(1, 0, "File loaded.")
        except Exception as e:
            self.screen.addstr(1, 0, "Error" + str(e))
        self.plane = np.copy(new_plane)
        self.screen.nodelay(1)
        curses.noecho()

    def handle_directional(self, event, coord, min_x, max_x, min_y, max_y, step):
        if event == ord("w") and (coord[0] - step) >= min_y: coord[0] -= step
        if event == ord("s") and (coord[0] + step) <= max_y: coord[0] += step
        if event == ord("a") and (coord[1] - step) >= min_x: coord[1] -= step
        if event == ord("d") and (coord[1] + step) <= max_x: coord[1] += step
        return coord

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: life.py -s (10,10) #start the game with a 10x10 playing field")
    parser.add_argument('-l', '--load', help='Load a pattern.')
    args = parser.parse_args()

    try:
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        screen.nodelay(1)
        screen.keypad(1)

        lf = Life(args, screen)
        lf.run()

        screen.nodelay(0)
        screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()

    except Exception as e:
        screen.nodelay(0)
        screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()
        print(e)
