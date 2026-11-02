# Grocery App — Development handoff (2026-11-02)

## Status: paused

Development is paused at the owner's request to preserve remaining weekly Codex compute for Kratos ERP. **Do not resume implementation until the owner requests it.** This document is the handoff for the next Grocery App session.

**Mission:** Make recipes easy to import and grocery lists easy to create and use. Preserve the existing Django application and its data rather than rebuilding.

## Repository and local environment

- GitHub: `LetsCodeNow290/grocery_app`
- Development branch: `development` (leave `master` untouched)
- Latest reported feature commit: `522d27c`
- Local checkout: `~/projects/grocery_app` (WSL Ubuntu on Windows)
- Django 5.2 LTS; local SQLite for now, PostgreSQL configuration available for future hosting
- Local app: `http://127.0.0.1:8000/`; importer: `http://127.0.0.1:8000/recipe/import/` (requires local server running)
- No dedicated TrueNAS DEV deployment yet; do not deploy publicly or to production without explicit authorization

## Completed work

| Commit | Milestone | Delivered |
| --- | --- | --- |
| `16f269e` | Foundation | Modernized Django, environment-based secrets, SQLite fallback and PostgreSQL configuration, CI, existing workflow fixes, mobile improvements |
| `7f078c3` | URL recipe importer | Schema.org Recipe JSON-LD extraction, editable review and save, source attribution, safe URL fetching |
| `cff649f` | Import reliability | Browser-copy fallback for blocked sites such as Allrecipes, saved HTML/text and JSON-LD import, preservation of original text |
| `522d27c` | Ingredient-to-grocery integration | Fraction/range/unit parsing, editable ingredient and food matching, safe reuse or creation of Food records, confirmed Ingredient relationships, grocery-list consolidation |

Codex reported **112 automated tests passing** and all four CI jobs successful for the latest milestone: https://github.com/LetsCodeNow290/grocery_app/actions/runs/41436829656 . Codex also reported successful desktop/mobile-width browser workflows and backup/migration verification preserving pre-existing SQLite values and relationships. These are Codex verification reports, not owner acceptance.

The owner personally tested the recipe import experience and said it **seems to work well**. The newer ingredient-to-grocery-list flow has **not yet received owner acceptance**.

## Current behavior and known limits

- URL import can fail when sites block automated requests (notably Allrecipes HTTP 403); use **Copy from browser**. Do not attempt CAPTCHA or anti-bot bypass.
- Imported ingredient review supports common fractions, mixed numbers, decimals, ranges, units, preparation notes, and normalized food matching.
- Ambiguous matches and unquantifiable lines require explicit review; original descriptions are retained. Confirmed ranges use the upper bound on shopping lists.
- Older imports can be processed with **Review ingredient matches for grocery lists** without replacing existing manual ingredient records.
- Existing grocery lists are **not** retroactively backfilled. Test newly confirmed recipes with a new grocery list.
- Parsing is conservative and English-oriented; complex ingredients can require corrections.
- Full details: `docs/INGREDIENT_PROCESSING.md` and `docs/RECIPE_IMPORTER.md`.

## First step when returning: owner acceptance test

1. Start the local app using `docs/DEVELOPMENT.md` if necessary.
2. Visit `http://127.0.0.1:8000/recipe/import/`.
3. Import a real recipe (URL or browser copy), inspect and correct ingredient matches, then save.
4. Add the saved recipe to a **new** grocery list.
5. Verify all foods, quantities, units, package notes and exclusions. Report any usability or parsing issues before adding new features.

## Next priorities (not authorized to start yet)

1. Faster weekly shopping: persistent next-trip list, quick-add items throughout the week, practical mobile shopping UX.
2. Multiple stores with store-specific lists, aisles and shopping order.
3. Photo and PDF recipe import using the existing review and ingredient processing pipeline.
4. Later: offline/PWA shopping, lightweight estimated inventory, recurring purchase/refill suggestions, frozen-meat thaw reminders, family Google Calendar integration.

Priorities may change based on owner acceptance feedback. Product requirements remain in `PROJECT_REQUIREMENTS.md`.

## Safeguards

- Preserve `master`, all existing recipes, grocery lists, SQLite data, media and backups.
- Continue on `development`, with tests before pushes.
- No TrueNAS, public DEV or production deployment until explicitly authorized and properly configured.
- Never modify Kratos ERP, its repositories, data or infrastructure.
- Source documentation: `PROJECT_REQUIREMENTS.md`, `docs/DEVELOPMENT.md`, `docs/DATA_RECOVERY.md`, `docs/RECIPE_IMPORTER.md`, and `docs/INGREDIENT_PROCESSING.md`.
