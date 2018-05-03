import os
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import re
import io 

import sova

from ruamel.yaml import YAML

VERSION='0.1'
AUTHOR={'name': 'sova-gui v' + VERSION,
        'email': 'sova-gui@otselo.eu'}

stdscr = curses.initscr()

#def parse(commit_params_string):
#    match = re.search('what: ?(.+)\nwhen: ?(.+)\nwho: ?(.+)\nhow long: ?(.+)', commit_params_string)
#    if not match:
#        raise RuntimeError("Commit params string does not match regex: %s" % commit_params_string)
#
#    return {'what': match.group(1), 'when': match.group(2), 'who': match.group(3), 'how_long': match.group(4)}
#
def log(s):
    with open('log.txt', 'a') as f:
        f.write(s)

class GUI():
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.model = sova.load()

    def paint_model(self):
        self.stdscr.clear()

        plot = self.model['plots'][0]
        width, height = plot['width'], plot['height']
        window_height, window_width = self.stdscr.getmaxyx()
        print(window_height, window_width)
        self.width_mod = window_width / width
        self.height_mod = window_height / height

        self.stdscr.addstr(1,1,','.join(map(str,[width, height])))
        self.stdscr.box('|','-')
        for bed in self.model['beds']:
            width, height = bed['width'], bed['height']
            left, top = bed['left'], bed['top']
            bed_win = self.stdscr.subwin(
                    int(height*self.height_mod), 
                    int(width*self.width_mod), 
                    int(top*self.height_mod), 
                    int(left*self.width_mod))
            x, y = bed_win.getbegyx()
            self.stdscr.addstr(x-1, y, ','.join(map(str,[left, top])))
            bed_win.clear()
            bed_win.box('#','#')
            bed_win.addstr(1,1,','.join(map(str,[width, height])))
            bed_win.addstr(" " + bed['name'])
            bed_win.refresh()

        self.stdscr.refresh()

    def do_action(self, action):
        if action == 'add_bed':
            #TODO have an interactive step at first where cursor determines top-left and
            # moving it determines height_width
            template = sova.help_adding('bed')
            edit_win = curses.newwin(20,80, 4,1) # TODO determine size from template size
            edit_win.addstr(template)
            rectangle(stdscr, 3,0, 4+20+1, 1+80+1)
            stdscr.refresh()

            box = Textbox(edit_win)
            box.edit()
            yaml = YAML()
            bed_str = box.gather()
            for plot in self.model['plots']:
                plot_str = io.StringIO()
                yaml.dump(plot, plot_str)
                bed_str = bed_str.replace('*{name}'.format(**plot), '\n'+sova.indent(4, plot_str.getvalue()))
            bed = yaml.load(bed_str)
            log('Bed:' + str(bed))

            edit_win.clear()
            commit_params_template = '\n'.join(['what:', 'when:', 'who:', 'how long:'])
            edit_win.addstr(commit_params_template)
            box.edit()
            commit_params = yaml.load(box.gather())
            log('Commit params:' + str(commit_params))

            self.model['beds'].append(bed)
            try:
                self.paint_model()
            except:
                log("Updated model did not pass validation. Reverting")
                self.model['beds'].remove(bed)
                self.paint_model()
            else:
                sova.save(self.model, author=AUTHOR, **commit_params)
                self.paint_model() # to remove artifacts from sova.save

    def paint(self, modifiers, action):
        y, x = self.stdscr.getyx()
        if modifiers:
            self.stdscr.addstr(2, 1, ''.join(map(str, modifiers)))
        else:
            self.stdscr.addstr(2, 1, ' '*10)

        if action:
            self.do_action(action)

        self.stdscr.move(y, x)

def main(stdscr):
    gui = GUI(stdscr)
    gui.paint_model()

    modifiers = list()
    while True:
        action = None
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
            if 'a' in modifiers:
                action = 'add_bed'
            else:
                modifiers.append('b')

        #TODO editing bed 
        #TODO adding planting

        gui.paint(modifiers, action)

def set_shorter_esc_delay_in_os():
    os.environ.setdefault('ESCDELAY', '25')

set_shorter_esc_delay_in_os()
wrapper(main)
