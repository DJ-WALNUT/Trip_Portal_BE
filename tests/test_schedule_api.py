from tests.conftest import login

GOOD = {'name': '2027-2', 'start': '2027-09-01', 'end': '2027-12-20'}


def _create(client):
    res = client.post('/api/admin/schedule', json=GOOD)
    assert res.status_code == 201
    return res.get_json()['data']


def test_post_and_get_has_id(client):
    login(client)
    item = _create(client)
    assert item['name'] == '2027-2' and item['start'] == '2027-09-01' and item['end'] == '2027-12-20'
    items = client.get('/api/schedule').get_json()
    assert any(i['id'] == item['id'] for i in items)


def test_start_after_end(client):
    login(client)
    res = client.post('/api/admin/schedule', json={'name': 'a', 'start': '2027-12-20', 'end': '2027-09-01'})
    assert res.status_code == 400
    assert res.get_json()['errors']['end'] == '종료일은 시작일 이후여야 합니다.'


def test_invalid_date_and_name(client):
    login(client)
    res = client.post('/api/admin/schedule', json={'name': 'a', 'start': '2027-13-01', 'end': '2027-12-01'})
    assert res.status_code == 400
    assert res.get_json()['errors']['start'] == 'YYYY-MM-DD 형식의 날짜를 입력해주세요.'
    res = client.post('/api/admin/schedule', json={'name': ' ', 'start': '2027-01-01', 'end': '2027-12-01'})
    assert res.get_json()['errors']['name'] == '값을 입력해주세요.'
    res = client.post('/api/admin/schedule', json={'name': 'a' * 51, 'start': '2027-01-01', 'end': '2027-12-01'})
    assert res.get_json()['errors']['name'] == '50자 이하로 입력해주세요.'


def test_put_and_delete(client):
    login(client)
    item = _create(client)
    res = client.put('/api/admin/schedule/%d' % item['id'],
                     json={'name': '2027-2b', 'start': '2027-09-02', 'end': '2027-12-21'})
    assert res.status_code == 200
    items = client.get('/api/schedule').get_json()
    assert [i for i in items if i['id'] == item['id']][0]['name'] == '2027-2b'
    assert client.delete('/api/admin/schedule/%d' % item['id']).status_code == 200
    assert all(i['id'] != item['id'] for i in client.get('/api/schedule').get_json())


def test_missing_id_404(client):
    login(client)
    assert client.put('/api/admin/schedule/9999', json=GOOD).status_code == 404
    assert client.delete('/api/admin/schedule/9999').status_code == 404


def test_sub_forbidden(client):
    login(client, 'sub')
    assert client.post('/api/admin/schedule', json=GOOD).status_code == 403
