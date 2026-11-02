import io
import json
import socket
import ssl
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse
from components.models import Food, FoodCategory, RecipeCategory
from groceries.models import GroceryList
from groceries.services import add_recipe
from .importer import RecipeImportError, extract_recipe, fetch_html
from .models import Ingredient, Recipe
from .test_support import reviewed_payload


def page(recipe):
    return '<html><script type="application/ld+json">' + json.dumps(recipe) + '</script></html>'


RECIPE = {'@type': 'Recipe', 'name': 'Soup &amp; bread',
          'recipeIngredient': ['1 1/2 cups milk', 'Salt, to taste', '1 (14 oz) can beans'],
          'recipeInstructions': [{'@type': 'HowToStep', 'text': '<p>Mix &amp; stir.</p>'},
                                 {'@type': 'HowToSection', 'name': 'Finish', 'itemListElement': [
                                     {'@type': 'HowToStep', 'text': 'Bake for 20 minutes.'}]}]}


class ExtractionTests(SimpleTestCase):
    def test_nested_graph_type_list_and_sections(self):
        recipe = dict(RECIPE, **{'@type': ['Thing', 'https://schema.org/Recipe']})
        result = extract_recipe(page({'@graph': [{'@type': 'WebPage', 'mainEntity': recipe}]}))
        self.assertEqual(result['recipe_name'], 'Soup & bread')
        self.assertEqual(result['ingredient_text'], '\n'.join(RECIPE['recipeIngredient']))
        self.assertEqual(result['recipe_instructions'], 'Mix & stir.\n\nFinish\n\nBake for 20 minutes.')

    def test_arrays_strings_and_html_entities(self):
        result = extract_recipe(page([{'@type': 'Organization'}, dict(
            RECIPE, recipeIngredient='½ teaspoon salt', recipeInstructions='Mix.<br>Serve.')]))
        self.assertEqual(result['ingredient_text'], '½ teaspoon salt')
        self.assertEqual(result['recipe_instructions'], 'Mix.\nServe.')

    def test_invalid_script_does_not_hide_valid_recipe(self):
        result = extract_recipe('<script type="application/ld+json">not JSON</script>' + page(RECIPE))
        self.assertEqual(result['recipe_name'], 'Soup & bread')

    def test_unsupported_ingredient_object_is_preserved(self):
        value = {'@type': 'PropertyValue', 'value': '3/4', 'name': 'sugar', 'unitText': 'cup'}
        result = extract_recipe(page(dict(RECIPE, recipeIngredient=[value])))
        self.assertEqual(json.loads(result['ingredient_text']), value)

    def test_first_complete_recipe_selected_in_document_order(self):
        result = extract_recipe(page([{'@type': 'Recipe', 'name': 'Incomplete'}, RECIPE,
                                      dict(RECIPE, name='Second')]))
        self.assertEqual(result['recipe_name'], 'Soup & bread')

    def test_missing_or_incomplete_recipe_has_clear_error(self):
        for html in ['<p>No recipe</p>', page({'@type': 'Recipe', 'name': 'Missing fields'}),
                     '<script type="application/ld+json">{broken</script>']:
            with self.subTest(html=html), self.assertRaisesRegex(RecipeImportError, 'No complete Recipe'):
                extract_recipe(html)

    def test_oversized_recipe_text_is_rejected(self):
        with self.assertRaisesRegex(RecipeImportError, 'too large'):
            extract_recipe(page(dict(RECIPE, recipeIngredient=['x' * 100001])))


