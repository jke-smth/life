import argparse
import curses
from curses.textpad import rectangle
import numpy as np


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
        ms = 100
        while True:
            event = self.screen.getch()
            curses.flushinp()
            if event == ord("q"): break
            if event == ord("e"): self.edit_mode()
            if event == ord("r"): game_tick = True
            if event == ord("p"): game_tick = False
            if event == ord("g"): ms = clamp(ms-10, 30, 5000)
            if event == ord("h"): ms = clamp(ms+10, 30, 5000)
            if game_tick: self.game_update()

            self.screen.addstr(0, 0, "Conway's Game of Life, Presented by Jacob Smith")
            self.screen.addstr(2, 0, "Press e to enter edit mode, press r to start the game, p to pause, q to quit.")
            self.draw_game()
            curses.napms(ms)

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
        while True:
            event = self.screen.getch()
            curses.flushinp()
            if event == ord("q"): break
            if event in [ord("w"), ord("s"), ord("a"), ord("d")]: self.handle_directional(event, self.edit_pos, 0, w, 0, h, 1)
            if event == ord("z"): self.plane[self.edit_pos[0]][self.edit_pos[1]] = True
            if event == ord("x"): self.plane[self.edit_pos[0]][self.edit_pos[1]] = False
            if event == ord("f"): self.plane.fill(True)
            if event == ord("c"): self.plane.fill(False)
            if event == ord("n"): self.plane = np.random.randint(0, 2, (h, w))
            if event == ord("o"): self.save()
            if event == ord("l"): self.load()
            self.draw_game()
            curses.napms(50)
            self.game_window.addstr(self.edit_pos[0] + 1,self.edit_pos[1] + 1, "▉")
            self.game_window.refresh()
            curses.napms(50)
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
        curses.napms(1000)
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
        epilog="Example: life.py")
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
