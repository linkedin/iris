from iris.bin.sync_targets import sync_from_oncall
from sqlalchemy import create_engine

sample_db_config = {
    'db': {
        'conn': {
            'str': "%(scheme)s://%(user)s:%(password)s@%(host)s/%(database)s?charset=%(charset)s",
            'kwargs': {
                'scheme': 'mysql+pymysql',
                'user': 'root',
                'password': '',
                'host': '127.0.0.1',
                'database': 'iris',
                'charset': 'utf8'}},
        'kwargs': {
            'pool_recycle': 3600,
            'echo': False,
            'pool_size': 100,
            'max_overflow': 100,
            'pool_timeout': 60
        }}}


def get_db_engine_from_config(config):
    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])
    return engine


def test_create_oncall_team_table(mocker):
    '''Test initialization of oncall_team table'''

    sample_oncall_teams_response = [["demo_team", 10001], ["foo_team", 10002], ["bar_team", 10003]]
    sample_oncall_users_response = {"abc": {"sms": "+1 223-456-7891", "slack": "abc", "call": "+1 223-456-7891", "email": "abc@domain.com"}, "demo": {"sms": "+1 223-456-7890", "slack": "demo", "call": "+1 223-456-7890", "email": "demo@domain.com"}, "foo": {"sms": "+1 223-456-7892", "slack": "foo", "call": "+1 223-456-7892", "email": "foo@domain.com"}}

    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = sample_oncall_teams_response
    mocker.patch('iris.bin.sync_targets.fetch_users_from_oncall').return_value = sample_oncall_users_response
    mocker.patch('iris.metrics.stats')

    engine = get_db_engine_from_config(sample_db_config)
    dummy_configs = {'oncall-api': 'foo'}
    sync_from_oncall(dummy_configs, engine)

    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert {'demo_team', 'foo_team', 'bar_team'} == iris_team_names


def test_rename_team(mocker):
    '''Test renaming of a team'''

    sample_oncall_teams_response = [["demo_team", 10001], ["foo_team", 10002], ["bar_team", 10003]]
    sample_oncall_users_response = {"abc": {"sms": "+1 223-456-7891", "slack": "abc", "call": "+1 223-456-7891", "email": "abc@domain.com"}, "demo": {"sms": "+1 223-456-7890", "slack": "demo", "call": "+1 223-456-7890", "email": "demo@domain.com"}, "foo": {"sms": "+1 223-456-7892", "slack": "foo", "call": "+1 223-456-7892", "email": "foo@domain.com"}}

    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = sample_oncall_teams_response
    mocker.patch('iris.bin.sync_targets.fetch_users_from_oncall').return_value = sample_oncall_users_response
    mocker.patch('iris.metrics.stats')
    engine = get_db_engine_from_config(sample_db_config)
    dummy_configs = {'oncall-api': 'foo'}

    sync_from_oncall(dummy_configs, engine)
    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert {'demo_team', 'foo_team', 'bar_team'} == iris_team_names

    # rename demo_team and foo_team also test swap edgecase
    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = [["foo_team", 10001], ["foo_team_renamed", 10002], ["bar_team", 10003]]
    sync_from_oncall(dummy_configs, engine)

    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert iris_team_names == {'foo_team_renamed', 'foo_team', 'bar_team'}


def test_delete_team(mocker):
    '''Test deletion of a team'''

    sample_oncall_teams_response = [["demo_team", 10001], ["foo_team", 10002], ["bar_team", 10003]]
    sample_oncall_users_response = {"abc": {"sms": "+1 223-456-7891", "slack": "abc", "call": "+1 223-456-7891", "email": "abc@domain.com"}, "demo": {"sms": "+1 223-456-7890", "slack": "demo", "call": "+1 223-456-7890", "email": "demo@domain.com"}, "foo": {"sms": "+1 223-456-7892", "slack": "foo", "call": "+1 223-456-7892", "email": "foo@domain.com"}}

    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = sample_oncall_teams_response
    mocker.patch('iris.bin.sync_targets.fetch_users_from_oncall').return_value = sample_oncall_users_response
    mocker.patch('iris.metrics.stats')
    engine = get_db_engine_from_config(sample_db_config)
    dummy_configs = {'oncall-api': 'foo'}

    sync_from_oncall(dummy_configs, engine)
    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert iris_team_names == {'demo_team', 'foo_team', 'bar_team'}

    # return only bar team. This simulates deleting foo and foo team from oncall
    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = [["bar_team", 10003]]
    sync_from_oncall(dummy_configs, engine)

    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `active` = 1 AND `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10003}
    assert iris_team_names == {'bar_team'}


def test_empty_oncall_response(mocker):
    '''Test handling of an empty response from oncall'''

    sample_oncall_teams_response = [["demo_team", 10001], ["foo_team", 10002], ["bar_team", 10003]]
    sample_oncall_users_response = {"abc": {"sms": "+1 223-456-7891", "slack": "abc", "call": "+1 223-456-7891", "email": "abc@domain.com"}, "demo": {"sms": "+1 223-456-7890", "slack": "demo", "call": "+1 223-456-7890", "email": "demo@domain.com"}, "foo": {"sms": "+1 223-456-7892", "slack": "foo", "call": "+1 223-456-7892", "email": "foo@domain.com"}}

    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = sample_oncall_teams_response
    mocker.patch('iris.bin.sync_targets.fetch_users_from_oncall').return_value = sample_oncall_users_response
    mocker.patch('iris.metrics.stats')

    engine = get_db_engine_from_config(sample_db_config)
    dummy_configs = {'oncall-api': 'foo'}
    sync_from_oncall(dummy_configs, engine)

    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert iris_team_names == {'demo_team', 'foo_team', 'bar_team'}

    # recieve empty response from oncall
    sample_oncall_teams_response = []
    sample_oncall_users_response = {"abc": {"sms": "+1 223-456-7891", "slack": "abc", "call": "+1 223-456-7891", "email": "abc@domain.com"}, "demo": {"sms": "+1 223-456-7890", "slack": "demo", "call": "+1 223-456-7890", "email": "demo@domain.com"}, "foo": {"sms": "+1 223-456-7892", "slack": "foo", "call": "+1 223-456-7892", "email": "foo@domain.com"}}

    mocker.patch('iris.bin.sync_targets.fetch_teams_from_oncall').return_value = sample_oncall_teams_response
    mocker.patch('iris.bin.sync_targets.fetch_users_from_oncall').return_value = sample_oncall_users_response
    mocker.patch('iris.metrics.stats')

    engine = get_db_engine_from_config(sample_db_config)
    dummy_configs = {'oncall-api': 'foo'}
    sync_from_oncall(dummy_configs, engine)

    iris_oncall_team_ids = {oncall_team_id for (oncall_team_id, ) in engine.execute('''SELECT `oncall_team_id` FROM `oncall_team`''')}
    iris_team_names = {name for (name, ) in engine.execute('''SELECT `name` FROM `target` WHERE `type_id` IN  (SELECT id FROM `target_type` WHERE `name` = "team")''')}
    assert iris_oncall_team_ids == {10001, 10002, 10003}
    assert iris_team_names == {'demo_team', 'foo_team', 'bar_team'}
