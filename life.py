import argparse
import curses
from curses.textpad import rectangle
import numpy as np
from numpy.lib.stride_tricks import as_strided
from PIL import Image
import time
import traceback



def clamp(num, min_value, max_value):
    """helper function to clamp an int between min and max values"""
    return max(min(num, max_value), min_value)

def handleDirectional(event, coord, min_x, max_x, min_y, max_y, step):
    """helper function to handle directional input"""
    if event == ord("w") and (coord[0] - step) >= min_y: coord[0] -= step # Todo: use clamp() for this
    if event == ord("s") and (coord[0] + step) <= max_y: coord[0] += step
    if event == ord("a") and (coord[1] - step) >= min_x: coord[1] -= step
    if event == ord("d") and (coord[1] + step) <= max_x: coord[1] += step
    return coord

def rowString(r):
    """helper function to convert a row [] into a string"""
    s = ''
    for c in r:
        if c: s += "O"
        else: s += " "
    return s



class Life:
    """Game engine for Conway's Game of Life"""
    def __init__(self, args):
        self.args = args
        self.images = []

    def curses_interface(self):
        """function to run the game in a terminal window using curses"""
        screen = curses.initscr() #set new terminal settings
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        screen.nodelay(1)
        screen.keypad(1)
        try:
            h, w = screen.getmaxyx() # Get screen size and do math to determine subwindow dimensions
            maxg_w = w - 10
            maxg_h = h - 10 # Max size of the game window
            mid_w = int(w/2)
            mid_h = int(h/2)
            banner_window = curses.newwin(10, w, 0, 0)
            b_h, b_w = banner_window.getmaxyx()
            if self.args.dimensions:
                p_w, p_h = self.args.dimensions
                g_w = clamp(p_w + 2, 0, maxg_w) # Make a game window the same size as the array, or the max size
                g_h = clamp(p_h + 2, 0, maxg_h) # Add 2 because of the box
                top_l = (mid_w-int(g_w/2), mid_h-int(g_h/2))
                game_window = curses.newwin(g_h, g_w, top_l[0], top_l[1])
            else:
                top_l = (mid_w-int(maxg_w/2), mid_h-int(maxg_h/2)) # If no dimensions are supplied, default to max size
                game_window = curses.newwin(maxg_h, maxg_w, top_l[0], top_l[1])
                p_h, p_w = game_window.getmaxyx() # Default plane dim to the size of the game window
                p_w -= 2 # To account for the box
                p_h -= 2
            if self.args.load:
                plane = self.load(self.args.load) # We can specify a save file to load at start
            else:
                plane = np.random.randint(0, 2, (p_h, p_w), dtype=bool) # Initializing with random noise
            game_running = False
            ms = 100 # Time to wait between updates
            exec_time = None
            recording = False
            # Main loop
            while True:
                events = self.get_events(screen, ms) #get event queue
                if ord("q") in events:
                    if len(self.images) > 0: self.output_gif()
                    break
                if ord("r") in events: game_running = True
                if ord("p") in events: game_running = False
                if ord("g") in events: ms = clamp(ms-10, 30, 5000)
                if ord("h") in events: ms = clamp(ms+10, 30, 5000)
                if ord("n") in events: plane = np.random.randint(0, 2, (p_h, p_w), dtype=bool)
                if ord("v") in events: recording = True
                if game_running:
                    exec_time, plane = self.game_update(plane)
                if (recording and game_running):
                    self.save_frame(plane)
                # Draw the main menu banner
                banner_window.addstr(0, 0, "Conway's Game of Life, Presented by Jacob Smith")
                banner_window.addstr(0, int(w/2), "Main Menu")
                if (recording and game_running):
                    banner_window.addstr(1, int(w/2), "Recording, Frames: " + str(len(self.images)))
                banner_window.addstr(2, 0, "Game Dimensions: " + str(p_h) + ',' + str(p_w))
                if exec_time: banner_window.addstr(1, 0, "Update function execution time: " + str(exec_time))
                banner_window.addstr(3, 0, "Press e to enter edit mode, press r to start the game, p to pause, q to quit.")
                banner_window.refresh()

                self.draw_game(game_window, plane)

            screen.nodelay(0) #reset terminal settings
            screen.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.curs_set(1)
            curses.endwin()

        except Exception as e:
            screen.nodelay(0) #reset terminal settings
            screen.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.curs_set(1)
            curses.endwin()
            print(e)
            print(traceback.format_exc())


    def get_events(self, screen, time_window):
        """loop for time_window milliseconds and collect keypress events from the screen into a list using getch"""
        start_time = time.time()*1000
        elapsed_time = 0
        events = []
        while time_window > elapsed_time:
            new_event = screen.getch()
            events.append(new_event)
            current_time = time.time()*1000
            elapsed_time = current_time - start_time
        curses.flushinp() #clear the buffer
        return events

    def game_update(self, plane):
        """update the game"""
        tic = time.perf_counter_ns()
        # mimic a toroidal surface by padding with opposite edges
        pad_me = np.pad(plane, pad_width=1, mode='wrap')
        next_plane = np.zeros(plane.shape, dtype=bool)
        # as_strided returns (3x3) new views for each cell
        # unlike splitting, as_strided does not copy
        neighborhoods = as_strided(pad_me,
                                   shape=(plane.shape[0],plane.shape[1],3,3),
                                   strides=pad_me.strides+pad_me.strides)
        for i, row in enumerate(plane):
            for j, cel in enumerate(row):
                n = np.count_nonzero(neighborhoods[i][j] == True) - 1
                if not cel and n == 2: next_plane[i][j] = True
                elif cel and n < 2: next_plane[i][j] = False
                elif cel and n > 3: next_plane[i][j] = False
                elif cel and (n == 2 or n == 3): next_plane[i][j] = True

        toc = time.perf_counter_ns()
        return (toc - tic), next_plane

    def draw_game(self, game_window, plane):
        """convert rows in the array into strings and display them in the game_window"""
        game_window.clear()
        game_window.box()
        max_h, max_w = game_window.getmaxyx()
        max_h -= 2
        max_w -= 2 # Edge of the screen is bordered by a 1px box
        h, w = plane.shape
        offset_h = int(h/2) - int(max_h/2) # Offset to center the view_mask
        offset_w = int(w/2) - int(max_w/2)
        # If the array is larger than our game window, only display a smaller slice.
        view_mask = plane[offset_h:max_h+offset_h, offset_w:max_w + offset_w]
        for i, row in enumerate(view_mask):
            game_window.addstr(1 + i, 1, rowString(row))
        game_window.refresh()

    def save(self, screen, plane):
        """function to save the current array using numpy"""

        screen.nodelay(0) # set new terminal settings
        curses.echo()

        screen.clear()
        screen.addstr(1, 0, "Save as: ")
        input = str(screen.getstr(1, 10), encoding='utf-8')
        with open(input, 'wb') as f:
            np.save(f, plane)
        screen.clear()
        screen.addstr(1, 0, "Saved pattern as: " + input)
        screen.refresh()
        curses.napms(1000)
        screen.clear()

        screen.nodelay(1) # reset terminal settings
        curses.noecho()

    def load(self, screen, filename=None):
        """function to load a saved array using numpy"""

        plane = np.zeros((p_h-2, p_w-2), dtype=bool) # Initializing with an empty plane
        if not filename: # enter submenu for user to specify a filename
            screen.nodelay(0) # set new terminal settings
            curses.echo()

            screen.clear()
            screen.addstr(1, 0, "Load file: ")
            filename = str(screen.getstr(1, 11), encoding='utf-8')
            screen.clear()
            screen.refresh()

            screen.nodelay(1) # reset terminal settings
            curses.noecho()

        new_arr = None
        try:
            new_arr = np.load(filename)
            screen.addstr(1, 0, "File loaded.")
        except Exception as e:
            screen.addstr(1, 0, "Error loading file." + str(e))

        if new_arr.any():
            plane = np.copy(new_arr)

        return plane

    def save_frame(self, plane):
        """record a frame"""
        im = Image.fromarray(plane*np.uint8(255))
        self.images.append(im)

    def output_gif(self):
        """save a gif"""
        self.images[0].save("output.gif", save_all=True, append_images=self.images[1:])



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: life.py -l duck_big #start the game with the example pattern duck_big")
    parser.add_argument('-c', '--curses', action='store_true', help='Run the curses interface.')
    parser.add_argument('-l', '--load', help='Load a pattern.')
    parser.add_argument('-d', '--dimensions', nargs='+', type=int, help='Run a game with the given dimensions, if no starting pattern is loaded it will default to starting with random noise.')
    args = parser.parse_args()

    lf = Life(args)


    if args.curses: lf.curses_interface()