def addresses(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', port))]


def remote_socket(body=b'<html></html>', status='200 OK', headers=None, length=True):
    fields = {'Content-Type': 'text/html; charset=utf-8', **(headers or {})}
    if length:
        fields['Content-Length'] = str(len(body))
    wire = ('HTTP/1.1 ' + status + '\r\n' + ''.join(
        f'{key}: {value}\r\n' for key, value in fields.items()) + '\r\n').encode() + body
    sock = MagicMock()
    sock.makefile.return_value = io.BytesIO(wire)
    return sock


class SafeFetchTests(SimpleTestCase):
    def test_https_pins_ip_preserves_host_and_checks_tls(self):
        sock = remote_socket(page(RECIPE).encode())
        context = MagicMock()
        context.wrap_socket.return_value = sock
        with patch('recipes.importer.socket.getaddrinfo', side_effect=addresses) as dns, \
                patch('recipes.importer.socket.socket', return_value=sock), \
                patch('recipes.importer.ssl.create_default_context', return_value=context):
            html, url = fetch_html('https://recipes.example/soup#ingredients')
        self.assertIn('Recipe', html)
        self.assertEqual(url, 'https://recipes.example/soup')
        self.assertEqual(dns.call_count, 1)
        sock.connect.assert_called_once_with(('93.184.216.34', 443))
        context.wrap_socket.assert_called_once_with(sock, server_hostname='recipes.example')
        request = b''.join(call.args[0] for call in sock.sendall.call_args_list)
        self.assertIn(b'Host: recipes.example', request)
        self.assertIn(b'Accept-Encoding: identity', request)
        self.assertNotIn(b'Cookie:', request)
        sock.close.assert_called()

    def test_changed_dns_answer_is_never_used_for_connection(self):
        sock = remote_socket()
        rebound = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('127.0.0.1', 80))]
        with patch('recipes.importer.socket.getaddrinfo', side_effect=[addresses('', 80), rebound]) as dns, \
                patch('recipes.importer.socket.socket', return_value=sock):
            fetch_html('http://recipes.example/')
        self.assertEqual(dns.call_count, 1)
        sock.connect.assert_called_once_with(('93.184.216.34', 80))

    def test_resolution_failure_is_reported_without_connection(self):
        with patch('recipes.importer.socket.getaddrinfo', side_effect=socket.gaierror), \
                patch('recipes.importer.socket.socket') as connect, \
                self.assertRaisesRegex(RecipeImportError, 'resolved'):
            fetch_html('http://recipes.example/')
        connect.assert_not_called()

    def test_http_is_allowed_and_environment_proxies_are_ignored(self):
        sock = remote_socket()
        with patch.dict('os.environ', {'HTTP_PROXY': 'http://127.0.0.1:8888'}), \
                patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                patch('recipes.importer.socket.socket', return_value=sock):
            fetch_html('http://recipes.example/soup')
        sock.connect.assert_called_once_with(('93.184.216.34', 80))

    def test_private_special_and_transition_addresses_never_connect(self):
        for ip in ['127.0.0.1', '10.1.2.3', '172.16.0.1', '192.168.1.1', '169.254.169.254',
                   '0.0.0.0', '100.64.0.1', '192.0.0.8', '192.0.0.9', '224.0.0.1', '::1', 'fc00::1', 'fe80::1', 'fec0::1',
                   '::ffff:127.0.0.1', '64:ff9b::7f00:1', '2002:7f00:1::', '168.63.129.16']:
            family = socket.AF_INET6 if ':' in ip else socket.AF_INET
            record = [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 80))]
            with self.subTest(ip=ip), patch('recipes.importer.socket.getaddrinfo', return_value=record), \
                    patch('recipes.importer.socket.socket') as connect, \
                    self.assertRaisesRegex(RecipeImportError, 'public websites'):
                fetch_html('http://recipes.example/soup')
            connect.assert_not_called()

    def test_mixed_public_and_private_dns_answers_are_blocked(self):
        records = addresses('', 80) + [(socket.AF_INET, socket.SOCK_STREAM,
                                        socket.IPPROTO_TCP, '', ('127.0.0.1', 80))]
        with patch('recipes.importer.socket.getaddrinfo', return_value=records), \
                patch('recipes.importer.socket.socket') as connect, self.assertRaises(RecipeImportError):
            fetch_html('http://recipes.example/')
        connect.assert_not_called()

    def test_malformed_urls_credentials_and_nonstandard_ports_never_connect(self):
        for url in ['file:///etc/passwd', 'ftp://recipes.example/', 'https://user:pass@recipes.example/',
                    'https://recipes.example:8443/', 'https://recipes.example:0/', 'http://recipes.example:443/',
                    'https://recipes.example/\r\nHost:local', 'https://recipes.example\\@127.0.0.1/',
                    'https://127.0.0.1%2f.example/', 'https://[::1%25lo]/']:
            with self.subTest(url=url), patch('recipes.importer.socket.socket') as connect, \
                    self.assertRaises(RecipeImportError):
                fetch_html(url)
            connect.assert_not_called()

    def test_redirect_to_private_host_is_blocked_before_connection(self):
        sock = remote_socket(status='302 Found', headers={'Location': 'https://internal.example/'})
        records = [addresses('', 443), [(socket.AF_INET, socket.SOCK_STREAM,
                                        socket.IPPROTO_TCP, '', ('10.0.0.1', 443))]]
        with patch('recipes.importer.socket.getaddrinfo', side_effect=records), \
                patch('recipes.importer.socket.socket', return_value=sock) as connect, \
                patch('recipes.importer.ssl.create_default_context') as context:
            context.return_value.wrap_socket.return_value = sock
            with self.assertRaisesRegex(RecipeImportError, 'public websites'):
                fetch_html('https://recipes.example/')
        self.assertEqual(connect.call_count, 1)
        sock.close.assert_called()

    def test_relative_redirect_and_dns_rebinding_are_safe(self):
        first = remote_socket(status='301 Moved', headers={'Location': '/final'})
        second = remote_socket()
        with patch('recipes.importer.socket.getaddrinfo', side_effect=addresses) as dns, \
                patch('recipes.importer.socket.socket', side_effect=[first, second]):
            _, url = fetch_html('http://recipes.example/start')
        self.assertEqual(url, 'http://recipes.example/final')
        self.assertEqual(dns.call_count, 2)  # Once per hop, never again at connect time.
        first.connect.assert_called_once_with(('93.184.216.34', 80))
        second.connect.assert_called_once_with(('93.184.216.34', 80))
        first.close.assert_called()
        second.close.assert_called()

    def test_unsafe_redirects_are_rejected(self):
        for target in ['http://recipes.example/plain', 'file:///etc/passwd',
                       'https://user:pass@recipes.example/', '//127.0.0.1/', 'https://[invalid/']:
            sock = remote_socket(status='307 Redirect', headers={'Location': target})
            def resolve(host, port, **kwargs):
                return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '',
                         ('127.0.0.1' if host == '127.0.0.1' else '93.184.216.34', port))]
            with self.subTest(target=target), patch('recipes.importer.socket.getaddrinfo', side_effect=resolve), \
                    patch('recipes.importer.socket.socket', return_value=sock) as connect, \
                    patch('recipes.importer.ssl.create_default_context') as context:
                context.return_value.wrap_socket.return_value = sock
                with self.assertRaises(RecipeImportError):
                    fetch_html('https://recipes.example/')
                self.assertEqual(connect.call_count, 1)

    def test_redirect_limit(self):
        sockets = [remote_socket(status='302 Found', headers={'Location': '/again'}) for _ in range(4)]
        with patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                patch('recipes.importer.socket.socket', side_effect=sockets) as connect, \
                self.assertRaisesRegex(RecipeImportError, 'redirect'):
            fetch_html('http://recipes.example/')
        self.assertEqual(connect.call_count, 4)
        for sock in sockets:
            sock.close.assert_called()

    def test_blocked_response_types_status_and_compression(self):
        cases = [('403 Forbidden', {}, 'HTTP 403'),
                 ('401 Unauthorized', {}, 'Copy from browser'),
                 ('429 Too Many Requests', {}, 'Copy from browser'),
                 ('200 OK', {'Content-Type': 'application/pdf'}, 'HTML'),
                 ('200 OK', {'Content-Encoding': 'gzip'}, 'compressed'),
                 ('302 Found', {}, 'redirect')]
        for status, headers, message in cases:
            sock = remote_socket(status=status, headers=headers)
            with self.subTest(status=status, headers=headers), \
                    patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                    patch('recipes.importer.socket.socket', return_value=sock), \
                    self.assertRaisesRegex(RecipeImportError, message):
                fetch_html('http://recipes.example/')
            sock.close.assert_called()

    def test_declared_and_streamed_size_limits(self):
        for length in [True, False]:
            sock = remote_socket(body=b'x' * 100, length=length)
            with self.subTest(length=length), patch('recipes.importer.MAX_BYTES', 64), \
                    patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                    patch('recipes.importer.socket.socket', return_value=sock), \
                    self.assertRaisesRegex(RecipeImportError, 'too large'):
                fetch_html('http://recipes.example/')

    def test_timeout_and_certificate_failure_have_clear_errors(self):
        sock = remote_socket()
        sock.connect.side_effect = TimeoutError
        with patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                patch('recipes.importer.socket.socket', return_value=sock), \
                self.assertRaisesRegex(RecipeImportError, 'securely'):
            fetch_html('http://recipes.example/')
        sock.close.assert_called()
        sock = remote_socket()
        with patch('recipes.importer.socket.getaddrinfo', side_effect=addresses), \
                patch('recipes.importer.socket.socket', return_value=sock), \
                patch('recipes.importer.ssl.create_default_context') as context:
            context.return_value.wrap_socket.side_effect = ssl.SSLCertVerificationError
            with self.assertRaisesRegex(RecipeImportError, 'securely'):
                fetch_html('https://recipes.example/')


