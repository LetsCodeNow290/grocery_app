# Grocery App requirements

## Mission

Make recipe importing and grocery shopping faster and easier. Revive the existing
Django application and preserve useful functionality and all existing recipe,
ingredient, food, and grocery-list data. Avoid an unnecessary rebuild.

## Phase 1 priorities

1. Import recipes easily from photographs, PDFs, and recipe website URLs. Extract
   a draft name, ingredients, quantities, units, and instructions. Let the user
   review and correct the draft before saving, retain source attribution, and
   report unsupported sources or extraction failures clearly. Support photographed
   pages and scanned PDFs as well as PDFs containing text. Map imported ingredients
   to existing foods without silently duplicating or overwriting them.
2. Create and manage grocery lists easily, including adding items throughout the
   week, generating lists from recipes, changing quantities, removing items, and
   exporting a useful shopping list. Combine the same food/unit; keep incompatible
   units separate. Re-submitting a recipe must not double quantities accidentally.
3. Support multiple stores with separate grocery lists and store-specific aisles.
   Preserve the existing global aisles during the eventual store migration. Show
   unassigned foods clearly instead of failing when an aisle is missing.

Acceptance for an operational Phase 1 includes end-to-end tests for all three
import sources, review/correction before saving, recipe-to-list generation,
weekly additions, and store-specific shopping order on a mobile screen.

## Later phases

- Lightweight estimated inventory, with simple corrections rather than mandatory
  precise stock tracking.
- Future Google Calendar integration for planning meals and shopping.
- Mobile-friendly design now, and eventual offline grocery lists with a clear
  synchronization/conflict strategy.

## Technical and delivery requirements

- Supported Django and compatible dependencies; automated regression tests.
- PostgreSQL is the intended database. SQLite is an explicit local/test fallback.
- Secrets and database credentials come from environment variables; `.env` is
  supported for local development and excluded from Git. Never reuse publicly
  committed secrets.
- Retain migration history and existing data. Rehearse any legacy database/data
  conversion on a backed-up copy and verify counts, links, and media first.
- Eventual self-hosting on TrueNAS. Do not deploy there yet: the application's
  DEV environment has not been established.
- Continuous DEV deployment of tested features is the target once a dedicated DEV
  environment exists. CI is a prerequisite, not a deployment environment.
- Production deployment always requires explicit owner authorization.
- Development inspection, edits, tests, commits, and pushes may proceed without
  routine approval checkpoints. Develop on `development`; preserve `master`.
- Never modify Kratos ERP, its databases, or its infrastructure. No destructive
  data operations or rewriting published Git history.

## Foundation delivery status

The foundation restores and tests the existing workflows on modern Django, adds
PostgreSQL configuration and CI, and documents setup and data recovery. The online
recipe importer MVP now extracts Recipe JSON-LD into an editable
review form and preserves ingredient text. Deterministic ingredient processing
now proposes quantities/units and normalized food matches, with editable review
and saving directly into grocery-list-ready Ingredient relationships. Photo/PDF importing, store-specific lists/aisles, offline support, and DEV
hosting are still to be implemented; this is not the completed Phase 1.
See `docs/REPOSITORY_ASSESSMENT.md` for findings and the next implementation steps.
