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

Import review now parses ingredient lines, matches existing foods, and lets you
correct amounts/units or create missing foods before saving confirmed Ingredient
relationships. Original text is retained. Uncertain lines require confirmation
or an explicit reference-only choice; ranges use the confirmed upper amount for
shopping. See [INGREDIENT_PROCESSING.md](INGREDIENT_PROCESSING.md) for the workflow,
prior-import processing, consolidation rules, and limits.

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

The initial URL-import suite had 64 tests, including focused mocked network/extraction
and review/save tests, manual conversion into grocery items, and a migration
regression test that retains old recipe/ingredient/list links. Automated tests
make no requests to external recipe sites. Live local HTTP verification covers
extraction into review; saving is exercised against disposable test databases.

## When a website blocks imports: copy from your browser

The URL importer still uses its original fetch security checks. For HTTP 401, 403,
or 429, it now explains that automatic downloading was blocked and points to
**Copy from browser**. Any fetch/extraction failure opens that section with the
original recipe URL already filled in. You can also open it directly without
trying a server download first.

1. Open <http://127.0.0.1:8000/recipe/import/>. Expand **Copy from browser** if it
   is not already open.
2. Enter/keep the recipe page URL. **Open recipe page in a new tab** opens it in
   your own browser; it does not start another server download. If JavaScript is
   disabled, open the URL manually instead.
3. Use the website's **Jump to recipe** button if available. On desktop, select
   and copy from the recipe title through the last direction. On a phone, press
   and hold the text, adjust the selection handles, and choose **Copy**. Keep
   the **Ingredients** and **Directions/Instructions** headings when available.
4. Return to the app and paste into **Recipe copied from your browser**.
5. Select **Review copied recipe**, correct the proposed fields, and save with
   the existing **Save reviewed recipe** button. Nothing is saved before review.

Heading recognition supports Ingredients followed by Directions, Instructions,
Method, or Preparation. It makes section suggestions without promising to understand every page layout.
Ingredient matching then processes those lines in the shared review form. The complete plain-text copy is
kept in **Notes / original browser copy**, including preambles and unknown
sections. If headings are missing, all text remains in Instructions and Notes;
enter a title and move ingredient lines into Ingredients before saving. Notes
can be edited/removed during review or through the existing recipe update page.
Source attribution and ingredient text retain the same existing model fields.

For desktop users, **Saved page or structured data** also accepts a UTF-8 `.html`,
`.htm`, `.json`, or `.txt` file (up to 2 MB), or pasted Recipe JSON-LD/page HTML.
Use your browser's **Save page → HTML only** option. Choose either pasted text or
one file. HTML/JSON uses the same Recipe JSON-LD extractor as URL imports; page
scripts, linked contexts, images, and redirects are never executed or fetched.
Files are not retained in media storage. Visible text/pasted text files are
limited to 100,000 characters so the full copy remains editable in review.

This fallback consumes only the content you supply: it makes no network request,
does not import browser cookies, and does not change the remote website's access
controls. Normal browser access is still necessary to copy or save that page.
There are no CAPTCHA solvers, headless downloads of blocked sites, proxy rotation,
identity rotation, or alternate endpoint probes. This increment needs no database
migration and does not replace the active SQLite file.

### Allrecipes investigation

For the reported URL, <https://www.allrecipes.com/recipe/275590/marry-me-chicken>,
standard direct requests from this WSL environment returned HTTP 403 with a
`Server: cloudflare` response. The trailing-slash URL and a single ordinary
browser-header request also returned 403; a normal Windows `Invoke-WebRequest`
request returned 403 as well. No structured data could be obtained through those
requests. The exact blocking rule cannot be determined from a 403 response.
Changing production request headers would not fix the observed failure, so the
identifiable importer User-Agent and all fetch restrictions remain intact.

### Reliability validation

The suite now has 84 tests, including the original 64 tests plus 20 browser-copy
regressions. They cover 403 handoff/source prefill, text/HTML/JSON-LD review and
save, unmatched text retention, original-copy notes, file/type/encoding/size
errors, CSRF, escaping, source validation, and the absence of network calls in
the fallback. Existing fetch tests also cover 401/429 guidance.

Local HTTP verification reproduced Allrecipes' 403 and checked that it opens the
fallback with the source intact; browser-copy review and the existing automatic
BBC Good Food import still worked. Chromium checks exercised copy → review →
save on desktop (1280 px) and mobile viewports (390 px and 320 px), plus a saved
HTML upload, using a separate SQLite copy. Source URLs, fractions, and complete
copy notes persisted; no horizontal overflow or page script errors occurred.
Those checks use only the local application, not automated browsing of blocked
recipe sites. They are viewport tests, not physical iOS/Android device testing.
The active SQLite database did not receive synthetic browser-test recipes.
