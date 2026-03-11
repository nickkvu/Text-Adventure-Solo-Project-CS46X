"""
Parses raw user input into a (verb, noun) command pair
Assumes a maximum of two word inputs
"""

VALID_VERBS = {"w", "a", "s", "d", "q", "shoot", "pickup", "use", "move", "go", "help"}
VALID_NOUNS = {"north", "south", "east", "west", "up", "down", "left", "right", "item"}


def parse(command):
    """
    Scans both words for a recognized verb and noun.
    Returns (verb, noun) where either may be None if not found.
    """
    words = command.strip().lower().split()

    verb = next((w for w in words if w in VALID_VERBS), None)
    noun = next((w for w in words if w in VALID_NOUNS), None)

    return (verb, noun)