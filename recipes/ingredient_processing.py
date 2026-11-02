"""Conservative deterministic parsing and exact normalized food matching."""
import re
import unicodedata
from fractions import Fraction
from .units import ALIASES

UNICODE_FRACTIONS = dict(zip('½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⅐⅑⅒',
    ('1/2', '1/3', '2/3', '1/4', '3/4', '1/5', '2/5', '3/5', '4/5',
     '1/6', '5/6', '1/8', '3/8', '5/8', '7/8', '1/7', '1/9', '1/10')))
NUMBER = r'(?:\d+-\d+\s*/\s*\d+|\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:\.\d+)?|\.\d+)'
PLURALS = dict(zip(
    'eggs onions carrots tomatoes potatoes leaves loaves halves cloves breasts thighs beans mushrooms apples bananas berries strawberries blueberries raspberries peppers lemons limes oranges peas walnuts almonds pecans oats'.split(),
    'egg onion carrot tomato potato leaf loaf half clove breast thigh bean mushroom apple banana berry strawberry blueberry raspberry pepper lemon lime orange pea walnut almond pecan oat'.split()))
MAX_LINES = 200


def normalize_food_name(name):
    name = ''.join(c for c in unicodedata.normalize('NFKD', name.casefold()) if not unicodedata.combining(c))
    name = name.replace('’', '').replace("'", '')
    words = re.sub(r'[^\w\s]', ' ', name).replace('_', ' ').split()
    return ' '.join(PLURALS.get(word, word) for word in words)


