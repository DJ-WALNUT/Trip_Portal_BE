from datetime import date

import models
from tests.helpers import login

GOOD = {
    'title': '학식 만족도 조사', 'content': '3분이면 끝나요',
    'link_url': 'https://forms.example.com/abc',
    'deadline': '2026-11-20', 'duration': '3분', 'reward': '추첨 기프티콘',
    'is_public': True,
}


def freeze(monkeypatch, y, m, d):
    monkeypatch.setattr(models, 'today_kst', lambda: date(y, m, d))


def create(client, **over):
    res = client.post('/api/surveys', json={**GOOD, **over})
    assert res.status_code == 201, res.get_json()
    return res.get_json()['data']


def logout(client):
    with client.session_transaction() as s:
        s.clear()


def test_create_requires_login(client):
    assert client.post('/api/surveys', json=GOOD).status_code == 401


def test_create_and_get_detail(client, monkeypatch):
    freeze(monkeypatch, 2026, 11, 11)
    login(client, 'sub')
    item = create(client)
    assert item['link_url'] == 'https://forms.example.com/abc'
    assert item['deadline'] == '2026-11-20'
    assert item['duration'] == '3분' and item['reward'] == '추첨 기프티콘'
    assert item['author'] == '여정 학생회' and item['views'] == 0
    assert item['is_public'] is True and item['is_closed'] is False
    got = client.get(f"/api/surveys/{item['id']}").get_json()
    assert got['title'] == '학식 만족도 조사'


def test_optional_fields_become_null(client):
    login(client)
    item = create(client, deadline='', duration='  ', reward=None)
    assert item['deadline'] is None and item['duration'] is None and item['reward'] is None
    assert item['is_closed'] is False


def test_is_closed_uses_kst_date(client, monkeypatch):
    login(client)
    item = create(client, deadline='2026-11-20')
    freeze(monkeypatch, 2026, 11, 20)
    assert client.get(f"/api/surveys/{item['id']}").get_json()['is_closed'] is False
    freeze(monkeypatch, 2026, 11, 21)
    assert client.get(f"/api/surveys/{item['id']}").get_json()['is_closed'] is True


def test_today_kst_is_kst(monkeypatch):
    from datetime import datetime, timezone

    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):  # 2026-11-20 15:30 UTC == 2026-11-21 00:30 KST
            return datetime(2026, 11, 20, 15, 30, tzinfo=timezone.utc).astimezone(tz)
    monkeypatch.setattr(models, 'datetime', FakeDT)
    assert models.today_kst() == date(2026, 11, 21)


def test_past_deadline_allowed(client, monkeypatch):
    freeze(monkeypatch, 2026, 11, 11)
    login(client)
    assert create(client, deadline='2026-01-01')['is_closed'] is True


def test_link_validation(client):
    login(client)
    for bad in ['javascript:alert(1)', '//evil.com', 'forms.example.com', 'ftp://a.b', '']:
        res = client.post('/api/surveys', json={**GOOD, 'link_url': bad})
        assert res.status_code == 400, bad
    assert create(client, link_url='  HTTPS://Forms.example.com/x  ')['link_url'] == 'HTTPS://Forms.example.com/x'


def test_required_and_format_errors(client):
    login(client)
    res = client.post('/api/surveys', json={**GOOD, 'title': '   '})
    assert res.status_code == 400
    assert res.get_json()['error'] == '제목, 내용, 설문 링크는 필수입니다.'
    res = client.post('/api/surveys', json={**GOOD, 'deadline': '2026-13-01'})
    assert res.get_json()['error'] == '마감일은 YYYY-MM-DD 형식으로 입력해주세요.'
    res = client.post('/api/surveys', json={**GOOD, 'duration': 'a' * 31})
    assert res.get_json()['error'] == '입력 길이를 초과했습니다.'
    for field, n in [('title', 201), ('link_url', 501), ('reward', 51)]:
        value = 'https://a.b/' + 'a' * n if field == 'link_url' else 'a' * n
        assert client.post('/api/surveys', json={**GOOD, field: value}).status_code == 400


def test_non_json_body_is_400(client):
    login(client)
    assert client.post('/api/surveys', data='hello', content_type='text/plain').status_code == 400
    assert client.post('/api/surveys', json=['a']).status_code == 400


def test_views_increment_only_when_asked(client):
    login(client)
    sid = create(client)['id']
    client.get(f'/api/surveys/{sid}')
    client.get(f'/api/surveys/{sid}?increment=false')
    assert client.get(f'/api/surveys/{sid}').get_json()['views'] == 0
    client.get(f'/api/surveys/{sid}?increment=true')
    assert client.get(f'/api/surveys/{sid}').get_json()['views'] == 1


def test_private_detail_404_for_guests(client):
    login(client)
    sid = create(client, is_public=False)['id']
    assert client.get(f'/api/surveys/{sid}').status_code == 200
    logout(client)
    assert client.get(f'/api/surveys/{sid}').status_code == 404
    assert client.get('/api/surveys/99999').status_code == 404
