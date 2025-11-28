# extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session, jsonify
from functools import wraps

# 1. Limiter 객체 생성 (app 없이 먼저 껍데기만 생성)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# 2. 로그인 필수 데코레이터 이동
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'}), 401
        return f(*args, **kwargs)
    return decorated_function