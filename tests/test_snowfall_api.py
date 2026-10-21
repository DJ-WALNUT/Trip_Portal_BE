from conftest import login


def test_snowfall_contract(client):
    assert client.get('/api/system/snowfall').get_json() == {'status': 'success', 'enabled': False}
    login(client, 'sub')
    res = client.post('/api/admin/system/snowfall', json={'enabled': True})
    assert res.status_code == 200
    assert res.get_json() == {'status': 'success', 'enabled': True}
    assert client.get('/api/system/snowfall').get_json()['enabled'] is True
    client.post('/api/admin/logout')
    assert client.post('/api/admin/system/snowfall', json={'enabled': False}).status_code == 401
