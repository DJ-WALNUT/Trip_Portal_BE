import os
import pandas as pd
import csv
from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from threading import Lock
from functools import wraps

# [NEW] 모델 및 라우트 임포트
from models import db, Schedule
from extensions import limiter, login_required 
from routes.notice_routes import notice_bp  # (앞서 작성한 공지사항 코드)
from routes.instagram_routes import insta_bp # (방금 작성한 인스타 코드)

# --- 환경 변수 로드 ---
load_dotenv()  # .env 파일을 찾아서 로드합니다.
data_lock = Lock()  # 데이터 접근 시 사용할 Lock 객체

# --- 기본 설정 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

app = Flask(__name__)
limiter.init_app(app) # [추가] Limiter를 app과 연결 (초기화)

# [수정] .env에서 가져오기 (없을 경우를 대비해 두 번째 인자에 기본값 설정 가능)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
# [수정] 비밀번호를 환경 변수에서 가져옴
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') 

# DB 설정 (SQLite)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'data', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# [NEW] DB 초기화 및 Blueprint 등록
db.init_app(app)
app.register_blueprint(notice_bp)
app.register_blueprint(insta_bp)

# CORS 설정
allowed_origins = [
    "http://localhost:3000",             # 로컬 개발용
    "http://localhost:5173",             # 로컬 개발용
    "http://localhost:5174",             # 로컬 개발용
    "https://cukeng.kr"                  # 여정 도메인
]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

# 한국 시간(KST) 설정
KST = timezone(timedelta(hours=9))

# --- 상수 정의 ---
DATA_DIR = 'data'
STOCK_FILE = os.path.join(DATA_DIR, 'stuff_ongoing.xlsx')
LOG_FILE = os.path.join(DATA_DIR, 'borrow_log.xlsx')
MAJOR_FILE = os.path.join(DATA_DIR, 'major.xlsx')
TEASER_FILE = os.path.join(DATA_DIR, 'teaser_entries.csv')

# --- 헬퍼 함수 ---
def load_stock():
    if not os.path.exists(STOCK_FILE):
        return pd.DataFrame(columns=['물품', '재고현황', '카테고리'])
    df = pd.read_excel(STOCK_FILE, dtype=str)
    df.fillna('', inplace=True)
    df['재고현황'] = pd.to_numeric(df['재고현황'], errors='coerce').fillna(0).astype(int)
    return df

def save_stock(df):
    df.to_excel(STOCK_FILE, index=False)

def load_log():
    if not os.path.exists(LOG_FILE):
        cols = ['이름','전화번호','학번','학과','대여물품','대여담당자','대여시각','대여현황','반납담당자','반납시각']
        return pd.DataFrame(columns=cols)
    df = pd.read_excel(LOG_FILE, dtype=str)
    return df.fillna('')

def save_log(df):
    df.to_excel(LOG_FILE, index=False)

