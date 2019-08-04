#!/usr/bin/env python3

import pygame
import os
from tkinter import *
from tkinter.messagebox import askyesno, showinfo

PREFS = 'preferences.txt'

INFO = """
Version: 1.2
Release: 02.02.2018
Changes:
    - menu was added;
    - now you can change volume level;
    - now you can choose melody.
Author: McPig
"""

USAGE = """
1. Decide on the task to be done.
2. Set the pomodoro timer (traditionally to 25 minutes).
3. Work on the task until the timer rings. 
4. Take a short break (3–5 minutes), then go to step 2.
5. After four pomodoros, take a longer break (15–30 minutes), then go to step 1.
"""


class Timer(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)

        # root settings
        self.master.title('Pomodoro Timer')
        self.master.iconbitmap('tomato.ico')
        self.master.protocol('WM_DELETE_WINDOW', self.quitter)

        # scale variables
        self.pomodoro_var = IntVar(value=25)
        self.shortbrk_var = IntVar(value=5)
        self.longbrk_var = IntVar(value=30)

        # volume and sound variables
        self.volume_var = IntVar(value=self.get_volume_value())
        self.sound_var = StringVar(value=self.get_sound_name())

        # last values
        self.last_value = (self.pomodoro_var.get(), 0)  # used in reset_timer method
        self.last_mode = 'pomodoro'
        self.pomodoro_counter = 0


        self.font = ('Source Sans Pro', 9, 'normal')
        self.after_id = None  # id of the "after" thread
        self.running = False  # state of the timer

        # menu bar
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        options = Menu(menubar, tearoff=False)
        # volume submenu
        volume = Menu(options, tearoff=False)
        for i in range(11):
            volume.add_radiobutton(label=str(i), value=i, variable=self.volume_var, command=self.set_volume_value)
        options.add_cascade(label="Volume", menu=volume)
        # sounds submenu
        fnames = [os.path.splitext(filename)[0] for filename in os.listdir(r'sounds')]
        sounds = Menu(options, tearoff=False)
        for fname in fnames:
            sounds.add_radiobutton(label=fname, value=fname, variable=self.sound_var, command=self.set_sound_name)
        options.add_cascade(label="Melody", menu=sounds)
        menubar.add_cascade(label="Settings", menu=options)

        info = Menu(menubar, tearoff=False)
        info.add_command(label="Usage", command=lambda: showinfo("Pomodoro", USAGE))
        info.add_separator()
        info.add_command(label="About", command=lambda: showinfo("Pomodoro", INFO))
        menubar.add_cascade(label="Help", menu=info)

        # widget for timer
        label = Label(self, text='{:02}:{:02}'.format(self.pomodoro_var.get(), 0))
        label.config(font=('Source Sans Pro', 110, 'bold'))
        label.grid(row=0, column=0, columnspan=5, sticky=NSEW)
        self.timer = label

        # pomodoro widgets
        pomodoro_bttn = Button(self, text='Pomodoro', width=16, bg='firebrick1', font=self.font)
        pomodoro_bttn.config(command=lambda: self.start_timer('pomodoro', self.pomodoro_var.get() * 60))
        pomodoro_bttn.grid(row=1, column=0, sticky=NSEW)
        pomodoro_scale = Scale(self, from_=10, to=60, orient='horizontal', variable=self.pomodoro_var)
        pomodoro_scale.grid(row=2, column=0, sticky=NSEW)

        # shortbreak widgets
        shortbrk_bttn = Button(self, text='Short break', width=16, bg='yellow', font=self.font)
        shortbrk_bttn.config(command=lambda: self.start_timer('short', self.shortbrk_var.get() * 60))
        shortbrk_bttn.grid(row=1, column=1, sticky=NSEW)
        shortbrk_scale = Scale(self, from_=3, to=5, orient='horizontal', variable=self.shortbrk_var)
        shortbrk_scale.grid(row=2, column=1, sticky=NSEW)

        # longbreak widgets
        longbrk_bttn = Button(self, text='Long break', width=16, bg='light green', font=self.font)
        longbrk_bttn.config(command=lambda: self.start_timer('long', self.longbrk_var.get() * 60))
        longbrk_bttn.grid(row=1, column=2, sticky=NSEW)
        longbrk_scale = Scale(self, from_=10, to=30, orient='horizontal', variable=self.longbrk_var)
        longbrk_scale.grid(row=2, column=2, sticky=NSEW)

        # start/stop button
        strt_stp_bttn = Button(self, text="Start", command=self.reset_timer)
        strt_stp_bttn.config(width=16, font=self.font)
        strt_stp_bttn.grid(row=1, column=3, columnspan=3, sticky=NSEW)
        self.strt_stp_bttn = strt_stp_bttn

        # pomodoro counter widgets
        dec_bttn = Button(self, text='-', command=self.dec_pomodoro_counter, relief=FLAT)
        dec_bttn.grid(row=2, column=3)
        pomodoro_label = Label(self, text='Pomodoros: %s' % self.pomodoro_counter, font=self.font)
        pomodoro_label.grid(row=2, column=4, sticky=NSEW)
        self.pomodoro_label = pomodoro_label
        inc_bttn = Button(self, text='+', command=self.inc_pomodoro_counter, relief=FLAT)
        inc_bttn.grid(row=2, column=5)

        for row in range(3):
            self.rowconfigure(row, weight=1)
        for col in range(6):
            self.columnconfigure(col, weight=1)

        # pygame mixer initialization
        pygame.init()
        pygame.mixer.init()

    def format_time(self, secs):
        m = secs // 60
        s = secs % 60
        return m, s

    def start_timer(self, mode, secs):
        try:
            self.after_cancel(self.after_id)
        except IndexError:
            pass
        self.running = True
        self.strt_stp_bttn.config(text="Stop")
        m, s = self.format_time(secs)
        self.last_value = (m, s)
        self.last_mode = mode
        fts = '{:02}:{:02}'.format(m, s)
        self.timer.config(text=fts)
        if m == 0 and s == 0:
            if mode == 'pomodoro':
                self.inc_pomodoro_counter()
            self.running = False
            self.playsound(os.path.join('sounds', self.sound_var.get()) + '.wav')
        else:
            self.after_id = self.after(1000, self.start_timer, mode, secs-1)

    def inc_pomodoro_counter(self):
        self.pomodoro_counter += 1
        self.pomodoro_label.config(text='Pomodoros: %s' % self.pomodoro_counter)

    def dec_pomodoro_counter(self):
        if self.pomodoro_counter > 0:
            self.pomodoro_counter -= 1
            self.pomodoro_label.config(text='Pomodoros: %s' % self.pomodoro_counter)

    def reset_timer(self):
        if self.running:
            self.running = False
            self.strt_stp_bttn.config(text="Start")
            self.after_cancel(self.after_id)
        else:
            m, s = self.last_value
            if not (m, s) == (0, 0):
                secs = m * 60 + s
                self.start_timer(self.last_mode, secs)

    def quitter(self):
        if askyesno('Pomodoro', 'Are you sure you want to quit?'):
            self.quit()

    def playsound(self, filename):
        pygame.mixer.music.set_volume(self.volume_var.get() / 10)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

    def get_volume_value(self):
        file = open(PREFS)
        lines = file.readlines()
        file.close()
        volume_value = int(lines[0].split(': ')[1][:-1])
        return volume_value

    def set_volume_value(self):
        file = open(PREFS)
        lines = file.readlines()
        file.close()
        del lines[0]  # delete line with volume information
        lines.insert(0, 'Volume: ' + str(self.volume_var.get()) + '\n')
        file = open(PREFS, 'w')
        file.writelines(lines)
        file.close()

    def get_sound_name(self):
        file = open(PREFS)
        lines = file.readlines()
        file.close()
        sound_name = lines[1].split(': ')[1][:-1]
        return sound_name

    def set_sound_name(self):
        file = open(PREFS)
        lines = file.readlines()
        file.close()
        del lines[1]  # delete line with sound information
        lines.insert(1, 'Sound: ' + self.sound_var.get() + '\n')
        file = open(PREFS, 'w')
        file.writelines(lines)
        file.close()
        self.playsound(os.path.join('sounds', self.sound_var.get()) + '.wav')

if __name__ == '__main__':
    root = Tk()
    timer = Timer(root)
    mainloop()
