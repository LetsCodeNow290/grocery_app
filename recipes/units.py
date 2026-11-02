"""Shared recipe/shopping units. Separate families prevent density or cup-size guesses."""
from fractions import Fraction

UNITS = [(value, value) for value in (
    'teaspoon(s)', 'TABLESPOON(s)', 'cup(s)', 'pint(s)', 'quart(s)', 'gallon(s)',
    'ounce(s)', 'pound(s)', 'fluid ounce(s)', 'gram(s)', 'kilogram(s)', 'milliliter(s)', 'liter(s)',
    'item(s)', 'clove(s)', 'slice(s)', 'piece(s)', 'can(s)', 'package(s)', 'bunch(es)',
    'pinch(es)', 'dash(es)', 'stick(s)', 'sprig(s)', 'jar(s)', 'bottle(s)', 'bag(s)',
    'vegetable or fruit', 'other')]
ALIASES = {}
for unit, words in {
    'teaspoon(s)': 't tsp tsps teaspoon teaspoons',
    'TABLESPOON(s)': 'tbsp tbs tbsps tablespoon tablespoons',
    'cup(s)': 'c cup cups', 'pint(s)': 'pt pts pint pints',
    'quart(s)': 'qt qts quart quarts', 'gallon(s)': 'gal gals gallon gallons',
    'ounce(s)': 'oz ounce ounces', 'pound(s)': 'lb lbs pound pounds',
    'gram(s)': 'g gr gram grams', 'kilogram(s)': 'kg kgs kilogram kilograms',
    'milliliter(s)': 'ml mls milliliter milliliters millilitre millilitres',
    'liter(s)': 'l liter liters litre litres', 'item(s)': 'item items',
    'clove(s)': 'clove cloves', 'slice(s)': 'slice slices', 'piece(s)': 'piece pieces',
    'can(s)': 'can cans tin tins', 'package(s)': 'package packages pkg pkgs packet packets',
    'bunch(es)': 'bunch bunches', 'pinch(es)': 'pinch pinches', 'dash(es)': 'dash dashes',
    'stick(s)': 'stick sticks', 'sprig(s)': 'sprig sprigs', 'jar(s)': 'jar jars',
    'bottle(s)': 'bottle bottles', 'bag(s)': 'bag bags',
}.items():
    for word in words.split():
        ALIASES[word] = unit

FAMILIES = (
    {'teaspoon(s)': 1, 'TABLESPOON(s)': 3, 'cup(s)': 48, 'pint(s)': 96,
     'quart(s)': 192, 'gallon(s)': 768, 'fluid ounce(s)': 6},  # US customary volume only.
    {'ounce(s)': 1, 'pound(s)': 16},
    {'gram(s)': 1, 'kilogram(s)': 1000},
    {'milliliter(s)': 1, 'liter(s)': 1000},
)


def conversion_factor(source, target):
    if source == target:
        return Fraction(1)
    for family in FAMILIES:
        if source in family and target in family:
            return Fraction(family[source], family[target])
    return None


def add_quantities(existing, added, factor=Fraction(1)):
    return float(Fraction(str(existing)) + Fraction(str(added)) * factor)
