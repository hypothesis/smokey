import json, requests

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

h_domain = 'hypothes.is'
url = 'http://jonudell.net/h/lorem.html'
user = 'hypothesistest'
query_url_template = 'https://%s/api/search?{query}' % h_domain

all = 6
tagged_latin = 2
tagged_latin_and_vocabulary = 1

base_params = { 'uri': url }
user_params = { 'uri': url, 'user': 'hypothesistest' }

params = {
    'base_params': base_params,
    'user_params': user_params
    }

def search(params):
    h_url = query_url_template.format(query=urlencode(params, True))
    json = requests.get(h_url).json()
    return h_url, json

def results_match_expected(params_name, params_dict, expected_name, expected_count):
    (query_url, result) = search(params_dict)
    count = len(result['rows'])
    return count == expected_count

class TestQueryCorrectness:

    def test_base_params_finds_all(self):
        params_name = 'base_params'
        current_params = params[params_name]
        assert results_match_expected(params_name, current_params, 'all', all)

    def test_user_params_finds_all(self):
        params_name = 'user_params'
        current_params = params[params_name]
        assert results_match_expected(params_name, current_params, 'all', all)

    def test_base_params_finds_tagged_latin(self):
        params_name = 'base_params'
        current_params = params[params_name]
        current_params['tags'] = 'latin'
        assert results_match_expected(params_name, current_params, 'tagged_latin', tagged_latin)

    def test_user_params_finds_tagged_latin(self):
        params_name = 'user_params'
        current_params = params[params_name]
        current_params['tags'] = 'latin'
        assert results_match_expected(params_name, current_params, 'tagged_latin', tagged_latin)

    def test_base_params_finds_tagged_latin_and_vocabulary(self):
        params_name = 'base_params'
        current_params = params[params_name]
        current_params['tags'] = tuple(['latin', 'vocabulary'])
        assert results_match_expected(params_name, current_params, 'tagged_latin_and_vocabulary', tagged_latin_and_vocabulary)

    def test_user_params_finds_tagged_latin_and_vocabulary(self):
        params_name = 'user_params'
        current_params = params[params_name]
        current_params['tags'] = tuple(['latin', 'vocabulary'])
        assert results_match_expected(params_name, current_params, 'tagged_latin_and_vocabulary', tagged_latin_and_vocabulary)


