# routes/campus_routes.py
from flask import Blueprint, jsonify, send_from_directory
import pandas as pd
import os

campus_bp = Blueprint('campus', __name__, url_prefix='/api/campus')

# 경로 설정
BASE_DIR = os.path.abspath(os.getcwd())
BUILDING_FILE = os.path.join(BASE_DIR, 'data', 'building_info.xlsx')
FACILITY_FILE = os.path.join(BASE_DIR, 'data', 'facility_info.xlsx')
IMAGE_FOLDER = os.path.join(BASE_DIR, 'uploads', 'campus')

# 1. 캠퍼스 정보 통합 조회 API
@campus_bp.route('/info', methods=['GET'])
def get_campus_info():
    try:
        result = {}

        # --- Step 1: 건물 기본 정보 읽기 (building_info.xlsx) ---
        if os.path.exists(BUILDING_FILE):
            df_b = pd.read_excel(BUILDING_FILE).fillna('')
            for _, row in df_b.iterrows():
                b_id = str(row['building_id']).strip() # 공백 제거 등 안전처리
                result[b_id] = {
                    'name': row['building_name'],
                    'description': row['description'],
                    'facilities': [] # 시설 리스트 초기화
                }
        else:
            return jsonify({'status': 'error', 'message': '건물 정보 파일이 없습니다.'}), 500

        # --- Step 2: 시설 상세 정보 읽기 (facility_info.xlsx) ---
        if os.path.exists(FACILITY_FILE):
            df_f = pd.read_excel(FACILITY_FILE).fillna('')
            for _, row in df_f.iterrows():
                b_id = str(row['building_id']).strip()
                
                # 건물 정보가 존재하는 경우에만 시설 추가
                if b_id in result:
                    img_file = row.get('image_file', '') # 컬럼이 없을 수도 있으므로 get 사용
                    
                    facility_data = {
                        'name': row['facility_name'],
                        'loc': row['location'],
                        'desc': row['description'],
                        'imgUrl': f"/api/campus/image/{img_file}" if img_file else None
                    }
                    result[b_id]['facilities'].append(facility_data)

        return jsonify({'status': 'success', 'data': result})

    except Exception as e:
        print(f"Error: {e}") # 디버깅용 로그
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 2. 팝업 이미지 제공 API
@campus_bp.route('/image/<filename>')
def get_campus_image(filename):
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    return send_from_directory(IMAGE_FOLDER, filename)