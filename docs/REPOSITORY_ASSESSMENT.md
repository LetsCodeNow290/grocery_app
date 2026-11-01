# Foundation assessment

## Existing application

The default branch is `master` (starting commit `520b074`). `development` was
created from `origin/master`; the original branch and published history are
preserved. This is a Django application with server-rendered Bootstrap 4 templates,
not a project needing a frontend or database rewrite.

| Area | Existing implementation | Foundation decision |
| --- | --- | --- |
| Catalog | `components`: Aisle, FoodCategory, Food, RecipeCategory, RecipeBook; forms and CRUD views | Preserve models, primary keys, and screens |
| Recipes | `recipes`: Recipe, Ingredient, image/instructions/rating/book, many-to-many ingredients, manual entry, filtering | Preserve; fix uploads, missing-image saves, ingredient validation, food filter, pagination |
| Shopping | `groceries`: dated GroceryList, ChooseItem, list recipes/items, recipe expansion, manual entries, edit/remove, CSV | Preserve; fix validation, repeated saves, fractional CSV, list-scoped edits and recipe expansion |
| Home | `home`: navigation and database-management landing pages; no domain models | Preserve; responsive wrapping for shared page columns |
| Import | Recipe/book image fields and manual ingredient entry only | No OCR, PDF extraction, URL fetching, or import review workflow exists |
| Tests | Empty placeholders; a recipe setup class with no test methods | Replace with executable regression coverage |
| Runtime | Django 3.0.5, Python 3.7 bytecode, old dependencies, SQLite, hardcoded secret/debug/wildcard hosts | Django 5.2 LTS, compatible dependencies, PostgreSQL default, environment settings |

Templates remain in `templates/{components,recipes,groceries,home}`. CSS lives in
`home/static/home/main.css`. Recipe uploads now retain original dimensions rather
than modifying the user's source image while saving. Saving records no longer
requires the placeholder image files to exist.

Source migrations comprise `components/0001`, `recipes/0001–0002`,
`groceries/0001–0003`, and Django's built-in migrations. Old tracked bytecode
mentioned additional historical migrations but is not authoritative source.
The model had lost `GroceryListItems`, although migration 0001 still creates it.
Restoring that explicit through model keeps `groceries_grocerylistitems` and its
existing links; no new schema migrations are needed. Automatic checks confirm
model/migration agreement. Existing installations with different migration
histories still require rehearsal on a copy; see `DATA_RECOVERY.md`.

## Shopping behavior after fixes

Both recipe entry points use the same atomic service and add ingredient rows.
Adding a recipe already on the list is a no-op for quantities. To buy more,
edit quantities explicitly. Foods merge only with the same unit; there is no
implicit unit conversion. New items aggregate into existing food/unit rows.
Legacy duplicate rows remain intact and are combined in display/export.

Missing aisles display as Unassigned. Rows sort naturally by aisle then food.
Quantity changes/removals apply only to the selected list. Shared legacy item
rows are copied before quantity changes and retained when another list references
them. The nonfunctional remove-by-recipe form was removed: manually editing items
means subtracting a recipe would require provenance tracking to be reliable.
Recipe references continue to display on the list.

## Validation

Local verification uses Python 3.14.4, the versions in `requirements.lock`, and
32 regression tests passing on SQLite and PostgreSQL 16. Tests cover catalog page
rendering and food CRUD/duplicates, recipe creation/upload/update/delete and
fractional ingredient entry, food filtering, list creation/validation, both
recipe-to-list paths, duplicate submission, manual quantity merging, aisle order,
CSV fractions, edit/remove validation, list isolation, shared legacy items, and
404 responses. PostgreSQL tests run in a new grocery-app-only container using an
ephemeral local port; no existing application database or infrastructure is used.

CI adds Python 3.12/3.14 × SQLite/PostgreSQL runs plus checks, fresh migration, and
static collection. The local Python 3.12 combination awaits CI. Automated template
rendering is not browser/device acceptance testing. No old live database was
available, so migration of the owner's actual installation is not yet verified.

## Next increments to reach operational Phase 1

1. Locate and back up the authoritative database and uploaded media. Inspect its
   migration history, convert legacy data on a copy if needed, and reconcile
   counts, recipe ingredients, list membership, quantities, and media references.
2. Implement a reviewable import draft: source URL/file, raw extracted text,
   normalized ingredients with food matching, editable quantities/units, and
   instructions. Save confirmed drafts transactionally into the existing models.
3. Add URL import from Recipe structured data with bounded fetches, safe public
   URL validation (including redirects/address resolution), timeouts, and clear
   unsupported-site errors. Do not silently download arbitrary network resources.
4. Add photo OCR and PDF text extraction/OCR fallback behind a replaceable
   extraction interface. Decide local vs. hosted extraction based on privacy,
   accuracy, and operating cost. Keep originals; enforce type/size/page limits.
   Test each import source and failures through review → recipe → grocery list.
5. Add Store and store-owned aisles/list selection with an additive, tested
   migration. Map current global aisles to a legacy/default store without losing
   existing data. Consider food-to-store aisle mappings because a food can appear
   in several stores. Add faster food search/quick entry during the week.
6. Complete mobile shopping acceptance tests and evaluate checked-off items and
   serving-size scaling. Keep offline synchronization and estimated inventory as
   later phases.
7. Establish a separate authenticated DEV environment, backups, media/static
   hosting, health checks, and a CI-gated continuous DEV deployment. No DEV target
   or credentials have been configured. Production requires explicit approval;
   TrueNAS deployment has not been performed.