# [보안] 엑셀 인젝션 방지 함수 (입력값 맨 앞이 =, +, -, @ 이면 ' 붙이기)
def sanitize_input(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

# [NEW] 관리자 세션 체크 API
# 프론트엔드가 페이지 이동할 때마다 "나 아직 로그인 상태 맞아?" 하고 물어보는 용도
@app.route('/api/admin/check-session', methods=['GET'])
def check_session():
    if session.get('is_admin'):
        return jsonify({'status': 'success', 'is_admin': True})
    return jsonify({'status': 'fail', 'message': '세션 만료'}), 401

# ==========================
# [NEW] 학사일정 API (DB 사용)
# ==========================
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    schedules = Schedule.query.all()
    # 만약 DB가 비어있으면 초기 데이터 삽입 (선택사항)
    return jsonify([s.to_dict() for s in schedules])

# ==========================
# [신규] 티저 이벤트 API (CSV 저장)
# ==========================
@app.route('/api/teaser/entry', methods=['POST'])
@limiter.limit("5 per minute")
def teaser_entry():
    try:
        data = request.get_json()
        name = sanitize_input(data.get('name'))
        student_id = sanitize_input(data.get('student_id'))
        dept = sanitize_input(data.get('department'))
        phone = sanitize_input(data.get('phone'))
        agreed = data.get('agreed')

        if not all([name, student_id, dept, phone, agreed]):
            return jsonify({'status': 'fail', 'message': '모든 정보를 입력해주세요.'}), 400

        file_exists = os.path.isfile(TEASER_FILE)
        
        # 전화번호 앞의 0을 보존하기 위해 문자열로 저장 ('010...')
        with open(TEASER_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['신청시각', '이름', '학번', '학과', '전화번호', '동의여부'])
            
            entry_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([entry_time, name, student_id, dept, phone, 'Y' if agreed else 'N'])

        return jsonify({'status': 'success', 'message': '응모 완료'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
# 2. [신규] 티저 응모 목록 조회 (관리자용)
@app.route('/api/admin/teaser', methods=['GET'])
@login_required
def get_teaser_entries():
    try:
        if not os.path.exists(TEASER_FILE):
             return jsonify({'status': 'success', 'data': []})
        
        # [수정] 전화번호 0 살리기: dtype=str로 읽어서 숫자로 변환되는 것 방지
        df = pd.read_csv(TEASER_FILE, dtype={'전화번호': str, '학번': str})
        
        # 혹시 이미 숫자로 저장되어 '101234...'로 읽혔을 경우를 대비해 '0' 붙이기
        if not df.empty and '전화번호' in df.columns:
            df['전화번호'] = df['전화번호'].apply(lambda x: '0' + str(x) if str(x).startswith('10') else str(x))

        if not df.empty:
            df = df.sort_values(by='신청시각', ascending=False)
            
        return jsonify({'status': 'success', 'data': df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================
# [기존] 재고 관리 API (통합됨)
# ==========================
@app.route('/api/admin/stock/update', methods=['POST'])
@login_required
def update_stock():
    try:
        data = request.get_json()
        new_items = data.get('items')
        df = pd.DataFrame(new_items)
        save_stock(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})

@app.route('/api/admin/stock/add', methods=['POST'])
@login_required
def add_stock_item():
    try:
        data = request.get_json()
        name = sanitize_input(data.get('name'))
        count = data.get('count')
        category = sanitize_input(data.get('category') or '반납물품')

        stock_df = load_stock()
        new_row = {'물품': name, '재고현황': count, '카테고리': category}
        stock_df = pd.concat([stock_df, pd.DataFrame([new_row])], ignore_index=True)
        save_stock(stock_df)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})

@app.route('/api/admin/stock/delete', methods=['POST'])
@login_required
def delete_stock_item():
    try:
        data = request.get_json()
        name = data.get('name')
        stock_df = load_stock()
        stock_df = stock_df[stock_df['물품'] != name]
        save_stock(stock_df)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)})

