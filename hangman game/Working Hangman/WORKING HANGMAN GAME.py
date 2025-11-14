#!/usr/bin/env python3
"""
Hangman implemented with pygame.

Controls:
- Click the Start button (top-center) to begin a round.
- Guess letters by typing keys on your keyboard (A-Z). Keys are case-insensitive.
- After the game ends a Restart button appears at top-center.

Requirements:
- pygame (install with `pip install pygame` in your environment)

This file tries to read a provided wordlist in a few likely locations (same folder or
in the `bad hangman/` subfolder). If not found it falls back to a small default list.

The hangman is drawn using basic shapes. The hangman starts fully visible and on
each wrong guess one appendage is removed in this order: left leg, right leg,
left arm, right arm, body, head. When all parts are removed the player loses.

When the player completes the word the letters turn lighter green and confetti
is emitted from the top for a few seconds.

"""

import os
import random
import string
import sys
import time

try:
    import pygame
except Exception:
    print('This script requires pygame. Install with: pip install pygame')
    raise


def find_wordlist():
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
                    words = [w for w in words if all(ch.isalpha() for ch in w)]
                    if words:
                        return [w.upper() for w in words]
            except Exception:
                pass
    return []


class PygameHangman:
    """Main Hangman game class using pygame."""
    WIDTH = 500
    HEIGHT = 500

    def __init__(self):
        # Character selection state
        self.character_selected = None  # 'angry', 'short', 'witchy'
        self.selecting_character = True
        pygame.init()
        pygame.display.set_caption('Hangman Game')
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Helvetica', 20)
        self.big_font = pygame.font.SysFont('Helvetica', 30, bold=True)
        self.small_font = pygame.font.SysFont('Helvetica', 14)

        # Load words
        self.word_list = find_wordlist()
        if not self.word_list:
            self.word_list = ['PYTHON', 'HANGMAN', 'DEVELOPER', 'GITHUB', 'COMPUTER', 'PROGRAM', 'KEYBOARD']

        # Game elements state
        self.running = True
        self.in_round = False
        self.chosen_word = ''
        self.guessed = set()
        self.wrong_guesses = []

        # For display
        self.underscores = []  # positions for letter drawing

        # Hangman parts visibility (True means visible)
        self.parts_visible = {
            'head': True,
            'body': True,
            'left_arm': True,
            'right_arm': True,
            'left_leg': True,
            'right_leg': True,
        }

        # Removal order: left leg, right leg, left arm, right arm, body, head
        self.removal_order = ['left_leg', 'right_leg', 'left_arm', 'right_arm', 'body', 'head']

        # Graveyard area coords
        self.grave_x = 60
        self.grave_y = 120

        # UI buttons
        self.start_button_rect = pygame.Rect((self.WIDTH//2 - 70, 40, 140, 40))
        self.restart_button_rect = pygame.Rect((self.WIDTH//2 - 70, 40, 140, 40))

        # Confetti
        self.confetti = []

        # Timing for confetti (ms) after win
        self.confetti_end_time = 0

    # ------------------ Game logic ------------------
    def start_round(self):
        # Only allow if character is selected
        if self.character_selected is None:
            return
        """Begin a new round: choose a word and reset state."""
        self.in_round = True
        self.selecting_character = False
        self.guessed = set()
        self.wrong_guesses = []
        self.chosen_word = random.choice(self.word_list).upper()
        # reset parts
        for k in self.parts_visible:
            self.parts_visible[k] = True
        self.removal_order = ['left_leg', 'right_leg', 'left_arm', 'right_arm', 'body', 'head']
        # build underscores positions (centered)
        n = len(self.chosen_word)
        spacing = 28
        total_w = (n-1) * spacing
        # Place underscores in the left half of the screen, lower down
        left_margin = 30
        max_underscore_width = self.WIDTH // 2 - 2 * left_margin
        # If word is too long, reduce spacing
        if total_w > max_underscore_width:
            spacing = max_underscore_width // max(1, n-1)
            total_w = (n-1) * spacing
        start_x = left_margin
        y = 430  # keep low
        self.underscores = []
        for i in range(n):
            x = start_x + i * spacing
            self.underscores.append((x, y))
        # reset confetti
        self.confetti = []
        self.confetti_end_time = 0
        print('chosen word:', self.chosen_word)

    def reveal_letter(self, ch):
        """Reveal letter ch in the word (if present). Return True if was present."""
        present = ch in self.chosen_word
        if present:
            self.guessed.add(ch)
            return True
        else:
            # wrong guess
            self.wrong_guesses.append(ch)
            # remove next part
            if self.removal_order:
                part = self.removal_order.pop(0)
                self.parts_visible[part] = False
            return False

    def check_win(self):
        return all(ch in self.guessed for ch in self.chosen_word)

    def check_lose(self):
        # lose when no parts remain visible except maybe the gallows
        return not any(self.parts_visible.values())

    # ------------------ Drawing ------------------
    def draw_gallows(self):
        # base
        pygame.draw.line(self.screen, (0,0,0), (220, 460), (480, 460), 6)
        # vertical post
        pygame.draw.line(self.screen, (0,0,0), (300, 460), (300, 120), 6)
        # top beam
        pygame.draw.line(self.screen, (0,0,0), (300, 120), (420, 120), 6)
        # rope
        pygame.draw.line(self.screen, (0,0,0), (420, 120), (420, 150), 3)

    def draw_hangman(self):
        # Always draw a blank hangman regardless of selection
        cx, cy = 420, 170  # head center
        # Head
        if self.parts_visible['head']:
            pygame.draw.circle(self.screen, (230,230,230), (cx, cy), 18, 0)
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy), 18, 2)
        # Body
        if self.parts_visible['body']:
            pygame.draw.line(self.screen, (0,0,0), (cx, cy+18), (cx, cy+88), 2)
        # Arms
        if self.parts_visible['left_arm']:
            pygame.draw.line(self.screen, (0,0,0), (cx, cy+38), (cx-30, cy+58), 2)
        if self.parts_visible['right_arm']:
            pygame.draw.line(self.screen, (0,0,0), (cx, cy+38), (cx+30, cy+58), 2)
        # Legs
        if self.parts_visible['left_leg']:
            pygame.draw.line(self.screen, (0,0,0), (cx, cy+88), (cx-20, cy+128), 2)
        if self.parts_visible['right_leg']:
            pygame.draw.line(self.screen, (0,0,0), (cx, cy+88), (cx+20, cy+128), 2)

    def draw_underscores_and_letters(self):
        for i, (x, y) in enumerate(self.underscores):
            # underscore line
            pygame.draw.line(self.screen, (0,0,0), (x-10, y), (x+10, y), 2)
            ch = self.chosen_word[i]
            if ch in self.guessed:
                # green letter above underscore
                color = (0,180,0)
                # if won, lighter green
                if self.check_win():
                    color = (102,255,102)
                text = self.font.render(ch, True, color)
                rect = text.get_rect(center=(x, y-16))
                self.screen.blit(text, rect)

    def draw_graveyard(self):
        # show wrong guesses vertically starting at grave_y
        for idx, ch in enumerate(self.wrong_guesses):
            text = self.small_font.render(ch, True, (200,0,0))
            self.screen.blit(text, (self.grave_x, self.grave_y + idx * 22))

    def draw_buttons(self):
        if self.selecting_character:
            # Draw character selection
            self.draw_character_selection()
        elif not self.in_round:
            # draw Start button
            pygame.draw.rect(self.screen, (76,175,80), self.start_button_rect)
            text = self.font.render('Start', True, (255,255,255))
            rect = text.get_rect(center=self.start_button_rect.center)
            self.screen.blit(text, rect)
            hint = self.small_font.render('Click Start to play', True, (80,80,80))
            hint_rect = hint.get_rect(center=(self.WIDTH//2, self.start_button_rect.bottom + 12))
            self.screen.blit(hint, hint_rect)
        # Draw restart button when game over
        if self.in_round and (self.check_win() or self.check_lose()):
            pygame.draw.rect(self.screen, (33,150,243), self.restart_button_rect)
            text = self.font.render('Restart', True, (255,255,255))
            rect = text.get_rect(center=self.restart_button_rect.center)
            self.screen.blit(text, rect)

    def draw_character_selection(self):
        # Draw three identical blank hangman heads, label 1, 2, 3, and put title above
        top_y = 50
        icon_size = 36
        spacing = 90
        base_x = self.WIDTH//2 - spacing
        # Title above characters, but within frame
        title = self.big_font.render('Choose Your Hangman', True, (0,0,0))
        self.screen.blit(title, title.get_rect(center=(self.WIDTH//2, 30)))
        # Left: blank hangman with a small top hat
        rect1 = pygame.Rect(base_x-50, top_y, icon_size, icon_size*2)
        self.draw_character_icon('blankman_hat', rect1.centerx, rect1.centery-10, small=True)
        pygame.draw.rect(self.screen, (0,0,0), rect1, 2)
        label = self.small_font.render('1', True, (0,0,0))
        self.screen.blit(label, label.get_rect(center=(rect1.centerx, rect1.bottom+10)))
        # Middle: blank hangman
        rect2 = pygame.Rect(base_x+spacing, top_y, icon_size, icon_size*2)
        self.draw_character_icon('blankman', rect2.centerx, rect2.centery-10, small=True)
        pygame.draw.rect(self.screen, (0,0,0), rect2, 2)
        label = self.small_font.render('2', True, (0,0,0))
        self.screen.blit(label, label.get_rect(center=(rect2.centerx, rect2.bottom+10)))
        # Right: blank hangman
        rect3 = pygame.Rect(base_x+2*spacing+50, top_y, icon_size, icon_size*2)
        self.draw_character_icon('blankman', rect3.centerx, rect3.centery-10, small=True)
        pygame.draw.rect(self.screen, (0,0,0), rect3, 2)
        label = self.small_font.render('3', True, (0,0,0))
        self.screen.blit(label, label.get_rect(center=(rect3.centerx, rect3.bottom+10)))
        # Store rects for click detection
        self.character_rects = [rect1, rect2, rect3]

    def draw_character_icon(self, char, cx, cy, small=False):
        # Draw a small version of the character for selection
        if small:
            scale = 0.6
        else:
            scale = 1.0
        if char == 'blankman':
            r = int(18 * scale)
            offset = int(20 * scale)
            # Blank hangman head (plain circle)
            pygame.draw.circle(self.screen, (230,230,230), (cx, cy-offset), r, 0)
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy-offset), r, 2)
        elif char == 'blankman_hat':
            r = int(18 * scale)
            offset = int(20 * scale)
            # Blank hangman head (plain circle)
            pygame.draw.circle(self.screen, (230,230,230), (cx, cy-offset), r, 0)
            pygame.draw.circle(self.screen, (0,0,0), (cx, cy-offset), r, 2)
            # Small top hat (fits within frame)
            hat_w = int(14 * scale)
            hat_h = int(7 * scale)
            brim_h = int(3 * scale)
            pygame.draw.rect(self.screen, (0,0,0), (cx-hat_w//2, cy-offset-r-6, hat_w, hat_h))
            pygame.draw.rect(self.screen, (0,0,0), (cx-hat_w, cy-offset-r-6+hat_h, hat_w*2, brim_h))

    def spawn_confetti(self):
        # create small confetti pieces
        colors = [(255,77,77),(77,255,77),(77,77,255),(255,255,77),(255,77,255),(77,255,255)]
        for i in range(40):
            x = random.randint(10, self.WIDTH-10)
            y = random.randint(-100, -10)
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(1, 4)
            size = random.randint(3,7)
            self.confetti.append([x, y, vx, vy, size, random.choice(colors)])
        self.confetti_end_time = pygame.time.get_ticks() + 3000

    def update_confetti(self):
        now = pygame.time.get_ticks()
        for piece in list(self.confetti):
            piece[0] += piece[2]
            piece[1] += piece[3]
            # rotate gravity slightly
            piece[3] += 0.05
            if piece[1] > self.HEIGHT + 20:
                try:
                    self.confetti.remove(piece)
                except ValueError:
                    pass
        # if time up, clear after small delay
        if now > self.confetti_end_time and self.confetti_end_time != 0:
            if not self.confetti:
                self.confetti_end_time = 0

    def draw_confetti(self):
        for piece in self.confetti:
            x, y, vx, vy, size, color = piece
            pygame.draw.ellipse(self.screen, color, (int(x), int(y), size, size))

    # ------------------ Main loop ------------------
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if self.selecting_character:
                        # Detect character selection
                        self.draw_character_selection()  # ensure rects exist
                        for idx, rect in enumerate(self.character_rects):
                            if rect.collidepoint(mx, my):
                                if idx == 0:
                                    self.character_selected = 'angry'
                                elif idx == 1:
                                    self.character_selected = 'short'
                                elif idx == 2:
                                    self.character_selected = 'witchy'
                                self.selecting_character = False
                                break
                    elif not self.in_round and self.start_button_rect.collidepoint(mx, my):
                        self.start_round()
                    elif self.in_round and (self.check_win() or self.check_lose()) and self.restart_button_rect.collidepoint(mx, my):
                        # restart returns to character selection
                        self.in_round = False
                        self.chosen_word = ''
                        self.character_selected = None
                        self.selecting_character = True
                elif event.type == pygame.KEYDOWN:
                    if self.in_round and not (self.check_win() or self.check_lose()):
                        ch = event.unicode.upper()
                        if ch and ch in string.ascii_uppercase and ch not in self.guessed and ch not in self.wrong_guesses:
                            present = self.reveal_letter(ch)
                            # If wrong and no parts remain, trigger lose actions
                            if not present and self.check_lose():
                                # reveal word
                                pass
                    else:
                        # allow keyboard to start the round
                        if not self.in_round and not self.selecting_character and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            self.start_round()

            # Drawing
            self.screen.fill((245,245,245))
            self.draw_gallows()
            # draw initial hangman parts (only those still visible)
            if not self.selecting_character:
                self.draw_hangman()
            # Draw underscores and revealed letters
            if self.in_round:
                self.draw_underscores_and_letters()
                self.draw_graveyard()
            # Draw confetti if win
            if self.check_win() and self.confetti_end_time == 0:
                self.spawn_confetti()
            self.update_confetti()
            self.draw_confetti()

            # Buttons and character selection
            self.draw_buttons()

            # Win/Lose messages
            # Draw win/lose popup with white background
            if self.in_round and (self.check_lose() or self.check_win()):
                # Popup rectangle
                popup_w = 320
                popup_h = 120
                popup_x = (self.WIDTH - popup_w) // 2
                popup_y = (self.HEIGHT - popup_h) // 2 - 20
                pygame.draw.rect(self.screen, (255,255,255), (popup_x, popup_y, popup_w, popup_h))
                pygame.draw.rect(self.screen, (0,0,0), (popup_x, popup_y, popup_w, popup_h), 2)
                if self.check_lose():
                    msg = self.big_font.render('You Lose!', True, (0,0,0))
                    self.screen.blit(msg, msg.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20)))
                    reveal = self.font.render('Word: ' + self.chosen_word, True, (200,0,0))
                    self.screen.blit(reveal, reveal.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 + 20)))
                elif self.check_win():
                    msg = self.big_font.render('You Win!', True, (0,0,0))
                    self.screen.blit(msg, msg.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 20)))

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


def main():
    app = PygameHangman()
    app.run()


if __name__ == '__main__':
    main()
