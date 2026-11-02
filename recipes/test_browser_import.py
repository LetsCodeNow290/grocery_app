import json
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from .forms import RecipeBrowserImportForm
from .importer import MAX_BYTES, RecipeImportError, extract_browser_content
from .models import Recipe

SOURCE = 'https://www.allrecipes.com/recipe/275590/marry-me-chicken'
# Invented recipe text with headings commonly copied from recipe websites.
COPIED = '''Browser skillet meal
Preparation: 15 minutes

Ingredients
1 ½ cups chopped vegetables
Salt, to taste

Directions
1. Warm the skillet.
2. Stir and serve.

Cook's note
Add a squeeze of lemon if desired.'''
STRUCTURED = {'@type': 'Recipe', 'name': 'Browser skillet meal',
              'recipeIngredient': ['1 ½ cups chopped vegetables', 'Salt, to taste'],
              'recipeInstructions': [{'@type': 'HowToStep', 'text': 'Warm the skillet.'}]}


class BrowserExtractionTests(SimpleTestCase):
    def test_common_headings_preserve_quantities_and_complete_original(self):
        draft = extract_browser_content(COPIED)
        self.assertEqual(draft['recipe_name'], 'Browser skillet meal')
        self.assertEqual(draft['ingredient_text'], '1 ½ cups chopped vegetables\nSalt, to taste')
        self.assertIn("Cook's note", draft['recipe_instructions'])
        self.assertIn('Preparation: 15 minutes', draft['comments'])
        self.assertEqual(draft['comments'], COPIED)

    def test_instruction_heading_variations(self):
        for heading in ['Instructions', 'METHOD:', 'Preparation', '  directions  ']:
            with self.subTest(heading=heading):
                draft = extract_browser_content(COPIED.replace('Directions', heading))
                self.assertIn('Warm the skillet.', draft['recipe_instructions'])
                self.assertIn('1 ½ cups', draft['ingredient_text'])

    def test_unrecognized_text_is_retained_for_manual_review(self):
        text = 'A recipe without headings\nSome uncertain quantities\nCook until ready.'
        draft = extract_browser_content(text)
        self.assertEqual(draft['recipe_name'], '')
        self.assertEqual(draft['ingredient_text'], '')
        self.assertEqual(draft['recipe_instructions'], text)
        self.assertEqual(draft['comments'], text)

    def test_heading_like_words_inside_ingredient_line_do_not_split(self):
        draft = extract_browser_content(COPIED.replace('Salt, to taste', 'Salt for preparation, to taste'))
        self.assertIn('Salt for preparation', draft['ingredient_text'])

    def test_supplied_json_ld_and_html_use_existing_extraction(self):
        raw = json.dumps({'@graph': [STRUCTURED]}, ensure_ascii=False)
        for content in [raw, '\ufeff' + raw,
                        '<html><script type="application/ld+json">' + raw + '</script></html>']:
            with self.subTest(content=content[:20]):
                draft = extract_browser_content(content)
                self.assertEqual(draft['recipe_name'], 'Browser skillet meal')
                self.assertIn('1 ½ cups', draft['ingredient_text'])
                self.assertEqual(draft['recipe_instructions'], 'Warm the skillet.')

    def test_raw_json_with_html_fragments_is_parsed_as_json_first(self):
        raw = dict(STRUCTURED, recipeInstructions='Warm the skillet. </script>Stir and serve.')
        draft = extract_browser_content(json.dumps(raw))
        self.assertEqual(draft['recipe_instructions'], 'Warm the skillet. Stir and serve.')

    def test_markup_contexts_and_scripts_are_not_fetched(self):
        raw = dict(STRUCTURED, **{'@context': 'http://127.0.0.1/context'})
        content = ('<html><script src="http://127.0.0.1/execute.js"></script>'
                   '<iframe src="http://169.254.169.254/"></iframe>'
                   '<script type="application/ld+json">' + json.dumps(raw) + '</script></html>')
        with patch('recipes.importer.socket.getaddrinfo') as dns, patch('recipes.importer.fetch_html') as fetch:
            draft = extract_browser_content(content)
        self.assertEqual(draft['recipe_name'], 'Browser skillet meal')
        dns.assert_not_called()
        fetch.assert_not_called()

    def test_invalid_structured_content_is_an_error_not_a_silent_text_guess(self):
        for content in ['{"@type": "Recipe", broken}', '<html>No Recipe JSON-LD</html>']:
            with self.subTest(content=content), self.assertRaises(RecipeImportError):
                extract_browser_content(content)

    def test_text_and_byte_limits(self):
        with self.assertRaisesRegex(RecipeImportError, '100,000'):
            extract_browser_content('x' * 100001)
        with self.assertRaisesRegex(RecipeImportError, '2 MB'):
            extract_browser_content('x' * (MAX_BYTES + 1))


