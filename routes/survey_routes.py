# routes/survey_routes.py
from datetime import date, datetime

from flask import Blueprint, request, jsonify, session, abort

from models import db, Survey
from extensions import limiter, login_required, master_required

survey_bp = Blueprint('survey', __name__, url_prefix='/api/surveys')

ERR_REQUIRED = '제목, 내용, 설문 링크는 필수입니다.'
ERR_LINK = '설문 링크는 http:// 또는 https://로 시작해야 합니다.'
ERR_DATE = '마감일은 YYYY-MM-DD 형식으로 입력해주세요.'
ERR_LENGTH = '입력 길이를 초과했습니다.'
ERR_PUBLIC = '공개 여부 값이 올바르지 않습니다.'

REQUIRED = ('title', 'content', 'link_url')
OPTIONAL_TEXT = ('duration', 'reward')
MAX_LEN = {'title': 200, 'link_url': 500, 'duration': 30, 'reward': 50}


def _text(value):
    return value.strip() if isinstance(value, str) else ''


def parse_survey_payload(data, partial=False):
    """요청 본문을 검증한다. (필드 dict, None) 또는 (None, 오류 문구)를 돌려준다.

    partial=True면 요청에 있는 키만 검증해 돌려준다(수정용).
    """
    if not isinstance(data, dict):
        return None, ERR_REQUIRED

    fields = {}

    for key in REQUIRED:
        if partial and key not in data:
            continue
        value = _text(data.get(key))
        if not value:
            return None, ERR_REQUIRED
        fields[key] = value

    link = fields.get('link_url')
    if link is not None and not link.lower().startswith(('http://', 'https://')):
        return None, ERR_LINK

    for key in OPTIONAL_TEXT:
        if partial and key not in data:
            continue
        fields[key] = _text(data.get(key)) or None

    for key, limit in MAX_LEN.items():
        if fields.get(key) and len(fields[key]) > limit:
            return None, ERR_LENGTH

    if not partial or 'deadline' in data:
        raw = data.get('deadline')
        if raw is None or raw == '':
            fields['deadline'] = None
        else:
            try:
                fields['deadline'] = datetime.strptime(_text(raw), '%Y-%m-%d').date()
            except ValueError:
                return None, ERR_DATE

    if 'is_public' in data:
        # 문자열 "false" 등이 True로 바뀌어 비공개 글이 공개되지 않도록 불리언만 받는다
        if not isinstance(data['is_public'], bool):
            return None, ERR_PUBLIC
        fields['is_public'] = data['is_public']
    elif not partial:
        fields['is_public'] = True

    return fields, None


def _sort_key(survey):
    """진행중(마감 임박순, 상시는 뒤) -> 마감(최근 마감순). 같은 조건이면 최신 글 먼저."""
    newest = (-survey.created_at.timestamp(), -survey.id)
    if survey.is_closed:
        return (1, -survey.deadline.toordinal(), *newest)
    return (0, (survey.deadline or date.max).toordinal(), *newest)


# --- 목록 조회 (GET) ---
@survey_bp.route('', methods=['GET'])
@limiter.limit("70 per minute")
def get_surveys():
    query = Survey.query.filter_by(is_public=True)
    # 관리자가 명시적으로 요청했을 때만 비공개 포함
    if session.get('is_admin') and request.args.get('include_private') == 'true':
        query = Survey.query

    surveys = sorted(query.all(), key=_sort_key)
    return jsonify([s.to_dict() for s in surveys])


# --- 상세 조회 + 조회수 증가 (GET) ---
@survey_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("70 per minute")
def get_survey_detail(id):
    survey = db.session.get(Survey, id)
    # 비공개 글은 관리자에게만 보인다
    if survey is None or (not survey.is_public and not session.get('is_admin')):
        abort(404)

    if request.args.get('increment') == 'true':
        survey.views = (survey.views or 0) + 1
        db.session.commit()

    return jsonify(survey.to_dict())


# --- 등록 (POST) ---
@survey_bp.route('', methods=['POST'])
@login_required
def create_survey():
    fields, error = parse_survey_payload(request.get_json(silent=True))
    if error:
        return jsonify({'error': error}), 400

    survey = Survey(**fields)
    db.session.add(survey)
    db.session.commit()
    return jsonify({'message': '등록 성공', 'data': survey.to_dict()}), 201


# --- 수정 (PUT) ---
@survey_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_survey(id):
    survey = db.session.get(Survey, id)
    if survey is None:
        abort(404)

    # 요청에 없는 값은 그대로 둔다 (공개 여부가 실수로 바뀌지 않게)
    fields, error = parse_survey_payload(request.get_json(silent=True), partial=True)
    if error:
        return jsonify({'error': error}), 400

    for key, value in fields.items():
        setattr(survey, key, value)
    db.session.commit()
    return jsonify({'message': '수정 성공', 'data': survey.to_dict()})


# --- 삭제 (DELETE) ---
# login_required가 바깥: 비로그인은 401, 로그인한 sub는 403
@survey_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@master_required
def delete_survey(id):
    survey = db.session.get(Survey, id)
    if survey is None:
        abort(404)
    db.session.delete(survey)
    db.session.commit()
    return jsonify({'message': '삭제 성공'})
