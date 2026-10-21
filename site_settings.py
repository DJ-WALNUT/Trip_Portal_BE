# site_settings.py
# 사이트 설정 키 정의, 검증, 기본값 채우기, 조회/수정.
import json
import re
from datetime import datetime

from models import db, SiteSetting, KST

MSG_EMPTY = '값을 입력해주세요.'
MSG_TYPE = '형식이 올바르지 않습니다.'
MSG_URL = 'http:// 또는 https://로 시작하는 주소를 입력해주세요.'
MSG_EMAIL = '이메일 형식이 올바르지 않습니다.'
MSG_INSTA = '영문, 숫자, 마침표, 밑줄만 사용할 수 있습니다.'
MSG_UNKNOWN = '알 수 없는 설정입니다.'

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_INSTA_RE = re.compile(r'^[A-Za-z0-9._]{1,30}$')


def _string(value, max_len, multiline):
    if not isinstance(value, str):
        return False, MSG_TYPE
    text = value.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return False, MSG_EMPTY
    if not multiline and '\n' in text:
        return False, MSG_TYPE
    if len(text) > max_len:
        return False, '%d자 이하로 입력해주세요.' % max_len
    return True, text


def _line(max_len):
    return lambda value: _string(value, max_len, False)


def _multiline(max_len):
    return lambda value: _string(value, max_len, True)


def _url(value):
    ok, result = _string(value, 500, False)
    if not ok:
        return ok, result
    if not (result.startswith('http://') or result.startswith('https://')):
        return False, MSG_URL
    return True, result


def _email(value):
    ok, result = _string(value, 200, False)
    if not ok:
        return ok, result
    if not _EMAIL_RE.match(result):
        return False, MSG_EMAIL
    return True, result


def _instagram(value):
    ok, result = _string(value, 200, False)
    if not ok:
        return ok, result
    if result.startswith('@'):
        result = result[1:]
    if not _INSTA_RE.match(result):
        return False, MSG_INSTA
    return True, result


def _boolean(value):
    if not isinstance(value, bool):
        return False, MSG_TYPE
    return True, value


def _int_range(low, high):
    def validate(value):
        if isinstance(value, bool) or not isinstance(value, int):
            return False, '%d~%d 사이의 숫자를 입력해주세요.' % (low, high)
        if value < low or value > high:
            return False, '%d~%d 사이의 숫자를 입력해주세요.' % (low, high)
        return True, value
    return validate


def _link(value):
    if not isinstance(value, dict):
        return False, MSG_TYPE
    ok, label = _string(value.get('label'), 30, False)
    if not ok:
        return False, label
    ok, url = _url(value.get('url'))
    if not ok:
        return False, url
    return True, {'label': label, 'url': url}


def _link_list(low, high):
    def validate(value):
        if not isinstance(value, list):
            return False, MSG_TYPE
        if len(value) < low or len(value) > high:
            return False, '%d~%d개까지 입력할 수 있습니다.' % (low, high)
        items = []
        for item in value:
            ok, result = _link(item)
            if not ok:
                return False, result
            items.append(result)
        return True, items
    return validate


