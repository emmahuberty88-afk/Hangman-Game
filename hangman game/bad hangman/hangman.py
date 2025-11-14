#!/usr/bin/env python3
"""
Hangman (Tkinter) - Python rewrite of the canvas-based Hangman game.

Features:
- 500x500 canvas with a Start button centered at the top.
- Loads random words from 'random_common_words_20000.txt' (one-per-line) in the project folder.
- Draws gallows (base, post, beam, rope) and a full stick-figure hangman at start.
- Displays underscores for each letter; correct letters appear in green above the underscores.
- Wrong letters appear in red in a "graveyard" to the left of the gallows.
- On each wrong guess an appendage disappears in this order: left leg, right leg, left arm, right arm, body, head.
- If the hangman fully disappears the player loses: a red "You Lose!" message appears and the correct word is revealed in red below.
- On win the letters turn lighter green and a confetti animation plays for a few seconds.

Run: python3 hangman.py

This file is standalone and uses only the Python standard library (tkinter).
"""

import random
import sys
import os
import math
import traceback
import tkinter as tk
from tkinter import messagebox

# ----- Configuration -----
CANVAS_W = 500
CANVAS_H = 500
WORDS_FILE = 'random_common_words_20000.txt'

# Colors
COLOR_GALLOWS = '#444444'
COLOR_HANGMAN = '#111111'
COLOR_UNDERSCORE = '#222222'
COLOR_CORRECT = '#10B981'  # green
COLOR_CORRECT_LIGHT = '#6EE7B7'
COLOR_WRONG = '#EF4444'    # red

# The order in which parts will be removed on wrong guesses (first removed = left leg)
PARTS_ORDER = ['left_leg', 'right_leg', 'left_arm', 'right_arm', 'body', 'head']


