# routes/survey_routes.py
from datetime import datetime

from flask import Blueprint, request, jsonify, session, abort

from models import db, Survey
from extensions import limiter, login_required

survey_bp = Blueprint('survey', __name__, url_prefix='/api/surveys')

ERR_REQUIRED = '제목, 내용, 설문 링크는 필수입니다.'
ERR_LINK = '설문 링크는 http:// 또는 https://로 시작해야 합니다.'
ERR_DATE = '마감일은 YYYY-MM-DD 형식으로 입력해주세요.'
ERR_LENGTH = '입력 길이를 초과했습니다.'

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
        fields['is_public'] = bool(data['is_public'])
    elif not partial:
        fields['is_public'] = True

    return fields, None


# --- 상세 조회 + 조회수 증가 (GET) ---
@survey_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per minute")
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
