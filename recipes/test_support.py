"""Explicitly confirm parser suggestions when exercising the import save boundary."""
from .ingredient_review import matching_formset


def reviewed_payload(data, reference_unknown=True):
    result = dict(data)
    formset = matching_formset(result.get('ingredient_text', ''))
    result.update({'ingredients-TOTAL_FORMS': str(len(formset.forms)),
                   'ingredients-INITIAL_FORMS': str(len(formset.forms))})
    for i, form in enumerate(formset):
        initial = form.initial
        for key, value in initial.items():
            result[f'ingredients-{i}-{key}'] = '' if value is None else str(value)
        result[f'ingredients-{i}-confirm_uncertain'] = 'on'
        if reference_unknown and (initial['quantity'] is None or not initial['new_food_name'] and not initial['food']):
            result[f'ingredients-{i}-reference_only'] = 'on'
    return result