def ingredient_lines(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > MAX_LINES:
        raise ValueError('Review supports at most 200 ingredient lines. Split this recipe before continuing; no lines were saved.')
    return lines


def _number(value):
    value = re.sub(r'(?<=\d)-(?=\d+\s*/)', ' ', value.strip())
    parts = re.split(r'\s+(?=\d+\s*/)', value)
    result = sum((Fraction(part.replace(' ', '')) for part in parts), Fraction())
    if result <= 0 or result > 1000000:
        raise ValueError
    return float(result)


def parse_ingredient(original):
    warnings, notes = [], []
    result = {'original_text': original, 'quantity': None, 'quantity_max': None,
              'unit': 'other', 'food_name': '', 'preparation_notes': '', 'warnings': warnings}
    text = re.sub(r'^\s*(?:[•*]\s*|-\s+)', '', original).strip()
    for char, fraction in UNICODE_FRACTIONS.items():
        text = re.sub(r'(?<=\d)' + char, ' ' + fraction, text)
        text = text.replace(char, fraction)
    text = unicodedata.normalize('NFKC', text).replace('⁄', '/')
    approximate = re.match(r'^(about|approximately|approx\.?|roughly)\s+', text, re.I)
    if approximate:
        notes.append(approximate[1])
        warnings.append('Approximate quantity; confirm how much to buy.')
        text = text[approximate.end():]
    words = {'a': '1', 'an': '1', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
             'five': '5', 'six': '6', 'half': '1/2', 'quarter': '1/4'}
    word = re.match(r'^(a|an|one|two|three|four|five|six|half|quarter)\s+(?!few\b|little\b)', text, re.I)
    if word:
        text = words[word[1].casefold()] + ' ' + text[word.end():]
    amount = re.match(r'^(' + NUMBER + r')(?:\s*(?:[–—-]|\bto\b)\s*(' + NUMBER + r'))?(?=\s|[A-Za-z(]|$)', text, re.I)
    if amount:
        try:
            result['quantity'] = _number(amount[1])
            if amount[2]:
                result['quantity_max'] = _number(amount[2])
                if result['quantity_max'] < result['quantity']:
                    raise ValueError
                warnings.append('Range: shopping will use the upper amount. Confirm or correct both values.')
            elif re.search(r'\d-\d+/', amount[1]):
                warnings.append('Hyphenated mixed number interpreted as a fraction; confirm the amount.')
            text = text[amount.end():].strip()
        except (ValueError, ZeroDivisionError, OverflowError):
            result['quantity'] = result['quantity_max'] = None
            warnings.append('The amount is invalid or outside the supported range; enter a positive quantity.')
    else:
        warnings.append('No reliable quantity found. Enter an amount or explicitly keep this line as reference only.')
    package = re.match(r'^\(([^)]+)\)\s*', text)
    if package:
        notes.append('Package size: ' + package[1])
        text = text[package.end():]
        warnings.append('Package size retained in notes; confirm the package count and unit.')
    modifier = re.match(r'^(heaped|heaping|scant|level)\s+', text, re.I)
    if modifier:
        notes.append(modifier[1])
        warnings.append('Approximate measure; confirm the amount.')
        text = text[modifier.end():]
    fluid = re.match(r'^(?:fluid\s+ounces?|fl\.?\s*oz\.?)\b\s*', text, re.I)
    if fluid:
        result['unit'] = 'fluid ounce(s)'
        text = text[fluid.end():].lstrip('. ')
    unit = re.match(r'^([A-Za-z]+)\.?\b\s*', text)
    if fluid:
        pass
    elif unit and unit[1].casefold() in ALIASES:
        result['unit'] = 'TABLESPOON(s)' if unit[1] == 'T' else ALIASES[unit[1].casefold()]
        text = text[unit.end():].lstrip('. ').strip()
        text = re.sub(r'^of\s+', '', text, flags=re.I)
    elif result['quantity'] is not None:
        result['unit'] = 'item(s)'
        warnings.append('No explicit measurement unit; counted items are suggested. Confirm the unit.')
    if re.search(r'\b(?:and|or)\b', text, re.I):
        warnings.append('Possible multiple foods or alternatives. Split the original line if necessary, then refresh suggestions.')
    text, comma, tail = text.partition(',')
    if comma:
        notes.append(tail.strip())
        if re.search(r'\b(to taste|as needed|plus|optional)\b', tail, re.I):
            warnings.append('An unspecified or additional amount appears in the notes; confirm the shopping quantity.')
    def parenthetical(match):
        notes.append(match[1])
        warnings.append('Parenthetical description or alternative measurement retained in notes; check it.')
        return ' '
    text = re.sub(r'\(([^)]+)\)', parenthetical, text)
    preparation = re.match(r'^((?:(?:finely|roughly|freshly|coarsely)\s+)?(?:chopped|diced|minced|sliced|grated|melted))\s+', text, re.I)
    if preparation:
        notes.append(preparation[1])
        warnings.append('Preparation appears before the food; confirm the food and measurement.')
        text = text[preparation.end():]
    size = re.match(r'^(extra[- ]large|small|medium|large)\s+', text, re.I)
    if size:
        notes.append(size[1])
        text = text[size.end():]
    taste = re.search(r'\b(to taste|as needed|for serving|for frying|for dusting|for greasing|for garnish|plus extra|plus more|optional)\b.*$', text, re.I)
    if taste:
        notes.append(taste[0])
        text = text[:taste.start()]
        warnings.append('Unspecified or optional amount; confirm how much to buy or keep as reference only.')
    trailing = re.search(r'\s+(chopped|diced|minced|sliced|grated|melted|softened|sifted|divided|beaten)$', text, re.I)
    if trailing:
        notes.append(trailing[1])
        text = text[:trailing.start()]
        warnings.append('Trailing preparation description retained in notes; confirm the food.')
    result['food_name'] = re.sub(r'\s+', ' ', text).strip(' .;:')
    if not result['food_name']:
        warnings.append('A food name could not be identified.')
    if original.lstrip().startswith(('{', '[')):
        warnings.append('Structured or unsupported ingredient description; correct the fields before confirming.')
    result['preparation_notes'] = '; '.join(note for note in notes if note)
    return result


def food_index(foods):
    index = {}
    for food in foods:
        index.setdefault(normalize_food_name(food.food_name), []).append(food)
    return index


def ingredient_suggestions(text, index):
    suggestions = []
    for line in ingredient_lines(text):
        parsed = parse_ingredient(line)
        matches = index.get(normalize_food_name(parsed['food_name']), [])
        suggestions.append({
            'original_text': line, 'quantity': parsed['quantity'], 'quantity_max': parsed['quantity_max'],
            'unit': parsed['unit'], 'preparation_notes': parsed['preparation_notes'],
            'food': matches[0].pk if len(matches) == 1 else None,
            'new_food_name': parsed['food_name'] if len(matches) != 1 else '',
        })
    return suggestions


def parse_quantity(value):
    text = str(value).strip()
    if len(text) > 64:
        raise ValueError('Quantity is too long.')
    for char, fraction in UNICODE_FRACTIONS.items():
        text = re.sub(r'(?<=\d)' + char, ' ' + fraction, text).replace(char, fraction)
    text = text.replace('⁄', '/')
    if not re.fullmatch(NUMBER, text):
        raise ValueError('Use a decimal, fraction, or mixed number.')
    return _number(text)
