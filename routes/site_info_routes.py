# routes/site_info_routes.py
# 사이트 정보 설정 API와 학사일정 쓰기 API
from datetime import datetime

from flask import Blueprint, jsonify, request, session

from extensions import limiter, login_required, master_required
from models import db, Schedule
from site_settings import get_public_settings, update_settings

site_info_bp = Blueprint('site_info', __name__)

MSG_TYPE = '형식이 올바르지 않습니다.'
MSG_EMPTY = '값을 입력해주세요.'
MSG_DATE = 'YYYY-MM-DD 형식의 날짜를 입력해주세요.'
MSG_ORDER = '종료일은 시작일 이후여야 합니다.'


@site_info_bp.route('/api/site-info', methods=['GET'])
@limiter.exempt
def get_site_info():
    return jsonify({'status': 'success', 'data': get_public_settings()})


@site_info_bp.route('/api/admin/site-info', methods=['PUT'])
@login_required
@master_required
def put_site_info():
    changes = request.get_json(silent=True)
    if not isinstance(changes, dict):
        return jsonify({'status': 'fail', 'errors': {'_': MSG_TYPE}}), 400
    ok, result = update_settings(changes, session.get('role'))
    if not ok:
        return jsonify({'status': 'fail', 'errors': result}), 400
    return jsonify({'status': 'success', 'data': result})


def _parse_date(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if len(text) != 10:
        return None
    try:
        datetime.strptime(text, '%Y-%m-%d')
    except ValueError:
        return None
    return text


def _validate_schedule(body):
    """(clean, errors) 반환."""
    if not isinstance(body, dict):
        return None, {'_': MSG_TYPE}
    errors = {}
    name = body.get('name')
    if not isinstance(name, str) or not name.strip():
        errors['name'] = MSG_EMPTY
    else:
        name = name.strip()
        if '\n' in name or '\r' in name:
            errors['name'] = MSG_TYPE
        elif len(name) > 50:
            errors['name'] = '50자 이하로 입력해주세요.'
    start = _parse_date(body.get('start'))
    end = _parse_date(body.get('end'))
    if start is None:
        errors['start'] = MSG_DATE
    if end is None:
        errors['end'] = MSG_DATE
    if start and end and start > end:
        errors['end'] = MSG_ORDER
    if errors:
        return None, errors
    return {'name': name, 'start': start, 'end': end}, None


def _fail(errors):
    return jsonify({'status': 'fail', 'errors': errors}), 400


@site_info_bp.route('/api/admin/schedule', methods=['POST'])
@login_required
@master_required
def create_schedule():
    clean, errors = _validate_schedule(request.get_json(silent=True))
    if errors:
        return _fail(errors)
    item = Schedule(name=clean['name'], start_date=clean['start'], end_date=clean['end'])
    db.session.add(item)
    db.session.commit()
    return jsonify({'status': 'success', 'data': item.to_dict()}), 201


@site_info_bp.route('/api/admin/schedule/<int:schedule_id>', methods=['PUT'])
@login_required
@master_required
def update_schedule(schedule_id):
    item = db.session.get(Schedule, schedule_id)
    if item is None:
        return jsonify({'status': 'fail', 'message': '일정을 찾을 수 없습니다.'}), 404
    clean, errors = _validate_schedule(request.get_json(silent=True))
    if errors:
        return _fail(errors)
    item.name = clean['name']
    item.start_date = clean['start']
    item.end_date = clean['end']
    db.session.commit()
    return jsonify({'status': 'success', 'data': item.to_dict()})


@site_info_bp.route('/api/admin/schedule/<int:schedule_id>', methods=['DELETE'])
@login_required
@master_required
def delete_schedule(schedule_id):
    item = db.session.get(Schedule, schedule_id)
    if item is None:
        return jsonify({'status': 'fail', 'message': '일정을 찾을 수 없습니다.'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'status': 'success'})
