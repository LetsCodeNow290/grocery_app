# Online recipe importer MVP

Open <http://127.0.0.1:8000/recipe/import/> or choose **Import a recipe from a URL**
on the home page. Paste a direct public recipe URL, click **Extract recipe**,
review/edit the name, ingredients, instructions, and source, then click
**Save reviewed recipe**. Choose an existing category or leave the default
**Imported** category, which is created only when saving. Cancel saves nothing.

Two public pages verified during implementation:

- <https://www.bbcgoodfood.com/recipes/easy-pancakes>
- <https://www.spendwithpennies.com/easy-homemade-lasagna/>

Website availability and import policies can change. The importer reads Recipe
JSON-LD in the downloaded HTML. It supports arrays, embedded `@graph`/`mainEntity`
objects, Recipe type lists, textual instructions, and HowToStep/HowToSection
instructions. It selects the first complete recipe. Unsupported ingredient
objects retain their JSON text for manual correction. It does not execute
JavaScript, log in, solve bot challenges, or scrape arbitrary visible-page layouts.
A blocked site, missing/incomplete recipe, or failed download displays an error
without saving a recipe.

## Ingredients and grocery lists

All ingredient lines and quantities remain editable text in `Recipe.ingredient_text`.
The importer deliberately does not guess numeric amounts, units, or food matches.
The saved recipe shows the text and a link to **add foods and quantities** using
the existing ingredient workflow. That page shows the imported text as a reference.
Once foods/quantities are entered, the existing recipe-to-grocery-list workflow
works normally. Text alone does not generate shopping items. This is the main
MVP limitation; no advanced ingredient matching is included.

Source attribution is stored in `Recipe.source_url`. Both fields can be edited
through the existing recipe update form. No remote images are fetched. Photo/PDF
importing and AI extraction are outside this feature.

## Local upgrade and data preservation

The additive recipe migration `0003` adds the two optional text/source fields;
it retains recipes, ingredients, foods, and grocery-list relationships. After
backing up the active SQLite database, apply it with:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test
```

The implementation run backed up the active SQLite database into ignored
`backups/` before migrating. No historical fixture or database is loaded. If the
local server was started with `--noreload`, restart the grocery-app tmux session
after pulling code/migrating. Keep `.env` pointing to the existing local SQLite
file; do not replace it with a new file for this feature.

## Fetch safety and tests

Only HTTP/HTTPS on their standard ports is accepted, without URL credentials.
Every destination, including each redirect, must resolve exclusively to public
addresses. Private, loopback, link-local, multicast, reserved, shared-address,
site-local, mapped/transition IPv6, and platform metadata addresses are blocked.
TCP connects directly to the checked DNS results, avoiding a second resolution;
HTTPS retains the original hostname for SNI and certificate validation. System
HTTP proxies are not used. HTTPS-to-HTTP redirects are rejected.

Downloads allow at most three redirects and 2 MB of uncompressed HTML, use
10-second socket timeouts and a 25-second elapsed deadline between operations,
and never fetch linked contexts/scripts/images. DNS resolution uses the operating
system resolver and its timeout. Sites that insist on compressed content are
reported as unsupported. Forms retain Django CSRF protection and render source
text with HTML escaping.

The full suite currently has 64 tests, including focused mocked network/extraction
and review/save tests, manual conversion into grocery items, and a migration
regression test that retains old recipe/ingredient/list links. Automated tests
make no requests to external recipe sites. Live local HTTP verification covers
extraction into review; saving is exercised against disposable test databases.
