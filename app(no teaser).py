import os
import sys
import pandas as pd
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv  # [추가] 환경변수 로드 모듈

# --- 환경 변수 로드 ---
load_dotenv()  # .env 파일을 찾아서 로드합니다.

# --- 기본 설정 ---
os.environ["PYTHONIOENCODING"] = "utf-8"

app = Flask(__name__)

# [수정] .env에서 가져오기 (없을 경우를 대비해 두 번째 인자에 기본값 설정 가능)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key') 

# CORS 설정
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- 상수 정의 ---
DATA_DIR = 'data'
STOCK_FILE = os.path.join(DATA_DIR, 'stuff_ongoing.xlsx')
LOG_FILE = os.path.join(DATA_DIR, 'borrow_log.xlsx')
MAJOR_FILE = os.path.join(DATA_DIR, 'major.xlsx') # 학과 정보 등
ADMIN_PASSWORD = 'trip0711'

# --- 헬퍼 함수 (기존 로직 유지) ---
def load_stock():
    if not os.path.exists(STOCK_FILE):
        return pd.DataFrame(columns=['물품', '재고현황', '카테고리'])
    df = pd.read_excel(STOCK_FILE, dtype=str)
    df.fillna('', inplace=True)
    # 재고현황 숫자로 변환 (확인중 -1 처리를 위해)
    df['재고현황'] = pd.to_numeric(df['재고현황'], errors='coerce').fillna(0).astype(int)
    return df

def save_stock(df):
    df.to_excel(STOCK_FILE, index=False)

def load_log():
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=['이름','전화번호','학번','학과','대여물품','대여담당자','대여시각','대여현황','반납담당자','반납시각'])
    return pd.read_excel(LOG_FILE, dtype=str).fillna('')

def save_log(df):
    df.to_excel(LOG_FILE, index=False)

# ==========================
# [API] 사용자용
# ==========================

# 1. 물품 목록 가져오기 (대여 페이지용)
@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        df = load_stock()
        # DataFrame -> List of Dict 변환
        items = df.to_dict(orient='records')
        return jsonify({'status': 'success', 'data': items})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 2. 학과 목록 가져오기 (드롭다운용)
@app.route('/api/departments', methods=['GET'])
def get_departments():
    try:
        if os.path.exists(MAJOR_FILE):
            df = pd.read_excel(MAJOR_FILE)
            depts = df['학과명'].dropna().tolist()
            return jsonify({'status': 'success', 'data': depts})
        return jsonify({'status': 'success', 'data': []})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 3. 대여 신청하기
@app.route('/api/borrow', methods=['POST'])
def borrow_item():
    data = request.get_json() # React에서 보낸 JSON 데이터 받기
    
    # 데이터 추출
    name = data.get('name')
    student_id = data.get('student_id')
    dept = data.get('department')
    phone = data.get('phone')
    selected_items = data.get('selected_items', []) # 리스트 형태 ['우산', '볼펜']

    if not all([name, student_id, dept, phone, selected_items]):
        return jsonify({'status': 'fail', 'message': '모든 정보를 입력해주세요.'}), 400

    stock_df = load_stock()
    log_df = load_log()
    
    # 재고 확인 및 차감 로직
    for item_name in selected_items:
        idx = stock_df.index[stock_df['물품'] == item_name].tolist()
        if not idx:
            return jsonify({'status': 'fail', 'message': f'{item_name} 은(는) 없는 물품입니다.'}), 400
        
        current_stock = stock_df.loc[idx[0], '재고현황']
        if current_stock <= 0:
            return jsonify({'status': 'fail', 'message': f'{item_name} 재고가 부족합니다.'}), 400
            
        stock_df.loc[idx[0], '재고현황'] -= 1

    # 로그 저장
    new_log = {
        '이름': name,
        '전화번호': phone,
        '학번': student_id,
        '학과': dept,
        '대여물품': ", ".join(selected_items),
        '대여담당자': '', # 승인 전이므로 비워둠
        '대여시각': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '대여현황': '신청',
        '반납담당자': '',
        '반납시각': ''
    }
    
    log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
    
    save_stock(stock_df)
    save_log(log_df)

    return jsonify({'status': 'success', 'message': '신청되었습니다.'})

# 4. 대여 현황 조회 (로그인 없이 이름/학번으로 조회)
@app.route('/api/check', methods=['POST'])
def check_status():
    data = request.get_json()
    name = data.get('name')
    student_id = data.get('student_id')

    log_df = load_log()
    
    # 필터링
    matches = log_df[
        (log_df['이름'] == name) & 
        (log_df['학번'] == student_id)
    ].copy()

    if matches.empty:
        return jsonify({'status': 'fail', 'message': '기록이 없습니다.'})

    # 반납 기한 계산 (대여시각 + 7일) 등 필요한 정보 가공
    result_list = []
    for _, row in matches.iterrows():
        borrow_time_str = str(row['대여시각'])
        try:
            borrow_dt = datetime.strptime(borrow_time_str, '%Y-%m-%d %H:%M:%S')
            return_due = (borrow_dt + timedelta(days=7)).strftime('%Y-%m-%d')
        except:
            return_due = '-'

        result_list.append({
            'items': row['대여물품'],
            'date': borrow_time_str,
            'status': row['대여현황'],
            'due_date': return_due
        })

    # 최신순 정렬
    result_list.reverse()
    
    return jsonify({
        'status': 'success', 
        'data': result_list,
        'user_info': {'name': name, 'student_id': student_id}
    })


# ==========================
# [API] 관리자용
# ==========================

# 5. 관리자 로그인
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')

    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({'status': 'success', 'message': '로그인 성공'})
    else:
        return jsonify({'status': 'fail', 'message': '비밀번호가 틀렸습니다.'}), 401

# 6. 관리자 - 대시보드 데이터
@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    # 실제 배포시엔 @login_required 데코레이터 등을 사용하는 것이 좋음
    # 여기선 간단히 세션 체크 예시
    # if not session.get('is_admin'):
    #     return jsonify({'status': 'fail', 'message': 'Unauthorized'}), 401

    log_df = load_log()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 금일 대여 건수 (대여시각에 오늘 날짜가 포함된 것)
    today_count = log_df[log_df['대여시각'].astype(str).str.contains(today)].shape[0]
    
    # 최근 기록 5개
    recent_logs = log_df.tail(5).to_dict(orient='records')[::-1]

    return jsonify({
        'status': 'success',
        'today_count': today_count,
        'recent_logs': recent_logs
    })

# (참고) 나머지 승인/반납/재고 API는 위와 비슷한 패턴으로 추가하면 됩니다.

if __name__ == '__main__':
    # Docker에서는 host='0.0.0.0'이 필수입니다.
    app.run(host='0.0.0.0', port=5000, debug=False)