class ImportWorkflowTests(TestCase):
    def draft(self):
        return {**extract_recipe(page(RECIPE)), 'source_url': 'https://recipes.example/soup'}

    def reviewed(self):
        return {**self.draft(), 'step': 'save', 'recipe_category': ''}

    def test_import_get_and_navigation(self):
        response = self.client.get(reverse('recipe_import'))
        self.assertContains(response, 'Extract recipe')
        self.assertContains(self.client.get(reverse('home')), reverse('recipe_import'))

    @patch('recipes.importer.import_url')
    def test_extract_only_reviews_and_never_writes(self, fetch):
        fetch.return_value = self.draft()
        response = self.client.post(reverse('recipe_import'), {'url': 'https://recipes.example/soup'})
        self.assertContains(response, 'Save reviewed recipe')
        self.assertContains(response, '1 1/2 cups milk')
        self.assertEqual(response.context['review_form'].initial['source_url'], self.draft()['source_url'])
        self.assertEqual(Recipe.objects.count(), 0)
        self.assertEqual(RecipeCategory.objects.count(), 0)
        fetch.assert_called_once_with('https://recipes.example/soup')

    def test_confirm_saves_edited_text_source_and_default_category(self):
        data = self.reviewed()
        data['recipe_name'] = 'Corrected soup'
        data['ingredient_text'] += '\n2–3 eggs (optional)'
        data['recipe_instructions'] = 'Reviewed instructions.'
        response = self.client.post(reverse('recipe_import'), reviewed_payload(data))
        recipe = Recipe.objects.get()
        self.assertRedirects(response, reverse('recipe_detail', args=[recipe.pk]))
        self.assertEqual(recipe.recipe_name, 'Corrected Soup')
        self.assertEqual(recipe.ingredient_text, data['ingredient_text'])
        self.assertEqual(recipe.source_url, data['source_url'])
        self.assertEqual(recipe.recipe_instructions, 'Reviewed instructions.')
        self.assertEqual(recipe.recipe_category.recipe_category_name, 'Imported')
        self.assertEqual(recipe.recipe_rating, "Haven't Made it Yet")
        self.assertEqual(Ingredient.objects.count(), 3)
        detail = self.client.get(reverse('recipe_detail', args=[recipe.pk]))
        self.assertContains(detail, 'Salt, to taste')
        self.assertContains(detail, data['source_url'])
        self.assertContains(detail, 'Add recipe to grocery list')

    def test_existing_recipe_and_category_are_preserved(self):
        category = RecipeCategory.objects.create(recipe_category_name='dinner')
        old = Recipe.objects.create(recipe_name='Existing recipe', recipe_category=category,
                                    recipe_instructions='Keep this', comments='Keep notes')
        data = {**self.reviewed(), 'recipe_category': category.pk}
        self.client.post(reverse('recipe_import'), reviewed_payload(data))
        old.refresh_from_db()
        self.assertEqual(old.recipe_instructions, 'Keep this')
        self.assertEqual(old.comments, 'Keep notes')
        self.assertEqual(old.source_url, '')
        self.assertEqual(old.ingredient_text, '')
        self.assertEqual(RecipeCategory.objects.count(), 1)
        self.assertEqual(Recipe.objects.exclude(pk=old.pk).get().recipe_category, category)

    @patch('recipes.importer.import_url')
    def test_invalid_review_keeps_text_and_does_not_refetch(self, fetch):
        data = dict(self.reviewed(), recipe_name='')
        response = self.client.post(reverse('recipe_import'), reviewed_payload(data))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['review_form'].errors)
        self.assertContains(response, 'Salt, to taste')
        self.assertFalse(Recipe.objects.exists())
        self.assertFalse(RecipeCategory.objects.exists())
        fetch.assert_not_called()

    def test_duplicate_confirmation_does_not_duplicate_recipe(self):
        for _ in range(2):
            response = self.client.post(reverse('recipe_import'), reviewed_payload(self.reviewed()))
        self.assertContains(response, 'already exists')
        self.assertEqual(Recipe.objects.count(), 1)

    @patch('recipes.importer.import_url', side_effect=RecipeImportError('Only public websites are allowed.'))
    def test_download_error_is_displayed(self, fetch):
        response = self.client.post(reverse('recipe_import'), {'url': 'http://127.0.0.1/'})
        self.assertContains(response, 'Only public websites')
        self.assertFalse(Recipe.objects.exists())

    def test_csrf_required_and_url_validation(self):
        from django.test import Client
        self.assertEqual(Client(enforce_csrf_checks=True).post(
            reverse('recipe_import'), {'url': 'https://recipes.example/soup'}).status_code, 403)
        response = self.client.post(reverse('recipe_import'), {'url': 'not a URL'})
        self.assertTrue(response.context['url_form'].errors)
        self.assertFalse(Recipe.objects.exists())

    def test_untrusted_text_is_escaped_on_review_and_detail(self):
        data = dict(self.reviewed(), ingredient_text='<img src=x onerror=alert(1)>')
        self.client.post(reverse('recipe_import'), reviewed_payload(data))
        response = self.client.get(reverse('recipe_detail', args=[Recipe.objects.get().pk]))
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')

    def test_confirmed_import_reaches_grocery_list_without_manual_reentry(self):
        self.client.post(reverse('recipe_import'), reviewed_payload(self.reviewed()))
        recipe = Recipe.objects.get()
        grocery_list = GroceryList.objects.create(list_name='2026-11-02')
        add_recipe(grocery_list, recipe)
        self.assertEqual(grocery_list.list_items.get(item_name__food_name='Milk').item_quantity, 1.5)
        self.assertEqual(recipe.ingredient_text, self.draft()['ingredient_text'])
        self.assertEqual(len(recipe.ingredient_review_exclusions), 1)


