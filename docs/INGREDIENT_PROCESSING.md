# Imported ingredients → grocery lists

Open <http://127.0.0.1:8000/recipe/import/> and import a URL or use Copy from
browser. The existing review form now includes **Ingredients for grocery lists**.

- Decimal amounts, fractions (`1/2`, `½`), mixed numbers (`1 1/2`, `1½`), and
  ranges (`1–2`, `1/2 to 3/4`) are parsed deterministically, without an AI API.
- Common US, metric, count, and container unit abbreviations are recognized.
  Ingredient cards retain the original line and editable preparation notes.
- Foods match by case, whitespace, punctuation, accents, and a conservative list
  of common plurals. Descriptive variants such as salted/unsalted butter stay
  distinct. There is no fuzzy or semantic matching.
- A unique normalized match is selected automatically. Ambiguous existing
  duplicates require an explicit selection and are not merged or deleted.
- Missing foods have their proposed names filled in. Saving creates/reuses them;
  optional category/aisle selectors are available. Defaults are Imported and
  Unassigned. Existing food details are never overwritten by these controls.
- Flagged lines require **I checked the flagged details**. Corrected amounts may
  also be entered as fractions. For ranges, both bounds are retained and the
  grocery list uses the upper bound, as stated before confirmation.
- If a line cannot reasonably be quantified, choose **Keep as reference only**.
  The original line and notes remain on the recipe, clearly marked as excluded
  from shopping. An unresolved line cannot disappear through an omitted form row.

**Save reviewed recipe** atomically saves the recipe, foods, and Ingredient
relationships. Use **Add recipe to grocery list** on the saved recipe. There is
no second round of manual ingredient entry. Reference-only exclusions produce a
shopping reminder.

If you change the original ingredient text or split a compound line, select
**Refresh ingredient suggestions**, then review the refreshed rows before saving.
Quantity/unit/food corrections can be made directly on a card without editing the
original line. Imported text is also supplied in Notes unless a browser copy is
already present. Imported descriptions and confirmed per-ingredient descriptions
remain available on the saved recipe.

## Recipes already in the database

For a prior import with text but no structured ingredients, open its detail page
and choose **Review ingredient matches for grocery lists**. This uses the same
parser, matching controls, and save service. Existing manual/confirmed Ingredient
rows are never replaced, and original recipe fields remain unchanged. Recipes
with unprocessed text are blocked from being added as an empty shopping recipe.

Processing a recipe does not retroactively change grocery lists. A recipe already
on an old list is still protected against duplicate addition; use a new list to
shop the newly confirmed ingredients. Existing confirmed ingredients are not
bulk-reparsed or rewritten by this feature.

## Consolidation

The same Food record can consolidate within US customary volume (tsp/tbsp/cup/
fluid ounce/pint/quart/gallon), US weight (oz/lb), metric weight (g/kg), or metric
volume (ml/litre). These families remain separate: no weight/volume or US/metric
cup conversion guesses. Counts and container units combine only with the same
unit. The existing item's unit is retained when adding compatible amounts.

Preparation/package notes are retained on shopping items, display, and CSV. Rows
with different notes stay separate: a 14-ounce can and a 28-ounce can are not
silently merged. Separate Food IDs also stay separate, even if their labels are
identical. Legacy compatible rows consolidate in display/export without deleting
or rewriting their stored rows. Shared shopping items are copied before changes.

## Migration and validation

The active local database remains SQLite. An ignored private backup was created
before migration, and every pre-existing application-table value and relationship
was compared afterward and retained. Migrations add optional ingredient metadata,
reference-only metadata, a nullable unique import-food key, shopping notes, and
unit choices. They use reversible Django operations; no data-deduplication or
history-rewriting migration is included. Restore the backup rather than reversing
schema changes on valuable data; a reversal removes the newly introduced metadata.

Existing food rows keep NULL import keys. New import-created rows use normalized
unique keys to prevent duplicate import creation; matching also searches existing
names. Renaming a keyed food releases its old key without changing other foods.

The full suite covers parsing and warnings, matching and ambiguity, inline food
creation/reuse, form integrity, atomic rollback, original description retention,
ranges/reference-only lines, old-import processing, existing manual data, both
shopping entry points, and compatible/incompatible consolidation. Import fetch
and browser-copy security tests remain in the suite.

## Limits and owner acceptance

Parsing is conservative and English-oriented. Compound alternatives, unfamiliar
measurements, missing quantities, and structured descriptions can need correction.
No nutritional/density calculations, serving-size scaling, or historical duplicate
merging is performed. Review supports up to 200 nonempty ingredient lines; an
oversized recipe is rejected rather than truncated.

Try one real recipe through URL import and one through Copy from browser. Check a
fraction, a range, package sizes, and an unquantified line. Correct a match/create
a missing food, save, then add it to a new grocery list and inspect quantities and
CSV. Also check the cards on your actual phone/browser; automated narrow-viewport
checks do not substitute for physical-device acceptance.

Implementation verification: **112 automated tests pass**. In an isolated SQLite
copy, Chromium at 1280 px, 390 px, and 320 px completed browser import → matching
review → save → Add Recipe to Grocery List, without manual ingredient re-entry.
Three recipes consolidated to 4.5 cups flour, 9 tablespoons butter, and 6 teaspoons
salt (the confirmed upper ranges); the reference-only oil remained off the list.
The recipe-detail markup was corrected after this test exposed overlapping mobile
content. No browser-test recipes were added to the active local database.
