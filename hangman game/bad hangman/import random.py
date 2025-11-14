import random

# Simple word pools (example seeds — will expand programmatically)
nouns = ["apple", "dog", "city", "car", "music", "river", "teacher", "book", "tree", "idea"]
verbs = ["run", "jump", "write", "read", "build", "speak", "play", "drive", "think", "learn"]
adjectives = ["happy", "strong", "bright", "quiet", "soft", "quick", "kind", "brave", "fresh", "warm"]
adverbs = ["quickly", "slowly", "quietly", "brightly", "happily", "sadly", "boldly", "gently", "neatly", "simply"]

# Expand each list to desired size
def expand_words(base_words, count):
    expanded = []
    while len(expanded) < count:
        word = random.choice(base_words)
        # Small modification for variety
        if random.random() < 0.3:
            mod = random.choice(["s", "ed", "ing", "ly", "er", "est", "ness", "ment", "ful", "less"])
            word = word + mod if len(word) > 3 else word
        expanded.append(word)
    return expanded[:count]

# Balanced distribution
word_list = (
    expand_words(nouns, 7000)
    + expand_words(verbs, 5000)
    + expand_words(adjectives, 5000)
    + expand_words(adverbs, 3000)
)

random.shuffle(word_list)

# Save to file
with open("random_common_words_20000.txt", "w") as f:
    f.write("\n".join(word_list))

print("✅ Created random_common_words_20000.txt with 20,000 words.")
