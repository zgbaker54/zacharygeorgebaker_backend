import pandas as pd
import numpy as np
import sys
import tty
import termios

# Output file for accepted words
OUTPUT_FILE = "wordListAccepted.txt"


def _getch():
    """Read a single character from stdin immediately (no Enter required)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# Read the source word list and filter to 7-letter words
df = pd.read_csv('wordList.txt', sep=r'\n', engine='python', header=None, names=['Words'])
df7 = df[df.Words.str.len() == 7]

# Shuffle the words randomly
rng = np.random.default_rng()
randIdxs = rng.choice(df7.size, size=df7.size, replace=False)
df7 = df7.iloc[randIdxs].reset_index(drop=True)

# Save shuffled list for reference
df7.to_csv("wordList7Letters.txt", index=False, header=False)

# Load already-accepted words to prevent duplicates
try:
    with open(OUTPUT_FILE, 'r') as f:
        accepted = set(line.strip() for line in f if line.strip())
except FileNotFoundError:
    accepted = set()

# Interactive word-perusal loop
words = df7['Words'].tolist()
for i, word in enumerate(words):
    if word in accepted:
        continue

    while True:
        print(f"[{i+1}/{len(words)}] '{word}' — accept (y), reject (n), quit (q): ", end='', flush=True)
        response = _getch().lower()
        print()  # newline after the char
        if response == 'y':
            with open(OUTPUT_FILE, 'a') as f:
                f.write(word + '\n')
            accepted.add(word)
            count = len(accepted)
            print(f"  → Accepted.  Total words in '{OUTPUT_FILE}': {count}")
            break
        elif response == 'n':
            print(f"  → Rejected.")
            break
        elif response == 'q':
            print(f"Quit early.  Total words in '{OUTPUT_FILE}': {len(accepted)}")
            exit(0)
        else:
            print("  Invalid input.  Enter 'y' (accept), 'n' (reject), or 'q' (quit).")

print(f"\nDone.  Total words in '{OUTPUT_FILE}': {len(accepted)}")