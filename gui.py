import os
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import re
import io 

import sova

from ruamel.yaml import YAML
yaml = YAML()

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
        if type(s) is str:
            f.write(s)
        else:
            import json
            f.write(json.dumps(s, indent=2))

def edit(contents):
    width=30
    height=60
    edit_win = curses.newwin(width, height, 4,1) # TODO determine size from template size
    edit_win.addstr(contents)
    rectangle(stdscr, 3,0, 4+width+1, 1+height+1)
    stdscr.refresh()

    box = Textbox(edit_win)
    box.edit()
    result = box.gather()

    return result

class GUI():
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.model = sova.get_model()

    def paint_model(self):
        self.stdscr.clear()
    
        plot = [p for p in self.model['plots'].values()][0]
        width, height = plot['width'], plot['height']
        window_height, window_width = self.stdscr.getmaxyx()
        self.width_mod = window_width / width
        self.height_mod = window_height / height

        self.stdscr.addstr(1,1,','.join(map(str,[width, height])))
        self.stdscr.box('|','-')
        bed_windows = {}
        for name, bed in self.model['beds'].items():
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
            bed_win.addstr(" " + name)
            bed_win.refresh()
            bed_windows[name] = bed_win

        self.stdscr.refresh()
        self.bed_windows = bed_windows

    def do_action(self, action):
        if action == 'add_bed':
            #TODO have an interactive step at first where cursor determines top-left and
            # moving it determines height_width
            template = sova.get_template('bed')
            bed_str = edit(template)
            bed = self.yaml_load(bed_str)

            commit_params_template = '\n'.join(['what:', 'when:', 'who:', 'how long:'])
            commit_params_str = edit(commit_params_template)
            commit_params = self.yaml_load(commit_params_str)

            self.model['beds'].append(bed)
            try:
                self.paint_model()
            except:
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
        elif c in [curses.KEY_LEFT, ord('h')]:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y, x-1)
        elif c in [curses.KEY_RIGHT, ord('l')]:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y, x+1)
        elif c in [curses.KEY_UP, ord('k')]:
            modifiers.clear()
            y, x = stdscr.getyx()
            stdscr.move(y-1, x)
        elif c in [curses.KEY_DOWN, ord('j')]:
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

        elif c == ord('i'):
            new = True
            beds = gui.model['beds']
            for name, bed_win in gui.bed_windows.items():
                y, x = stdscr.getyx()
                if bed_win.enclose(y, x):
                    new = False
                    bed = beds[name]
                    break

            template = sova.get_template('bed') if new else sova.dump(bed)
            #TODO let template be a dict so you can easily fill in default values and divide keys and values
            new_bed = sova.load(edit(template))

            if new:
                name = new_bed.pop('name')

            beds[name] = new_bed
            try:
                gui.paint_model()
            except:
                beds.remove(new_bed)
                if not new:
                    beds.append(bed)
                gui.paint_model()
            else:
                commit_params_template = '\n'.join(['what: %s bed %s' % ('adding' if new else 'changing', name), 'when:', 'who:', 'how long:'])
                commit_params_str = edit(commit_params_template)
                commit_params = sova.load(commit_params_str)

                sova.save(gui.model, author=AUTHOR, **commit_params)
                gui.paint_model() # to remove artifacts from sova.save

            gui.model['beds']
        pass

        #TODO editing
        #TODO adding planting

        gui.paint(modifiers, action)

def set_shorter_esc_delay_in_os():
    os.environ.setdefault('ESCDELAY', '25')

set_shorter_esc_delay_in_os()
wrapper(main)
