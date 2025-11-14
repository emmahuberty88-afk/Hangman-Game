#!/usr/bin/env python3
"""
Hangman GUI game using tkinter.

Features:
- 500x500 window with a Start button top-center that begins a new round.
- Gallows (base, vertical post, top beam, rope) and a stick-figure hangman drawn on a Canvas.
- Underscores under the hangman for each letter in the chosen word.
- Word chosen randomly from a word list text file if available (tries a few locations), otherwise falls back to a small list.
- Player guesses letters by typing on the keyboard. Correct letters appear in green above their underscores.
- Incorrect guesses are shown in red in a "graveyard" area to the left of the hangman.
- On each incorrect guess an appendage disappears in order: left leg, right leg, left arm, right arm, body, head.
- When all parts are gone player loses and the correct word is revealed in red and a Restart button appears.
- When player completes the word all letters turn lighter green, "You Win!" appears and confetti is generated for a few seconds.

Usage: run this file with Python 3.6+.

"""

import os
import random
import string
import tkinter as tk
from tkinter import messagebox


def find_wordlist():
    """Try to find the provided word list in a few likely locations relative to this file.

    Returns a list of words or an empty list if not found.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, 'bad hangman', 'random_common_words_20000.txt'),
        os.path.join(here, 'random_common_words_20000.txt'),
        os.path.join(here, '..', 'bad hangman', 'random_common_words_20000.txt'),
        os.path.join(here, '..', 'random_common_words_20000.txt'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    words = [w.strip() for w in f if w.strip()]
                    # filter to simple words (letters only)
                    words = [w for w in words if all(ch.isalpha() for ch in w)]
                    if words:
                        return words
            except Exception:
                pass
    return []


class HangmanGame:
    """Encapsulates the Hangman game logic and GUI rendering using tkinter Canvas."""

    def __init__(self, root):
        self.root = root
        self.width = 500
        self.height = 500
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg='white')
        self.canvas.pack()

        # Load words
        self.word_list = find_wordlist()
        if not self.word_list:
            # Fallback short list
            self.word_list = [
                'PYTHON', 'HANGMAN', 'DEVELOPER', 'GITHUB', 'COMPUTER', 'PROGRAM', 'KEYBOARD'
            ]

        # UI elements: use canvas-drawn buttons to avoid embedded-widget display issues
        self.start_button_ids = None  # (rect_id, text_id)
        self.restart_button_ids = None

        # Game state
        self.chosen_word = ''
        self.letters_positions = []  # list of text ids for letters above underscores
        self.underscore_positions = []  # list of line ids (for future use)
        self.guessed = set()
        self.wrong_guesses = []
        self.max_wrong = 6
        self.parts_ids = []  # items that will be removed on wrong guesses in removal order
        self.parts_removal_order = []  # item ids in the order to remove
        self.game_over = False

        # Bind keys
        root.bind('<Key>', self.on_key_press)
        # Also bind Space and Enter to start the game as a fallback if the Start button is not visible
        root.bind('<space>', lambda e: self.start_game())
        root.bind('<Return>', lambda e: self.start_game())

        # Helpful console hint for users who can't see the Start button on some macOS setups
        print("Hint: If you don't see the Start button, press Space or Enter to begin the game.")

        # Draw static gallows and initial hangman (fully visible)
        self.draw_gallows()
        self.draw_full_hangman()

        # Now create the Start button on top of the static drawing so it's visible
        self.create_start_button()

        # Debug: list canvas items and check the start button bbox so we can diagnose visibility issues
        try:
            items = self.canvas.find_all()
            print('Canvas items after init:', items)
            start_items = self.canvas.find_withtag('start_btn')
            print(' start_btn items:', start_items)
            print(' start_btn bbox:', self.canvas.bbox('start_btn'))
            # print each item's tags and coords
            for it in items:
                print('  item', it, 'tags=', self.canvas.gettags(it), 'coords=', self.canvas.coords(it))
        except Exception:
            pass

        # Graveyard layout base coordinates
        self.grave_x = 60
        self.grave_y = 120
        self.grave_spacing = 22

        # Word display baseline
        self.word_y = 380

        # As a robust fallback for macOS cases where canvas items may be hard to see,
        # create a small modal Toplevel with a native Start button. This guarantees
        # that the player can begin the game even if the canvas button is invisible.
        # The dialog will be automatically destroyed when Start is clicked.
        try:
            self.start_dialog = tk.Toplevel(self.root)
            self.start_dialog.title('Start')
            self.start_dialog.transient(self.root)
            self.start_dialog.resizable(False, False)
            # Use a small wrapper so we destroy the dialog first and then schedule start_game
            def native_start():
                try:
                    self.start_dialog.destroy()
                except Exception:
                    pass
                # schedule start_game slightly later so the destroy completes and the event loop settles
                try:
                    self.root.after(50, self.start_game)
                except Exception:
                    # fallback: call directly
                    self.start_game()

            btn = tk.Button(self.start_dialog, text='Start', command=native_start)
            btn.pack(padx=16, pady=12)
            # position dialog near center of main window
            self.start_dialog.update_idletasks()
            w = self.start_dialog.winfo_width()
            h = self.start_dialog.winfo_height()
            rx = self.root.winfo_x() + (self.width - w) // 2
            ry = self.root.winfo_y() + 60
            try:
                self.start_dialog.geometry(f'+{rx}+{ry}')
            except Exception:
                pass
            try:
                # try to ensure the dialog is on top and takes focus (but avoid modal grab which can interfere)
                self.start_dialog.lift()
                self.start_dialog.focus_force()
            except Exception:
                pass
        except Exception:
            # non-fatal if Toplevel cannot be created
            self.start_dialog = None

    # ----------------- Drawing helpers -----------------
    def draw_gallows(self):
        """Draw the static parts of the gallows (base, post, beam, rope)."""
        # base
        self.canvas.create_line(220, 460, 480, 460, width=6)
        # vertical post
        self.canvas.create_line(300, 460, 300, 120, width=6)
        # top beam
        self.canvas.create_line(300, 120, 420, 120, width=6)
        # rope
        self.canvas.create_line(420, 120, 420, 150, width=3)

    def draw_full_hangman(self):
        """Draw the full stick-figure hangman; save parts so they can be removed later."""
        # Head
        head = self.canvas.create_oval(400, 150, 440, 190, width=2, fill='')
        # Body
        body = self.canvas.create_line(420, 190, 420, 260, width=2)
        # Arms
        left_arm = self.canvas.create_line(420, 210, 390, 230, width=2)
        right_arm = self.canvas.create_line(420, 210, 450, 230, width=2)
        # Legs
        left_leg = self.canvas.create_line(420, 260, 390, 300, width=2)
        right_leg = self.canvas.create_line(420, 260, 450, 300, width=2)

        # Save parts and removal order. Removal order: left leg, right leg, left arm, right arm, body, head
        self.parts_ids = {
            'head': head,
            'body': body,
            'left_arm': left_arm,
            'right_arm': right_arm,
            'left_leg': left_leg,
            'right_leg': right_leg,
        }
        self.parts_removal_order = [
            self.parts_ids['left_leg'],
            self.parts_ids['right_leg'],
            self.parts_ids['left_arm'],
            self.parts_ids['right_arm'],
            self.parts_ids['body'],
            self.parts_ids['head'],
        ]

    def clear_word_display(self):
        """Remove any previous word display elements from the canvas."""
        for tid in self.letters_positions:
            try:
                self.canvas.delete(tid)
            except Exception:
                pass
        for lid in self.underscore_positions:
            try:
                self.canvas.delete(lid)
            except Exception:
                pass
        self.letters_positions = []
        self.underscore_positions = []

    def draw_underscores(self):
        """Draw underscores for each letter in the chosen word, and create containers for letters above them."""
        self.clear_word_display()
        n = len(self.chosen_word)
        # compute total width and spacing
        letter_spacing = 28
        total_w = (n-1) * letter_spacing
        start_x = (self.width - total_w) // 2

        for i, ch in enumerate(self.chosen_word):
            x1 = start_x + i * letter_spacing - 10
            x2 = start_x + i * letter_spacing + 10
            # underscore line
            line = self.canvas.create_line(x1, self.word_y, x2, self.word_y, width=2)
            self.underscore_positions.append(line)
            # placeholder for letter (above the underscore)
            letter_id = self.canvas.create_text((x1+x2)//2, self.word_y-16, text='', font=('Helvetica', 16, 'bold'))
            self.letters_positions.append(letter_id)

    # ----------------- Canvas button helpers -----------------
    def create_start_button(self):
        """Create a Start button using canvas shapes (rectangle + text) at top-center and bind click."""
        # remove any existing start button/hint
        self.canvas.delete('start_btn')
        self.canvas.delete('start_hint')

        # make the button larger and lower so it's clearly visible on macOS where titlebars
        # or safe-areas can overlap the very top of the window; place at y=80 to be safe
        w = 160
        h = 50
        x = self.width // 2
        y = 80

        rect = self.canvas.create_rectangle(x - w//2, y - h//2, x + w//2, y + h//2, fill='#4CAF50', outline='black', width=2, tags='start_btn')
        text = self.canvas.create_text(x, y, text='Start', font=('Helvetica', 14, 'bold'), fill='white', tags='start_btn')
        # small hint text below the button to make it obvious
        hint = self.canvas.create_text(x, y + h//1.5, text='Click Start to play', font=('Helvetica', 10), fill='gray20', tags='start_hint')

        self.canvas.tag_bind('start_btn', '<Button-1>', lambda e: self.start_game())
        # make sure the start button and hint are on top of other canvas items
        try:
            self.canvas.tag_raise('start_btn')
            self.canvas.tag_raise('start_hint')
        except Exception:
            pass
        self.start_button_ids = (rect, text, hint)

        # brief pulse animation to draw attention: alternate fill a few times
        def pulse(count=6):
            if count <= 0:
                try:
                    self.canvas.itemconfigure(rect, fill='#4CAF50')
                except Exception:
                    pass
                return
            try:
                color = '#66BB6A' if count % 2 == 0 else '#388E3C'
                self.canvas.itemconfigure(rect, fill=color)
            except Exception:
                pass
            self.root.after(300, lambda: pulse(count-1))

        try:
            pulse()
        except Exception:
            pass

        # Ensure the start button is on top (try twice: immediate and after a short delay)
        try:
            self.canvas.tag_raise('start_btn')
            self.canvas.tag_raise('start_hint')
            # also schedule another raise after widgets have been drawn
            self.root.after(80, lambda: (self.canvas.tag_raise('start_btn'), self.canvas.tag_raise('start_hint')))
        except Exception:
            pass

        # debug print bbox
        try:
            print('created start_btn bbox:', self.canvas.bbox('start_btn'))
        except Exception:
            pass

    def create_restart_button(self):
        """Create a Restart button using canvas shapes at top-center and bind click."""
        self.canvas.delete('restart_btn')
        w = 110
        h = 30
        x = self.width // 2
        y = 50
        rect = self.canvas.create_rectangle(x - w//2, y - h//2, x + w//2, y + h//2, fill='#2196F3', outline='black', tags='restart_btn')
        text = self.canvas.create_text(x, y, text='Restart', font=('Helvetica', 12, 'bold'), fill='white', tags='restart_btn')
        self.canvas.tag_bind('restart_btn', '<Button-1>', lambda e: self.restart())
        try:
            self.canvas.tag_raise('restart_btn')
        except Exception:
            pass
        self.restart_button_ids = (rect, text)

    # ----------------- Game lifecycle -----------------
    def start_game(self):
        """Start a new game: choose a word, reset state and UI, remove start button."""
        # If a native start dialog exists, remove it now so the main window is visible.
        if getattr(self, 'start_dialog', None):
            try:
                try:
                    # release grab if we set it
                    self.start_dialog.grab_release()
                except Exception:
                    pass
                self.start_dialog.destroy()
            except Exception:
                pass
            self.start_dialog = None

        # Defensive: if the canvas widget was destroyed for any reason, recreate it
        if not getattr(self, 'canvas', None) or not self.canvas.winfo_exists():
            try:
                print('Canvas missing or destroyed; recreating canvas widget')
                self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg='white')
                # remove any previous packing and pack new canvas
                self.canvas.pack()
            except Exception as e:
                print('Failed to recreate canvas:', e)

        # Safely remove start button (erase it) and ensure restart button is removed.
        # Delete the canvas window first so the button visibly disappears even if widget.destroy() raises.
        # Debug visibility: print when start_game is invoked and remove any canvas buttons
        print('start_game() called')
        print('  removing canvas start_btn and restart_btn (if present)')
        # remove canvas-drawn start/restart buttons (preferred)
        try:
            self.canvas.delete('start_btn')
        except Exception:
            pass
        try:
            self.canvas.delete('start_hint')
        except Exception:
            pass
        self.start_button_ids = None
        try:
            self.canvas.delete('restart_btn')
        except Exception:
            pass
        self.restart_button_ids = None

        # Also defensively remove any legacy widget-based buttons if they exist
        if getattr(self, 'start_button', None):
            try:
                self.start_button.destroy()
            except Exception:
                pass
            self.start_button = None
        if getattr(self, 'start_window', None):
            try:
                self.canvas.delete(self.start_window)
            except Exception:
                pass
            self.start_window = None

        # Force the canvas to update immediately so the UI reflects removal
        try:
            self.canvas.update_idletasks()
            print('  canvas update_idletasks called')
        except Exception:
            pass

        self.game_over = False
        self.guessed = set()
        self.wrong_guesses = []

        # choose a random word
        self.chosen_word = random.choice(self.word_list).upper()
        print('chosen word:', self.chosen_word)

        # reset hangman: if some parts are missing, redraw everything: remove old parts and redraw all
        for item in list(self.parts_ids.values()):
            try:
                self.canvas.delete(item)
            except Exception:
                pass

        # draw gallows and full hangman again
        self.canvas.delete('all')
        self.draw_gallows()
        self.draw_full_hangman()

        # redraw graveyard area label
        self.canvas.create_text(self.grave_x, self.grave_y - 30, text='Graveyard', font=('Helvetica', 12, 'bold'))

        # draw underscores for chosen word
        self.draw_underscores()
        try:
            print('underscores created, letter count:', len(self.letters_positions), 'ids=', self.letters_positions)
        except Exception:
            pass

        # Ensure the main window and canvas are visible and updated
        try:
            self.canvas.update_idletasks()
            self.canvas.update()
        except Exception:
            pass
        try:
            # bring main window to front in case a dialog was covering it
            self.root.lift()
            self.root.focus_force()
            print('drew gallows and underscores; window lifted and focused')
        except Exception:
            pass

        # reset parts removal order in case it's been modified
        self.parts_removal_order = [
            self.parts_ids['left_leg'],
            self.parts_ids['right_leg'],
            self.parts_ids['left_arm'],
            self.parts_ids['right_arm'],
            self.parts_ids['body'],
            self.parts_ids['head'],
        ]

        # draw initial hangman is already done; show empty graveyard
        self.draw_graveyard()

    def draw_graveyard(self):
        """Render all wrong guessed letters in the graveyard area (left side)."""
        # Clear previous grave letters by deleting items with tag 'grave'
        try:
            self.canvas.delete('grave')
        except Exception as e:
            # Log the error but don't crash the UI callback
            print('Warning: failed to delete grave tag on canvas:', repr(e))
        
        for idx, ch in enumerate(self.wrong_guesses):
            x = self.grave_x
            y = self.grave_y + idx * self.grave_spacing
            self.canvas.create_text(x, y, text=ch, fill='red', font=('Helvetica', 14, 'bold'), tag='grave')
        try:
            self.canvas.update_idletasks()
            print('graveyard drawn, wrong guesses:', self.wrong_guesses)
        except Exception:
            pass

    def on_key_press(self, event):
        """Handle key press events for guessing letters. Ignores non-alpha and if game not running."""
        if self.game_over:
            return
        if not self.chosen_word:
            return
        ch = event.char.upper()
        if not ch or ch not in string.ascii_uppercase:
            return
        if ch in self.guessed:
            return
        self.guessed.add(ch)

        if ch in self.chosen_word:
            # reveal all positions of this letter
            for i, letter in enumerate(self.chosen_word):
                if letter == ch:
                    self.canvas.itemconfigure(self.letters_positions[i], text=ch, fill='green')
            # check win
            if all(self.canvas.itemcget(tid, 'text') != '' for tid in self.letters_positions):
                self.win()
        else:
            # wrong guess
            self.wrong_guesses.append(ch)
            self.draw_graveyard()
            self.remove_next_part()

    def remove_next_part(self):
        """Remove the next part from the hangman according to the removal order.

        If no parts remain, trigger loss.
        """
        if not self.parts_removal_order:
            # already empty
            return
        next_id = self.parts_removal_order.pop(0)
        try:
            self.canvas.delete(next_id)
        except Exception:
            pass

        if not self.parts_removal_order:
            self.lose()

    def lose(self):
        """Handle losing the game: show message and reveal the word; provide restart button."""
        self.game_over = True
        # big "You lose!" message
        self.canvas.create_text(self.width//2, self.height//2 - 20, text='You Lose!', font=('Helvetica', 30, 'bold'), fill='black', tag='endmsg')
        # reveal correct word below in red
        reveal_text = 'Word: ' + self.chosen_word
        self.canvas.create_text(self.width//2, self.height//2 + 20, text=reveal_text, font=('Helvetica', 20, 'bold'), fill='red', tag='endmsg')
        # show restart button
        self.show_restart()

    def win(self):
        """Handle winning the game: change letters to lighter green, show message, produce confetti and restart."""
        self.game_over = True
        # change letters to lighter green
        for tid in self.letters_positions:
            self.canvas.itemconfigure(tid, fill='#66ff66')

        self.canvas.create_text(self.width//2, self.height//2 - 20, text='You Win!', font=('Helvetica', 30, 'bold'), fill='black', tag='endmsg')

        # start confetti
        self.start_confetti(duration=3000)

        # show restart button after a short delay
        self.root.after(1000, self.show_restart)

    def show_restart(self):
        """Create a Restart button on screen to allow replaying."""
        # use canvas-based restart button
        if self.restart_button_ids:
            return
        self.create_restart_button()

    def restart(self):
        """Restart the game: clear overlays and show the start button again (or start immediately)."""
        # remove any end messages and confetti
        self.canvas.delete('endmsg')
        self.canvas.delete('confetti')
        # remove any canvas restart button
        try:
            self.canvas.delete('restart_btn')
        except Exception:
            pass
        self.restart_button_ids = None

        # Reset state
        self.chosen_word = ''
        self.guessed = set()
        self.wrong_guesses = []
        self.game_over = False

        # clear canvas and redraw static gallows and fresh hangman
        self.canvas.delete('all')
        self.draw_gallows()
        self.draw_full_hangman()

        # recreate start button in the cleared canvas
        self.create_start_button()

    # ----------------- Confetti -----------------
    def start_confetti(self, duration=3000):
        """Launch confetti pieces that fall from the top for 'duration' milliseconds."""
        end_time = self.root.after(duration, lambda: None)
        # spawn many little rectangles/ovals with random colors and animate them falling
        import time
        start_t = self.root.winfo_toplevel().tk.call('clock', 'milliseconds')

        # create a lot of confetti pieces
        pieces = []
        colors = ['#ff4d4d', '#4dff4d', '#4d4dff', '#ffff4d', '#ff4dff', '#4dffff']
        for i in range(60):
            x = random.randint(10, self.width-10)
            y = random.randint(-80, -10)
            size = random.randint(4, 8)
            color = random.choice(colors)
            pid = self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline='', tag='confetti')
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(2, 5)
            pieces.append((pid, vx, vy))

        def animate():
            # move each piece; if below screen remove it
            for i, (pid, vx, vy) in enumerate(pieces[:]):
                try:
                    self.canvas.move(pid, vx, vy)
                    coords = self.canvas.coords(pid)
                    if coords and coords[1] > self.height + 20:
                        self.canvas.delete(pid)
                        pieces.remove((pid, vx, vy))
                except Exception:
                    pass
            if pieces:
                self.root.after(33, animate)

        animate()


def main():
    root = tk.Tk()
    root.title('Hangman Game')
    # Set fixed size
    root.resizable(False, False)
    app = HangmanGame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