class ImportMigrationTests(TransactionTestCase):
    def test_adding_import_fields_preserves_existing_recipe_and_list_links(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        previous = [(app, '0002_auto_20230331_1010') if app == 'recipes' else (app, migration)
                    for app, migration in latest]
        try:
            executor.migrate(previous)
            old = executor.loader.project_state(previous).apps
            category = old.get_model('components', 'RecipeCategory').objects.create(recipe_category_name='Keep')
            food_category = old.get_model('components', 'FoodCategory').objects.create(food_category_name='Keep')
            food = old.get_model('components', 'Food').objects.create(
                food_name='Keep food', food_category_id=food_category.pk, food_aisle=None)
            ingredient = old.get_model('recipes', 'Ingredient').objects.create(
                ingredient_name_id=food.pk, ingredient_quantity=1.25, quantity_unit='cup(s)')
            recipe = old.get_model('recipes', 'Recipe').objects.create(
                recipe_name='Keep recipe', recipe_category_id=category.pk,
                recipe_instructions='Keep instructions', comments='Keep notes')
            recipe.ingredients.add(ingredient)
            item = old.get_model('groceries', 'ChooseItem').objects.create(
                item_name_id=food.pk, item_quantity=1.25, item_quantity_unit='cup(s)')
            grocery_list = old.get_model('groceries', 'GroceryList').objects.create(list_name='2026-11-02')
            grocery_list.list_items.add(item)
            grocery_list.list_recipes.add(recipe)
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            saved = Recipe.objects.get(pk=recipe.pk)
            self.assertEqual(saved.recipe_instructions, 'Keep instructions')
            self.assertEqual(saved.comments, 'Keep notes')
            self.assertEqual(saved.ingredient_text, '')
            self.assertEqual(saved.ingredient_review_exclusions, [])
            self.assertIsNone(saved.ingredients.get().quantity_max)
            self.assertEqual(saved.ingredients.get().original_text, '')
            self.assertEqual(saved.source_url, '')
            self.assertEqual(saved.ingredients.get().ingredient_quantity, 1.25)
            saved_list = GroceryList.objects.get(pk=grocery_list.pk)
            self.assertEqual(saved_list.list_recipes.get().pk, saved.pk)
            self.assertEqual(saved_list.list_items.get().item_quantity, 1.25)
        finally:
            MigrationExecutor(connection).migrate(latest)
