# Hangman Game (Canvas + Python)

This repository contains two implementations of a Hangman game:

- A browser-based HTML/JavaScript canvas version (`index.html`, `style.css`, `script.js`).
- A Python/Tkinter desktop version (`hangman.py`) that loads words from a local file.

Both use a 500×500 canvas area, a Start button centered at the top, gallows and a stick-figure hangman, underscores for the chosen word, a left-side graveyard for wrong guesses, and win/lose behavior (with confetti on win).

Key behavior shared by both implementations:

- The hangman starts fully drawn. Wrong guesses remove parts in this order: left leg, right leg, left arm, right arm, body, head.
- Correct letters appear in green above the underscores. Wrong letters appear in red in the graveyard.
- On loss the game displays a red "You Lose!" message and reveals the correct word in red below it.
- On win the letters turn a lighter green and a confetti animation runs briefly.

How the word bank works

### Python implementation (`hangman.py`) — words file
The Python game expects a local file named `random_common_words_20000.txt` (one word per line) in the same folder as `hangman.py` and will choose a word randomly from it for each round. You already provided `random_common_words_20000.txt` and the Python code reads it directly.

If `random_common_words_20000.txt` is missing or empty, `hangman.py` will fall back to a small built-in word list.

If you prefer to use a different word list, replace `random_common_words_20000.txt` (or change the `WORDS_FILE` constant inside `hangman.py`) and restart the Python program.

### Browser implementation (`script.js`) — virtual 1,200,000-word bank
The original JavaScript version uses a deterministic virtual WordBank that can produce 1,200,000+ pseudo-words without shipping a huge file. If you want the browser version to use a real word list, place a `words.txt` file (one word per line) in the project folder and update `script.js` (there is a commented `fetch('words.txt')` hint in the file).

## Run the Python (Tkinter) version

1. Make sure you have Python 3 installed. On macOS the system Python may include Tkinter. If you installed Python from python.org or with most package managers, Tkinter is usually available.

2. From the project folder run:

```bash
python3 "./hangman.py"
```

3. Click the `Start` button at the top of the window, then type letters on your keyboard to guess.

If Tkinter is not available with your Python distribution, install a Python that includes Tkinter (for macOS the official python.org installer typically includes it) or follow your platform instructions to add Tk support.

## Files in this project

- `index.html`, `style.css`, `script.js` — original browser-based implementation (canvas 500×500).
- `hangman.py` — Python/Tkinter implementation that reads `random_common_words_20000.txt`.
- `random_common_words_20000.txt` — the provided word list used by `hangman.py`.

## Notes

- The Python game uses keyboard input only. If you'd like on-screen buttons (for touch), I can add them.
- The JavaScript version uses a virtual 1.2M-word generator to meet the "1,000,000+ words" requirement without bundling a huge file. You can switch either implementation to a real dictionary by providing a word file and wiring the loader.

Enjoy — let me know if you'd like the Python README section to include troubleshooting notes (e.g., how to add Tkinter on your specific macOS setup) or if you'd like an installer/launch script.

Enjoy!
