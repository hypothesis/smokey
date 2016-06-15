from behave import given, then, when


def search(context, params={}):
    api_root = context.config.userdata['api_root']
    context.last_response = context.http.get('%s/search' % api_root,
                                             params=params)


def create_annotation(context, data=None):
    try:
        getattr(context, 'user')
    except AttributeError:
        raise RuntimeError("can't create annotations without active test user")

    if data is None:
        data = {}

    data.update({
        "smokey": True,
        "uri": "http://example.com",
        "permissions": {
            "read": ["group:__world__"],
            "delete": [context.user['userid']],
        }
    })

    api_root = context.config.userdata['api_root']
    url = '{root}/annotations'.format(root=api_root)
    context.last_response = context.http.post(url, json=data)


def delete_annotation(context, id):
    try:
        getattr(context, 'user')
    except AttributeError:
        raise RuntimeError("can't delete annotations without active test user")

    api_root = context.config.userdata['api_root']
    url = '{root}/annotations/{id}'.format(root=api_root, id=id)
    context.last_response = context.http.delete(url)


@given('I am acting as the test user "{user}"')
def act_as_test_user(context, user):
    if user not in context.test_users:
        context.scenario.skip('API key for test user "{user}" not '
                              'provided!'.format(user=user))
        return

    # Set the current user so that other step definitions can refer to it
    context.user = context.test_users[user]

    # Set the API token in use
    context.http.headers.update({
        'Authorization': 'Bearer {token}'.format(token=context.user['token'])
    })


@when('I create a test annotation')
def create_test_annotation(context):
    create_annotation(context)
    ann = context.last_response.json()
    context.last_test_annotation = ann
    if 'id' not in ann:
        raise RuntimeError("could not create annotation: {}".format(ann))
    context.teardown.append(lambda: delete_annotation(context, ann['id']))


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
        matching_tags = [t for t in annotation['tags']
                         if tag.lower() in t.lower()]
        assert len(matching_tags) > 0


@then('I should get annotations authored by "{user}"')
def verify_annotation_author(context, user):
    response = context.last_response.json()
    assert len(response['rows']) > 0
    for annotation in response['rows']:
        print(annotation['user'])
        assert annotation['user'] == 'acct:%s@hypothes.is' % user
