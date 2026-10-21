import json

from models import SiteSetting, db
import site_settings
from site_settings import (SETTINGS_SPEC, ensure_defaults, get_public_settings,
                           get_setting, update_settings)


def _no_file(tmp_path):
    return str(tmp_path / 'nope.json')


def test_ensure_defaults_fills_all_keys(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    pub = get_public_settings()
    assert set(pub.keys()) == set(SETTINGS_SPEC.keys())
    assert len(SETTINGS_SPEC) == 18
    assert pub['contact.room'] == '공대방(N507)'
    assert pub['rental.return_days'] == 4
    assert len(pub['links.school']) == 5


def test_ensure_defaults_keeps_existing(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    db.session.merge(SiteSetting(key='contact.room', value=json.dumps('X(1)'), updated_by='master'))
    db.session.commit()
    ensure_defaults(_no_file(tmp_path))
    assert get_setting('contact.room') == 'X(1)'


def test_snowfall_migrated_from_settings_json(app_ctx, tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'snowfall': True}), encoding='utf-8')
    ensure_defaults(str(path))
    assert get_setting('system.snowfall') is True


def test_snowfall_default_false_without_file(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    assert get_setting('system.snowfall') is False


def test_update_rejects_all_on_any_error(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    ok, errors = update_settings({'contact.room': '새방', 'contact.email': 'bad'}, 'master')
    assert ok is False
    assert errors == {'contact.email': '이메일 형식이 올바르지 않습니다.'}
    assert get_setting('contact.room') == '공대방(N507)'


def test_update_success_returns_all_and_records_role(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    ok, data = update_settings({'contact.room': '  새방  '}, 'master')
    assert ok is True
    assert set(data.keys()) == set(SETTINGS_SPEC.keys())
    assert data['contact.room'] == '새방'
    assert db.session.get(SiteSetting, 'contact.room').updated_by == 'master'


def test_update_normalizes_instagram(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    ok, _ = update_settings({'sns.instagram': '@new.id'}, 'master')
    assert ok
    assert get_setting('sns.instagram') == 'new.id'


def _check(key, value):
    return SETTINGS_SPEC[key]['validate'](value)


def test_validators():
    assert _check('rental.return_days', 0)[0] is False
    assert _check('rental.return_days', 31)[0] is False
    assert _check('rental.return_days', '4')[0] is False
    assert _check('rental.return_days', True)[0] is False
    assert _check('rental.return_days', 30) == (True, 30)
    assert _check('rental.return_days', 0)[1] == '1~30 사이의 숫자를 입력해주세요.'

    assert _check('links.school', [])[0] is False
    assert _check('links.school', [])[1] == '1~10개까지 입력할 수 있습니다.'
    assert _check('links.school', [{'label': 'a', 'url': 'https://a.kr'}] * 11)[0] is False
    assert _check('links.school', [{'label': 'a', 'url': 'ftp://x'}])[0] is False
    assert _check('links.school', [{'label': 'a', 'url': 'https://a.kr'}])[0] is True

    ok, reason = _check('contact.room', 'a' * 201)
    assert (ok, reason) == (False, '200자 이하로 입력해주세요.')
    assert _check('contact.room', '   ') == (False, '값을 입력해주세요.')
    assert _check('contact.room', 5) == (False, '형식이 올바르지 않습니다.')
    assert _check('contact.room', 'a\nb')[0] is False
    assert _check('footer.copyright', 'a\nb') == (True, 'a\nb')

    assert _check('rental.enabled', 'true') == (False, '형식이 올바르지 않습니다.')
    assert _check('rental.enabled', False) == (True, False)
    assert _check('sns.linktree', 'x.kr') == (False, 'http:// 또는 https://로 시작하는 주소를 입력해주세요.')
    assert _check('sns.instagram', 'a b')[1] == '영문, 숫자, 마침표, 밑줄만 사용할 수 있습니다.'
    assert _check('links.external', {'label': 'a', 'url': 'https://a.kr'})[0] is True


def test_unknown_key_rejected(app_ctx, tmp_path):
    ensure_defaults(_no_file(tmp_path))
    ok, errors = update_settings({'nope.key': 1}, 'master')
    assert (ok, errors) == (False, {'nope.key': '알 수 없는 설정입니다.'})
