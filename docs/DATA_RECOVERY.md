# Preserve existing data before modernization

No existing database has been migrated or overwritten by this foundation. No
SQLite database is tracked in this checkout. Both JSON backups, `InitialData/`,
and media files are preserved as received. Do not treat a successful fresh test
migration as proof an old installation is ready to migrate.

## Inventory of committed backups

| Backup | Catalog | Recipes/ingredients | Shopping data | Compatibility |
| --- | --- | --- | --- | --- |
| `db.json` | 110 foods, 41 books, 27 food categories, 19 recipe categories, 18 aisles | 2 recipes, 20 ingredients | None | Legacy MeasuringUnit model; ingredient units are numeric foreign keys |
| `julybackup.json` | 3 foods, 3 books, 8 food categories, 6 recipe categories, 11 aisles | 3 recipes, 2 ingredients | 16 lists, 3 chosen items | Older recipe/ingredient relations and numeric units; includes auth/session/admin metadata |

They are different snapshots, not successive fixtures to load together. Their
primary keys can overlap with unrelated records. Neither is known to be the
owner's authoritative current dataset. **Do not run `loaddata` on these files
against an active database.** They need an explicit, verified conversion first.
The original `initialize_data.py` and `food_fix.py` are ad hoc legacy utilities,
not a supported setup or recovery process.

## Safe rehearsal procedure

1. Find the original database, application version, and full `media/` directory on
   the owner's machine. Make an immutable backup of the stopped SQLite database
   (or use SQLite's backup API); for PostgreSQL take `pg_dump --format=custom`.
   Copy media separately. Keep backup copies out of Git. Record counts and retain
   the original installation for comparison.
2. Work on a separate database and copied media only. Inspect `django_migrations`,
   database tables, and foreign keys. Some historical migration names exist only
   as bytecode in the original repository; do not delete migration records,
   blindly fake migrations, or regenerate initial migrations to hide differences.
3. If the database matches the checked-in migration chain, rehearse the Django
   upgrade and `migrate --plan` on that copy. The list join table should be
   `groceries_grocerylistitems`, with `grocery_list_id` and `choose_item_id`. This
   foundation deliberately keeps that schema.
4. For older JSON snapshots, write a separate conversion that reads without
   modifying the original. Resolve numeric units from each snapshot's
   `components.measuringunit` rows into the current unit strings. Preserve
   unsupported unit labels in a conversion report instead of guessing. Rebuild
   legacy `linked_recipe` relationships only when the association is unambiguous;
   detect orphan IDs and duplicate names. Report every dropped/changed field and
   retain a complete archival copy. Do not use `--ignorenonexistent`: it would
   hide lost relationships and units.
5. For a current-schema database export, transfer application data (including
   `groceries.GroceryListItems`) into a fresh PostgreSQL database. A Django dump
   with natural foreign keys can avoid built-in permission/content-type ID
   collisions; decide separately whether users/admin/session data belongs in the
   transfer. Inspect the export before loading; do not combine snapshots.
6. Compare per-model counts and primary keys, recipe-to-ingredient links,
   food/category/aisle links, grocery item/recipe membership, quantities/units,
   dates, and media files. Test list display/export/editing and representative
   recipes on the recovered copy. Reset/check database sequences when using a
   custom SQL import. Keep an exception report and reconcile every discrepancy.
7. Only after that rehearsal should a cutover be planned. Changing the live
   production application requires explicit owner authorization. Never overwrite
   the source database or remove the backups.

The old hardcoded Django key is publicly compromised. Use a newly generated key;
old signed sessions should be invalidated. The historical backup contains account
and session records; review credentials before any future hosted environment and
do not publish backup content in logs or reports. This work does not rewrite Git
history or remove the owner's archives.