SETTINGS_SPEC = {
    'contact.address': {
        'default': '14662 경기 부천시 원미구 지봉로 43 가톨릭대학교 니콜스관 N507 공과대학 학생회실',
        'validate': _line(200)},
    'contact.room': {'default': '공대방(N507)', 'validate': _line(200)},
    'contact.email': {'default': 'cukeng2026@gmail.com', 'validate': _email},
    'contact.manager': {'default': '김세호', 'validate': _line(200)},
    'sns.instagram': {'default': 'cuk.engineering', 'validate': _instagram},
    'sns.linktree': {'default': 'https://linktr.ee/cuk_engineering', 'validate': _url},
    'sns.kakao': {'default': 'https://pf.kakao.com/_xcyDGn', 'validate': _url},
    'links.school': {
        'default': [
            {'label': '학교 홈페이지', 'url': 'https://www.catholic.ac.kr'},
            {'label': '학사일정', 'url': 'https://www.catholic.ac.kr/ko/support/calendar2024_list.do'},
            {'label': '트리니티', 'url': 'https://uportal.catholic.ac.kr'},
            {'label': '사이버캠퍼스', 'url': 'https://e-cyber.catholic.ac.kr'},
            {'label': '공결허가원', 'url': 'https://www.catholic.ac.kr/ko/support/absence_notification.do'},
        ],
        'validate': _link_list(1, 10)},
    'links.external': {
        'default': {'label': '2025 새길', 'url': 'https://2025saegil.cukeng.kr'},
        'validate': _link},
    'home.hero_sub': {'default': '제4대 공과대학 학생회 [여정]', 'validate': _line(200)},
    'home.hero_title': {'default': '변화를 새길, 우리의 여정!', 'validate': _line(200)},
    'footer.copyright': {
        'default': '© 2026 Catholic University of Korea.\nCUK Engineering Student Council Trip. All Rights Reserved',
        'validate': _multiline(1000)},
    'maintenance.notice': {
        'default': '보다 안정적인 서비스를 위해\n서버를 점검하고 있습니다.\n매일 05:00 ~ 06:00은 정기 점검 시간입니다.',
        'validate': _multiline(1000)},
    'maintenance.available': {
        'default': '이용 가능 서비스:\n학교페이지 바로가기, 조직도 열람,\n단과대 및 학과 편성',
        'validate': _multiline(1000)},
    'rental.enabled': {'default': True, 'validate': _boolean},
    'rental.return_days': {'default': 4, 'validate': _int_range(1, 30)},
    'rental.cancel_notice': {
        'default': '※ 신청 시각 기준 24시간이 지나면 자동으로 신청이 취소되오니,\n참고하여 수령해주시길 바랍니다.',
        'validate': _multiline(1000)},
    'system.snowfall': {'default': False, 'validate': _boolean},
}


def _legacy_snowfall(settings_json_path):
    try:
        with open(settings_json_path, 'r', encoding='utf-8') as f:
            return bool(json.load(f).get('snowfall', False))
    except (OSError, ValueError, AttributeError):
        return False


def ensure_defaults(settings_json_path):
    """DB에 없는 키만 기본값으로 삽입한다. 기존 값은 덮어쓰지 않는다."""
    existing = set(row[0] for row in db.session.query(SiteSetting.key).all())
    added = False
    for key, spec in SETTINGS_SPEC.items():
        if key in existing:
            continue
        value = spec['default']
        if key == 'system.snowfall':
            value = _legacy_snowfall(settings_json_path)
        db.session.add(SiteSetting(
            key=key, value=json.dumps(value, ensure_ascii=False),
            updated_at=datetime.now(KST), updated_by='system'))
        added = True
    if added:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


def get_public_settings():
    """모든 설정 키의 현재 값(DB 값, 없거나 깨졌으면 기본값)."""
    result = {key: spec['default'] for key, spec in SETTINGS_SPEC.items()}
    for row in SiteSetting.query.all():
        if row.key in result:
            try:
                result[row.key] = json.loads(row.value)
            except ValueError:
                pass
    return result


def get_setting(key):
    row = db.session.get(SiteSetting, key)
    if row is not None:
        try:
            return json.loads(row.value)
        except ValueError:
            pass
    return SETTINGS_SPEC[key]['default']


def update_settings(changes, role):
    """모든 키를 검증한 뒤 한 트랜잭션으로 저장. 하나라도 오류면 아무것도 저장하지 않는다."""
    if not isinstance(changes, dict):
        return False, {'_': MSG_TYPE}
    errors = {}
    normalized = {}
    for key, value in changes.items():
        spec = SETTINGS_SPEC.get(key)
        if spec is None:
            errors[key] = MSG_UNKNOWN
            continue
        ok, result = spec['validate'](value)
        if ok:
            normalized[key] = result
        else:
            errors[key] = result
    if errors:
        return False, errors
    try:
        now = datetime.now(KST)
        for key, value in normalized.items():
            row = db.session.get(SiteSetting, key)
            payload = json.dumps(value, ensure_ascii=False)
            if row is None:
                db.session.add(SiteSetting(key=key, value=payload, updated_at=now, updated_by=role))
            else:
                row.value = payload
                row.updated_at = now
                row.updated_by = role
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return True, get_public_settings()
