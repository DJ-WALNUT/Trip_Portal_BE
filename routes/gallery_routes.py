# routes/gallery_routes.py
import os
from flask import Blueprint, jsonify, send_from_directory
from extensions import limiter

gallery_bp = Blueprint('gallery', __name__, url_prefix='/api/gallery')

# 사진 저장 경로 설정 (./uploads/title)
BASE_DIR = os.path.abspath(os.getcwd())
GALLERY_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'title')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 폴더가 없으면 생성
if not os.path.exists(GALLERY_UPLOAD_FOLDER):
    os.makedirs(GALLERY_UPLOAD_FOLDER)

def is_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. 사진 목록 전체 조회 ---
@gallery_bp.route('', methods=['GET'])
@limiter.exempt
def get_gallery_list():
    try:
        # 폴더 내 파일 목록 읽기
        files = os.listdir(GALLERY_UPLOAD_FOLDER)
        # 이미지 파일만 필터링
        image_files = [f for f in files if is_image_file(f)]
        
        # 파일명을 기반으로 프론트엔드가 접근 가능한 URL 생성
        # DomeGallery가 기대하는 [{src, alt}, ...] 형식으로 반환
        data = []
        for f in image_files:
            data.append({
                "src": f"/api/gallery/image/{f}",
                "alt": "여정 갤러리 이미지"
            })
            
        return jsonify(data) # 프론트엔드에서 res.data로 바로 받음
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 2. 이미지 파일 제공 API ---
@gallery_bp.route('/image/<filename>')
@limiter.exempt
def get_gallery_image(filename):
    return send_from_directory(GALLERY_UPLOAD_FOLDER, filename)