class BrowserFormTests(SimpleTestCase):
    def test_exactly_one_content_source_required(self):
        for data, files in [({'source_url': SOURCE}, None),
                            ({'source_url': SOURCE, 'content': COPIED},
                             {'content_file': SimpleUploadedFile('recipe.txt', COPIED.encode())})]:
            form = RecipeBrowserImportForm(data, files)
            self.assertFalse(form.is_valid())
            self.assertIn('Paste recipe content or choose a saved file', str(form.errors))

    def test_uploaded_files_are_bounded_text_only(self):
        for name, content, message in [
            ('recipe.html', b'x' * (MAX_BYTES + 1), 'maximum 2 MB'),
            ('recipe.pdf', b'%PDF', 'Choose an HTML'),
            ('recipe.txt', b'\xff\xfe', 'UTF-8'),
            ('recipe.txt', b'   ', 'empty')]:
            with self.subTest(name=name, message=message):
                form = RecipeBrowserImportForm({'source_url': SOURCE},
                                                {'content_file': SimpleUploadedFile(name, content)})
                self.assertFalse(form.is_valid())
                self.assertIn(message, str(form.errors))

    def test_source_validation_requires_attribution_without_credentials(self):
        for source in ['', 'javascript:alert(1)', 'file:///etc/passwd', 'ftp://example.com/recipe',
                       'https://user:secret@example.com/recipe']:
            with self.subTest(source=source):
                form = RecipeBrowserImportForm({'source_url': source, 'content': COPIED})
                self.assertFalse(form.is_valid())
                self.assertIn('source_url', form.errors)


