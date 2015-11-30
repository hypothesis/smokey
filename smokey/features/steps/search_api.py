from behave import *

import requests

def search(context, params={}):
    api_root = context.config.userdata['api_root']
    context.last_response = requests.get('%s/search' % api_root, params=params)


@when('I search with no query')
def search_with_no_query(context):
    search(context)


@when('I search for annotations tagged "{tag}"')
def search_by_tag(context, tag):
    search(context, params={'tags': tag})


@when('I search for annotations authored by "{user}"')
def search_by_user(context, user):
    search(context, params={'user': user})


@then('I should get at least {count} annotations')
def verify_annotation_count(context, count):
    count = int(count)
    response = context.last_response.json()
    assert len(response['rows']) >= count
    assert response['total'] >= count


@then('I should get annotations tagged "{tag}"')
def verify_annotation_tag(context, tag):
    response = context.last_response.json()
    assert len(response['rows']) > 0
    for annotation in response['rows']:
        matching_tags = filter(lambda t: tag in t, annotation['tags'])
        assert len(matching_tags) > 0


@then('I should get annotations authored by "{user}"')
def verify_annotation_author(context, user):
    response = context.last_response.json()
    assert len(response['rows']) > 0
    for annotation in response['rows']:
        print(annotation['user'])
        assert annotation['user'] == 'acct:%s@hypothes.is' % user
