Conway's Game of Life as presented by Jacob Smith

This is a proof of concept code demonstrating Conway's Game of Life.
The game rules are as follows:
1. Any live cell with fewer than two live neighbors dies, as if by underpopulation.
2. Any live cell with two or three live neighbors lives on to the next generation.
3. Any live cell with more than three live neighbors dies, as if by overpopulation.
4. Any dead cell with exactly three live neighbors becomes a live cell, as if by reproduction.

This implementation of Conway's Game takes place on a 2-dimensional boolean array.
The game's rules are applied for every cell by iterating through the entire array
and taking a 3x3 slice around each cell and counting the number of live cells in
the slice. Then a series of if/then statements set the state of each cell to either
True or False. The slice is clamped to the edges of the array, unlike other versions
of the game where the edges wrap around. This results in unique behavior of cells
close to the edge "walls".

The interface uses the Python Curses library to display the array as rows and
columns of text within a terminal screen. There is a rudimentary menu that allows
running and pausing of the game, as well as accessing a submenu for editing. From
the editing menu you can draw and delete cells using a displayed cursor. There is
also a function for filling the entire screen with a random distribution of cells,
as well as submenus for saving and loading of patterns. I have included some
example patterns.

This first version is very limited, and I intend to continuously improve it.

Some future fixes and improvements that I am planning:

1. Displaying the array as text within a terminal window limits the possible
   size of the game. Though it is possible to load arrays that are larger than
   the terminal window, you will only be able to see a small section that fits
   within the subwindow. I considered developing functions for moving the display,
   however I would still be limited by font sizes. Therefore my next goal for this
   program is to output the display as a pixel array in a format that is viewable
   in a video player. This would still limit the size of the array to the number
   of pixels on your screen. I would like to provide a function to output a
   video stream.

2. The current implementation of the rules is not efficient, I am working on a
   better way to apply the rules using Numpy. Ideally we would not be iterating
   over the array but rather performing an efficient function that makes better
   use of Numpy array transformation algorithms. This would increase the possible
   size of the array considerably and reduce the time it takes to calculate each
   frame. This will be done concurrently with the first changes as I anticipate
   the larger array sizes made possible through pixel arrays will start to impact
   performance.