class HangmanGame:
    """Main game class managing state, drawing and input."""

    def __init__(self, root):
        self.root = root
        self.root.title('Hangman')
        # Top Start button (centered)
        # Use a small wrapper so we can catch and report any startup errors and
        # ensure the canvas gets keyboard focus when a round starts.
        self.start_btn = tk.Button(root, text='Start', command=self._on_start_button, bg='#2b6cb0', fg='white', padx=12, pady=6)
        self.start_btn.pack(pady=12)

        # Canvas for 500x500 game area
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg='white', highlightthickness=1, highlightbackground='#e2e8f0')
        self.canvas.pack()
        # allow clicking the canvas to focus it (so keyboard input will be received)
        self.canvas.bind('<Button-1>', lambda e: self.canvas.focus_set())

        # Load words from the provided file (fallback to small default list)
        self.words = self.load_words(WORDS_FILE)
        print(f'Loaded {len(self.words)} words (sample: {self.words[0] if self.words else "<none>"})')

        # Game state
        self.current_word = ''
        self.revealed = []  # booleans per letter
        self.wrong_letters = []
        # parts_present maps part name to boolean (True = visible)
        self.parts_present = {p: True for p in PARTS_ORDER}
        self.game_active = False

        # confetti particles (on win)
        self.confetti = []
        self.confetti_job = None

        # keyboard binding
        root.bind('<Key>', self.on_key)

        # initial render
        self.render()

    # ----------------- Word loading -----------------
    def load_words(self, path):
        """Load words from the given path. Returns a list of words.

        If the file is missing or empty, returns a small fallback list.
        """
        try:
            base = os.path.dirname(__file__)
        except NameError:
            base = os.getcwd()
        p = os.path.join(base, path)
        if not os.path.exists(p):
            print(f"Warning: {path} not found — using fallback word list.")
            return ['python', 'hangman', 'canvas', 'example', 'testing']

        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return ['python', 'hangman', 'canvas', 'example', 'testing']
        return lines

    # ----------------- Game flow -----------------
    def start_round(self):
        """Begin a new round: pick a random word and reset state."""
        # pick and log the chosen word (diagnostics)
        self.current_word = random.choice(self.words).strip()
        print(f'Picked raw word: "{self.current_word}"')
        # guard: ensure word is alphabetical; if not pick again a few times
        attempts = 0
        while attempts < 10 and not self.current_word.isalpha():
            self.current_word = random.choice(self.words).strip()
            attempts += 1

        # normalize
        self.current_word = self.current_word.lower()
        self.revealed = [False] * len(self.current_word)
        self.wrong_letters = []
        self.parts_present = {p: True for p in PARTS_ORDER}
        self.game_active = True
        self.stop_confetti()
        # ensure keyboard events go to the canvas so the player can type guesses
        try:
            self.canvas.focus_set()
        except Exception:
            pass
        print(f'After init: current_word="{self.current_word}", revealed_len={len(self.revealed)}, wrong_letters={self.wrong_letters}, parts_present={self.parts_present}')
        self.render()

    def _on_start_button(self):
        """Wrapper called by the Start button. Logs the click and reports errors if any occur."""
        print('Start button clicked')
        try:
            self.start_round()
        except Exception as e:
            # Show a helpful error dialog and print traceback to the terminal
            tb = traceback.format_exc()
            print('Error starting round:', e)
            print(tb)
            messagebox.showerror('Error', f'Failed to start a new round: {e}\nSee terminal for details.')

    def on_key(self, event):
        """Handle keyboard input (letters only) when a round is active."""
        if not self.game_active:
            return
        ch = event.char.lower()
        if not ch or not ch.isalpha() or len(ch) != 1:
            return
        self.handle_guess(ch)

    def handle_guess(self, ch):
        """Process a single-letter guess."""
        if ch in self.wrong_letters:
            return
        lower = self.current_word
        any_reveal = False
        for i, c in enumerate(lower):
            if c == ch and not self.revealed[i]:
                self.revealed[i] = True
                any_reveal = True

        if any_reveal:
            # check for win
            if all(self.revealed):
                self.win()
        else:
            # wrong guess
            self.wrong_letters.append(ch)
            # remove next part in the configured order
            for p in PARTS_ORDER:
                if self.parts_present.get(p, False):
                    self.parts_present[p] = False
                    break
            # if all parts removed -> lose
            if not any(self.parts_present.values()):
                self.lose()

        self.render()

    def win(self):
        """Handle win state: stop active play and play confetti."""
        self.game_active = False
        # reveal all to show the lighter-green effect (render handles colors)
        for i in range(len(self.revealed)):
            self.revealed[i] = True
        self.start_confetti(3000)

    def lose(self):
        """Handle lose state: reveal full word and stop play (render displays red messages)."""
        self.game_active = False
        for i in range(len(self.revealed)):
            self.revealed[i] = True

    # ----------------- Drawing helpers -----------------
    def render(self):
        """Clear and redraw entire canvas and UI elements."""
        print('render() called — redrawing canvas')
        # Clear everything and redraw. Avoid querying canvas internals (find_all/bbox)
        # which can raise if the widget is in a transient state. Instead, log which
        # draw helpers run so we can see which elements are being created.
        try:
            self.canvas.delete('all')
        except Exception as e:
            print('Canvas delete error:', repr(e))
            return

        self.draw_gallows()
        self.draw_hangman()
        self.draw_graveyard()
        self.draw_word_display()
        self.draw_overlay()
        # On-canvas debug banner so we can visually confirm the canvas is rendering.
        try:
            state_text = f'Word="{self.current_word}" revealed={sum(1 for r in self.revealed if r)}/{len(self.revealed) if self.revealed else 0} wrong={len(self.wrong_letters)}'
            # Draw a simple background rectangle for readability
            self.canvas.create_rectangle(6, 6, CANVAS_W-6, 36, fill='#ffffff', outline='#111111', width=1)
            self.canvas.create_text(CANVAS_W/2, 20, text=state_text, fill='#111111', font=('Sans', 12, 'bold'))
        except Exception as e:
            print('Debug banner error:', repr(e))

        # If confetti particles exist, draw them directly (confetti animation
        # steps draw confetti without calling render to avoid re-entrancy).
        if self.confetti:
            try:
                for p in self.confetti:
                    x = p['x']; y = p['y']; r = p['r']
                    self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=p['color'], outline='', tags='confetti')
            except Exception as e:
                print('Error drawing confetti in render:', repr(e))

    def draw_gallows(self):
        print('draw_gallows()')
        c = self.canvas
        # base (thicker)
        c.create_line(40, 460, 220, 460, width=10, fill=COLOR_GALLOWS)
        # vertical post
        c.create_line(120, 460, 120, 80, width=10, fill=COLOR_GALLOWS)
        # top beam
        c.create_line(120, 80, 340, 80, width=10, fill=COLOR_GALLOWS)
        # rope
        c.create_line(340, 80, 340, 140, width=6, fill=COLOR_GALLOWS)

    def draw_hangman(self):
        print('draw_hangman()')
        c = self.canvas
        hp = self.parts_present
        headX = 340; headY = 170; headR = 24
        bodyTop = headY + headR; bodyBottom = bodyTop + 90
        armY = headY + 36

        # head
        if hp.get('head', False):
            c.create_oval(headX-headR, headY-headR, headX+headR, headY+headR, width=4, outline=COLOR_HANGMAN)

        # body (thicker)
        if hp.get('body', False):
            c.create_line(headX, bodyTop, headX, bodyBottom, width=6, fill=COLOR_HANGMAN)

        # left arm
        if hp.get('left_arm', False):
            c.create_line(headX, armY, headX-40, armY+28, width=5, fill=COLOR_HANGMAN)

        # right arm
        if hp.get('right_arm', False):
            c.create_line(headX, armY, headX+40, armY+28, width=5, fill=COLOR_HANGMAN)

        # left leg
        if hp.get('left_leg', False):
            c.create_line(headX, bodyBottom, headX-30, bodyBottom+60, width=5, fill=COLOR_HANGMAN)

        # right leg
        if hp.get('right_leg', False):
            c.create_line(headX, bodyBottom, headX+30, bodyBottom+60, width=5, fill=COLOR_HANGMAN)

    def draw_graveyard(self):
        print('draw_graveyard()')
        c = self.canvas
        x = 10; y = 150
        c.create_text(x, y-20, anchor='nw', text='Wrong:', fill=COLOR_WRONG, font=('Monospace', 14, 'bold'))
        for i, ch in enumerate(self.wrong_letters):
            c.create_text(x, y + i*24, anchor='nw', text=ch.upper(), fill=COLOR_WRONG, font=('Monospace', 14, 'bold'))

    def draw_word_display(self):
        print('draw_word_display()')
        c = self.canvas
        word = self.current_word.upper()
        n = len(word)
        if n == 0:
            return

        area_left = 30
        area_right = CANVAS_W - 30
        area_width = area_right - area_left
        spacing = min(40, max(20, area_width // n))
        start_x = area_left + (area_width - spacing*n)/2 + spacing/2
        y_underscore = 380

        for i, ch in enumerate(word):
            x = start_x + i*spacing
            # underscore (bigger)
            c.create_line(x-16, y_underscore, x+16, y_underscore, fill=COLOR_UNDERSCORE, width=3)
            # revealed letters
            if self.revealed[i]:
                # if game_active False and win occured, show lighter green
                color = COLOR_CORRECT if self.game_active else (COLOR_CORRECT_LIGHT if all(self.revealed) else COLOR_CORRECT)
                c.create_text(x, y_underscore - 18, text=ch, fill=color, font=('Monospace', 20, 'bold'))
                c.create_text(x, y_underscore - 10, text=ch, fill=color, font=('Monospace', 16))

    def draw_overlay(self):
        print('draw_overlay()')
        c = self.canvas
        if not self.game_active and self.current_word:
            won = all(self.revealed)
            if won:
                c.create_text(CANVAS_W/2, CANVAS_H/2 - 10, text='You Win!', fill='#047857', font=('Sans', 28, 'bold'))
            else:
                c.create_text(CANVAS_W/2, CANVAS_H/2 - 10, text='You Lose!', fill=COLOR_WRONG, font=('Sans', 28, 'bold'))
                # reveal word in red below
                c.create_text(CANVAS_W/2, CANVAS_H/2 + 24, text='Word: ' + self.current_word.upper(), fill=COLOR_WRONG, font=('Monospace', 16))

    # ----------------- Confetti (simple) -----------------
    def start_confetti(self, duration_ms=3000):
        self.confetti = []
        for _ in range(120):
            self.confetti.append({
                'x': random.uniform(0, CANVAS_W),
                'y': random.uniform(-200, 0),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(1, 4),
                'r': random.uniform(3, 7),
                'color': random.choice(['#EF4444','#F59E0B','#10B981','#3B82F6','#8B5CF6']),
                'rot': random.uniform(0, math.pi*2)
            })
        # schedule animation
        end_time = self._now_ms() + duration_ms
        self._confetti_step(end_time)

    def _confetti_step(self, end_time):
        self.canvas.delete('confetti')
        for p in list(self.confetti):
            x = p['x']; y = p['y']; r = p['r']
            # draw as small oval
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=p['color'], outline='', tags='confetti')
            # update
            p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] += 0.05
        self.render()  # redraw rest of scene (keeps confetti on top)
        if self._now_ms() < end_time and any(p['y'] < CANVAS_H+50 for p in self.confetti):
            self.confetti_job = self.root.after(33, lambda: self._confetti_step(end_time))
        else:
            self.stop_confetti()

    def stop_confetti(self):
        if self.confetti_job:
            try:
                self.root.after_cancel(self.confetti_job)
            except Exception:
                pass
            self.confetti_job = None
        self.confetti = []
        self.canvas.delete('confetti')

    def _now_ms(self):
        return int(self.root.tk.call('clock', 'milliseconds'))


def main():
    root = tk.Tk()
    app = HangmanGame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
