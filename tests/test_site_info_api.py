from tests.helpers import login


def test_get_site_info_public(client):
    res = client.get('/api/site-info')
    assert res.status_code == 200
    body = res.get_json()
    assert body['status'] == 'success'
    assert body['data']['sns.instagram'] == 'cuk.engineering'


def test_put_requires_master(client):
    res = client.put('/api/admin/site-info', json={'home.hero_title': 'x'})
    assert res.status_code == 401
    assert res.get_json()['message'] == '로그인이 필요합니다.'
    login(client, 'sub')
    res = client.put('/api/admin/site-info', json={'home.hero_title': 'x'})
    assert res.status_code == 403
    assert res.get_json()['message'] == '마스터 권한이 필요합니다.'
    login(client, 'master')
    res = client.put('/api/admin/site-info', json={'home.hero_title': 'x'})
    assert res.status_code == 200


def test_put_partial_update(client):
    login(client)
    res = client.put('/api/admin/site-info', json={'home.hero_title': '새 문구'})
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['home.hero_title'] == '새 문구'
    assert data['contact.room'] == '공대방(N507)'
    assert client.get('/api/site-info').get_json()['data']['home.hero_title'] == '새 문구'


def test_put_atomic(client):
    login(client)
    res = client.put('/api/admin/site-info', json={'contact.room': 'A', 'rental.return_days': 99})
    assert res.status_code == 400
    body = res.get_json()
    assert body['status'] == 'fail'
    assert body['errors'] == {'rental.return_days': '1~30 사이의 숫자를 입력해주세요.'}
    assert client.get('/api/site-info').get_json()['data']['contact.room'] == '공대방(N507)'


def test_put_non_object(client):
    login(client)
    res = client.put('/api/admin/site-info', json=[1, 2])
    assert res.status_code == 400
    assert res.get_json() == {'status': 'fail', 'errors': {'_': '형식이 올바르지 않습니다.'}}