# ==========================
# [기존] 사용자/관리자 API
# ==========================
@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        df = load_stock()
        return jsonify({'status': 'success', 'data': df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/departments', methods=['GET'])
def get_departments():
    try:
        if os.path.exists(MAJOR_FILE):
            df = pd.read_excel(MAJOR_FILE)
            depts = df['학과명'].dropna().tolist()
            return jsonify({'status': 'success', 'data': depts})
        else:
            return jsonify({'status': 'success', 'data': []})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/borrow', methods=['POST'])
@limiter.limit("10 per minute")
def borrow_item():
    data = request.get_json()
    selected_items = data.get('selected_items', []) 

    with data_lock:
        stock_df = load_stock()
    
        for item_name in selected_items:
            idx = stock_df.index[stock_df['물품'] == item_name].tolist()
            if not idx:
                return jsonify({'status': 'fail', 'message': f'{item_name} 없는 물품입니다.'})
            stock_idx = idx[0]
            if stock_df.loc[stock_idx, '재고현황'] <= 0:
                return jsonify({'status': 'fail', 'message': f'{item_name} 재고가 부족합니다.'})
            stock_df.loc[stock_idx, '재고현황'] -= 1

        log_df = load_log()
        new_log = {
            '이름': sanitize_input(data.get('name')),
            '전화번호': sanitize_input(data.get('phone')),
            '학번': sanitize_input(data.get('student_id')),
            '학과': sanitize_input(data.get('department')),
            '대여물품': ", ".join(selected_items),
            '대여담당자': '', 
            '대여시각': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S'),
            '대여현황': '신청',
            '반납담당자': '',
            '반납시각': ''
        }
        log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
        save_stock(stock_df)
        save_log(log_df)
    return jsonify({'status': 'success'})

@app.route('/api/check', methods=['POST'])
def check_status():
    data = request.get_json()
    name = data.get('name')
    student_id = data.get('student_id')
    log_df = load_log()
    matches = log_df[(log_df['이름'] == name) & (log_df['학번'] == student_id)].copy()
    if matches.empty:
        return jsonify({'status': 'fail', 'message': '기록이 없습니다.'})

    result_list = []
    for _, row in matches.iterrows():
        try:
            borrow_dt = datetime.strptime(str(row['대여시각']), '%Y-%m-%d %H:%M:%S')
            due_date = (borrow_dt + timedelta(days=7)).strftime('%Y-%m-%d')
        except:
            due_date = '-'
        result_list.append({
            'items': row['대여물품'],
            'date': str(row['대여시각']),
            'status': row['대여현황'],
            'due_date': due_date
        })
    result_list.reverse()
    return jsonify({'status': 'success', 'data': result_list, 'user_info': {'name': name, 'student_id': student_id}})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail', 'message': '비밀번호 불일치'}), 401
    
# [NEW] 관리자 로그아웃 API
@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    # 세션에서 관리자 권한 제거
    session.pop('is_admin', None)
    return jsonify({'status': 'success', 'message': '로그아웃 되었습니다.'})

@app.route('/api/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    log_df = load_log()
    today = datetime.now(KST).strftime('%Y-%m-%d')
    today_count = log_df[log_df['대여시각'].astype(str).str.contains(today)].shape[0]
    recent_logs = log_df.tail(5).to_dict(orient='records')[::-1]
    return jsonify({'status': 'success', 'today_count': today_count, 'recent_logs': recent_logs})

@app.route('/api/admin/requests', methods=['GET'])
@login_required
def get_requests():
    log_df = load_log()
    log_df['id'] = log_df.index 
    requests = log_df[log_df['대여현황'] == '신청'].copy()
    data = []
    for _, row in requests.iterrows():
        data.append({
            'id': int(row['id']),
            'date': row['대여시각'],
            'name': row['이름'],
            'student_id': row['학번'],
            'items': row['대여물품']
        })
    data.reverse()
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/admin/approve', methods=['POST'])
@login_required
def approve_request():
    data = request.get_json()
    log_id = data.get('id')
    handler = data.get('handler')
    log_df = load_log()
    stock_df = load_stock()

    if log_id < len(log_df):
        items_str = log_df.loc[log_id, '대여물품']
        items_list = items_str.split(', ')
        is_all_disposable = True
        for item_name in items_list:
            stock_row = stock_df[stock_df['물품'] == item_name]
            if not stock_row.empty:
                if stock_row.iloc[0]['카테고리'] != '일회용품':
                    is_all_disposable = False
                    break
            else:
                is_all_disposable = False
        
        if is_all_disposable:
            log_df.loc[log_id, '대여현황'] = '반납완료'
            log_df.loc[log_id, '반납시각'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
        else:
            log_df.loc[log_id, '대여현황'] = '미반납'
            
        log_df.loc[log_id, '대여담당자'] = handler
        save_log(log_df)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route('/api/admin/reject', methods=['POST'])
@login_required
def reject_request():
    data = request.get_json()
    log_id = data.get('id')
    log_df = load_log()
    stock_df = load_stock()

    if log_id < len(log_df):
        items_str = log_df.loc[log_id, '대여물품']
        items_list = items_str.split(', ')
        for item_name in items_list:
            idx = stock_df.index[stock_df['물품'] == item_name].tolist()
            if idx:
                stock_df.loc[idx[0], '재고현황'] += 1
        
        log_df = log_df.drop(log_id).reset_index(drop=True)
        save_stock(stock_df)
        save_log(log_df)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route('/api/admin/ongoing', methods=['GET'])
@login_required
def get_ongoing():
    log_df = load_log()
    log_df['id'] = log_df.index
    ongoing = log_df[log_df['대여현황'] == '미반납'].copy()
    data = []
    for _, row in ongoing.iterrows():
        data.append({
            'id': int(row['id']),
            'date': row['대여시각'],
            'name': row['이름'],
            'student_id': row['학번'],
            'phone': row['전화번호'],
            'items': row['대여물품']
        })
    data.reverse()
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/admin/return', methods=['POST'])
@login_required
def return_item():
    data = request.get_json()
    log_id = data.get('id')
    handler = data.get('handler')
    log_df = load_log()
    stock_df = load_stock()
    
    if log_id < len(log_df):
        items_str = log_df.loc[log_id, '대여물품']
        items_list = items_str.split(', ')
        for item_name in items_list:
            idx = stock_df.index[stock_df['물품'] == item_name].tolist()
            if idx:
                stock_idx = idx[0]
                category = stock_df.loc[stock_idx, '카테고리']
                if category != '일회용품' and stock_df.loc[stock_idx, '재고현황'] != -1:
                    stock_df.loc[stock_idx, '재고현황'] += 1

        log_df.loc[log_id, '대여현황'] = '반납완료'
        log_df.loc[log_id, '반납담당자'] = handler
        log_df.loc[log_id, '반납시각'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
        save_stock(stock_df)
        save_log(log_df)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route('/api/admin/logs', methods=['GET'])
@login_required
def get_all_logs():
    log_df = load_log()
    data = log_df.to_dict(orient='records')[::-1]
    return jsonify({'status': 'success', 'data': data})

# ==========================
# [수정] 엑셀 다운로드 API (파일명 + 시각 설정)
# ==========================
@app.route('/api/admin/download_log', methods=['GET'])
@login_required
def download_log_file():
    if os.path.exists(LOG_FILE):
        # 1. 현재 시간(KST) 구하기
        timestamp = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
        
        # 2. 파일명 생성 (예: 대여반납기록_20251121_123000.xlsx)
        custom_filename = f"대여반납기록_{timestamp}.xlsx"
        
        # 3. 파일 전송 (download_name 옵션 사용)
        return send_file(
            LOG_FILE, 
            as_attachment=True, 
            download_name=custom_filename
        )
    return "파일이 없습니다.", 404

# --- 서버 시작 시 DB 테이블 생성 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # notices, schedules 테이블 생성
        
        # 학사일정 초기 데이터가 없으면 넣기 (편의용)
        if not Schedule.query.first():
            print("Initialize Schedule Data...")
            initial_schedules = [
                Schedule(name='2025-2', start_date='2025-09-02', end_date='2025-12-20'),
                Schedule(name='2026-1', start_date='2026-03-02', end_date='2026-06-19'),
                Schedule(name='2026-2', start_date='2026-09-01', end_date='2026-12-21'),
                Schedule(name='2027-1', start_date='2027-03-02', end_date='2027-06-18'),
            ]
            db.session.add_all(initial_schedules)
            db.session.commit()

    app.run(host='0.0.0.0', port=5000, debug=True)