class BrowserWorkflowTests(TestCase):
    def test_get_offers_mobile_and_desktop_instructions(self):
        response = self.client.get(reverse('recipe_import'))
        self.assertContains(response, 'Copy from browser')
        self.assertContains(response, 'On a phone')
        self.assertContains(response, 'Review copied recipe')
        self.assertContains(response, 'multipart/form-data')
        self.assertContains(response, 'browser_import.js')

    @patch('recipes.importer.import_url', side_effect=RecipeImportError(
        'The website blocked automatic downloading (HTTP 403). Use Copy from browser below.'))
    def test_403_opens_fallback_and_prefills_exact_source(self, fetch):
        response = self.client.post(reverse('recipe_import'), {'url': SOURCE})
        self.assertContains(response, 'HTTP 403')
        self.assertTrue(response.context['browser_open'])
        self.assertEqual(response.context['browser_form']['source_url'].value(), SOURCE)
        self.assertFalse(Recipe.objects.exists())
        fetch.assert_called_once_with(SOURCE)

    def test_plain_copy_review_edit_and_save_preserves_source_and_original(self):
        with patch('recipes.importer.import_url') as fetch, \
                patch('recipes.importer.socket.getaddrinfo') as dns:
            response = self.client.post(reverse('recipe_import'), {
                'step': 'browser', 'source_url': SOURCE, 'content': COPIED})
        fetch.assert_not_called()
        dns.assert_not_called()
        self.assertContains(response, 'Save reviewed recipe')
        self.assertContains(response, 'complete browser copy')
        self.assertFalse(Recipe.objects.exists())
        draft = response.context['review_form'].initial
        self.assertEqual(draft['source_url'], SOURCE)
        data = {**draft, 'step': 'save', 'recipe_category': '', 'recipe_name': 'Reviewed skillet meal'}
        self.client.post(reverse('recipe_import'), data)
        saved = Recipe.objects.get()
        self.assertEqual(saved.recipe_name, 'Reviewed Skillet Meal')
        self.assertEqual(saved.source_url, SOURCE)
        self.assertIn('1 ½ cups', saved.ingredient_text)
        self.assertEqual(saved.comments, COPIED)
        detail = self.client.get(reverse('recipe_detail', args=[saved.pk]))
        self.assertContains(detail, 'Notes / original browser copy')
        self.assertContains(detail, 'Preparation: 15 minutes')
        self.assertContains(detail, SOURCE)

    def test_missing_headings_produce_editable_review_and_clear_hint(self):
        text = 'Copied text without section headings'
        response = self.client.post(reverse('recipe_import'), {
            'step': 'browser', 'source_url': SOURCE, 'content': text})
        self.assertContains(response, 'headings were not recognized')
        draft = response.context['review_form'].initial
        self.assertEqual(draft['recipe_instructions'], text)
        response = self.client.post(reverse('recipe_import'), {**draft, 'step': 'save'})
        self.assertTrue(response.context['review_form'].errors)
        self.assertContains(response, text)
        self.assertFalse(Recipe.objects.exists())

    def test_saved_html_upload_uses_same_review(self):
        raw = '<html><script type="application/ld+json">' + json.dumps(STRUCTURED) + '</script></html>'
        with patch('recipes.importer.fetch_html') as fetch:
            response = self.client.post(reverse('recipe_import'), {
                'step': 'browser', 'source_url': SOURCE,
                'content_file': SimpleUploadedFile('recipe.html', raw.encode(), content_type='text/html')})
        fetch.assert_not_called()
        self.assertContains(response, 'Save reviewed recipe')
        self.assertEqual(response.context['review_form'].initial['recipe_name'], STRUCTURED['name'])
        self.assertFalse(Recipe.objects.exists())

    def test_empty_and_malformed_input_stays_on_fallback_without_writes(self):
        for content in ['', '<html>No structured recipe here</html>']:
            with self.subTest(content=content):
                response = self.client.post(reverse('recipe_import'), {
                    'step': 'browser', 'source_url': SOURCE, 'content': content})
                self.assertIsNone(response.context['review_form'])
                self.assertTrue(response.context['browser_form'].errors)
                self.assertTrue(response.context['browser_open'])
                self.assertEqual(response.context['browser_form']['source_url'].value(), SOURCE)
                self.assertFalse(Recipe.objects.exists())

    def test_browser_copy_and_file_upload_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for data in [{'step': 'browser', 'source_url': SOURCE, 'content': COPIED},
                     {'step': 'browser', 'source_url': SOURCE,
                      'content_file': SimpleUploadedFile('recipe.txt', COPIED.encode())}]:
            self.assertEqual(client.post(reverse('recipe_import'), data).status_code, 403)

    def test_untrusted_copy_is_escaped_in_review_and_notes(self):
        text = COPIED + '\n<img src=x onerror=alert(1)>'
        response = self.client.post(reverse('recipe_import'), {
            'step': 'browser', 'source_url': SOURCE, 'content': text})
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')
        self.client.post(reverse('recipe_import'), {
            **response.context['review_form'].initial, 'step': 'save'})
        detail = self.client.get(reverse('recipe_detail', args=[Recipe.objects.get().pk]))
        self.assertContains(detail, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(detail, '<img src=x onerror=alert(1)>')
