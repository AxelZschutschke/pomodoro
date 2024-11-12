import argparse
import time
import curses
import pyfiglet
import signal
import sys
import datetime

class CursesApp:
    def __init__(self, task, logfile, font="slant"):
        self.stdscr = None
        self.task = task
        self.logfile = logfile
        self.font = font

    def enter(self, stdscr):
        self.stdscr = stdscr
        signal.signal(signal.SIGWINCH, self.handleResize)
        signal.signal(signal.SIGINT, self.handleSignal)
        self.run()

    def run(self):
        pass

    def log(self, event):
        global args

        with open(self.logfile, "a") as f:
            date = datetime.datetime.utcnow().strftime("%a;%Y:%m:%d;%H:%M")
            f.write(f"{date};{self.task};{event}\n")

    def handleResize(self, *args, **kwargs):
        del args
        del kwargs

        curses.endwin()  # This could lead to crashes according to below comment
        self.stdscr.refresh()

    def handleSignal(self, *args, **kwargs):
        del args
        del kwargs

        self.log("aborted")
        sys.exit(0)


    def center(self, text, banner=False, padding_v_percent = 50 ):
        if banner:
            text = self.getAsciiStr(text)
        lines = text.split("\n")
        maxWidth = max([len(l) for l in lines])
        padding_h = int((curses.COLS - maxWidth)/2)
        padding_v = int((curses.LINES - len(lines))*padding_v_percent/100) 

        for i, l in enumerate(lines):
            self.stdscr.addstr(padding_v + i, padding_h, l)

    def getAsciiStr(self, string):
        return pyfiglet.figlet_format(string, font=self.font)


class Pomodoro(CursesApp):
    def __init__(self, interval, task, logfile):
        super().__init__(task, logfile)
        self.interval = interval
        self.start = int(time.time())
        self.end = self.start + int(self.interval * 60)
        self.left = 1
        self.running = False

    def tick(self):
        now = time.time()
        self.left = int(self.end - now)
        return self.left > 0

    def formatTime(self):
        left_m = int(self.left / 60)
        left_s = self.left - (left_m * 60)
        return f"{left_m} : {left_s:02d}"

    def setColorsRunning(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
        self.stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.clear()

    def setColorsFinished(self):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_GREEN)
        self.stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.clear()

    def run(self):
        self.log("start")
        self.stdscr.nodelay(True)

        while self.tick():
            key = self.stdscr.getch() 
            if key == curses.KEY_RESIZE:
                curses.resizeterm(*self.stdscr.getmaxyx())

            self.setColorsRunning()
            self.center(args.task, padding_v_percent=25)
            self.center(self.formatTime(), banner=True, padding_v_percent=60)
            self.stdscr.refresh()
            time.sleep(0.25)

        self.stdscr.nodelay(False)
        self.setColorsFinished()
        self.center("end", banner=True, padding_v_percent=50)
        self.stdscr.getkey()

        self.log("end")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser("pomodoro")
    parser.add_argument("-interval", default="15", help="interval minutes [default=15]")
    parser.add_argument("-task", default="concentrate", help="title for this pomodoro")
    parser.add_argument("-log", default="pomodoro.csv", help="output file")

    args = parser.parse_args()

    interval = float(args.interval)
    task = args.task
    logfile = args.log
    app = Pomodoro(interval, task, logfile)
    curses.wrapper(app.enter)
