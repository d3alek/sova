import os
import curses

import garden

stdscr = curses.initscr()

from curses import wrapper

def paint_model(stdscr, model):
    stdscr.clear()

    plot = model['plots'][0]
    width, height = plot['width'], plot['height']
    window_height, window_width = stdscr.getmaxyx()
    width_mod = window_width / width
    height_mod = window_height / height

    stdscr.addstr(1,1,','.join(map(str,[width, height])))
    stdscr.box('|','-')
    for bed in model['beds']:
        width, height = bed['width'], bed['height']
        left, top = bed['left'], bed['top']
        bed_win = stdscr.subwin(
                int(height*height_mod), 
                int(width*width_mod), 
                int(top*height_mod), 
                int(left*width_mod))
        x, y = bed_win.getbegyx()
        stdscr.addstr(x-1, y, ','.join(map(str,[left, top])))
        bed_win.clear()
        bed_win.box('#','#')
        bed_win.addstr(1,1,','.join(map(str,[width, height])))
        bed_win.addstr(" " + bed['name'])
        bed_win.refresh()

    stdscr.refresh()

def paint(stdscr, modifiers):
    y, x = stdscr.getyx()
    if modifiers:
        stdscr.addstr(2, 1, ''.join(map(str, modifiers)))
    else:
        stdscr.addstr(2, 1, ' '*10)

    stdscr.move(y, x)

def main(stdscr):
    model = garden.load()
    paint_model(stdscr, model)
    modifiers = list()
    while True:
        c = stdscr.getch()
        if c == ord('q'):
            return
        if c == 27: # ALT, assume ESC
            stdscr.nodelay(True)
            c = stdscr.getch()
            modifiers.clear()
            stdscr.nodelay(False)
        elif c == curses.KEY_LEFT:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y, x-1)
        elif c == curses.KEY_RIGHT:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y, x+1)
        elif c == curses.KEY_UP:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y-1, x)
        elif c == curses.KEY_DOWN:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y+1, x)
        elif c == ord('a'):
            modifiers.append('a')

        elif c == ord('b'):
            #TODO adding bed
            pass

        #TODO moving bed 
        #TODO adding planting

        paint(stdscr, modifiers)

def set_shorter_esc_delay_in_os():
    os.environ.setdefault('ESCDELAY', '25')

set_shorter_esc_delay_in_os()
wrapper(main)
