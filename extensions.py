# extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request, session, jsonify
from functools import wraps

def client_ip():
    """요청 제한을 셀 기준이 되는 방문자 IP.

    운영 서버는 Cloudflare -> 시놀로지 역방향 프록시 -> Flask 순서라서
    remote_addr는 항상 프록시 주소다. 그대로 쓰면 모든 방문자가 한도 하나를 함께 쓴다.
    Cloudflare가 넣어 주는 CF-Connecting-IP(실제 방문자 IP)를 우선 사용하고,
    없으면(로컬 개발 등) 접속 주소로 대신한다.
    """
    return (request.headers.get('CF-Connecting-IP') or '').strip() or get_remote_address()


# 1. Limiter 객체 생성 (app 없이 먼저 껍데기만 생성)
limiter = Limiter(
    key_func=client_ip,
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

def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin') or session.get('role') != 'master':
            return jsonify({'status': 'fail', 'message': '마스터 권한이 필요합니다.'}), 403
        return f(*args, **kwargs)
    return decorated_function