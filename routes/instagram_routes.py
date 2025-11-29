# routes/instagram_routes.py
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from models import db, InstaPost
from extensions import limiter, login_required

insta_bp = Blueprint('instagram', __name__, url_prefix='/api/instagram')

# 이미지 저장 경로 설정 (uploads/instagram 폴더 사용)
BASE_DIR = os.path.abspath(os.getcwd())
INSTA_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'instagram')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(INSTA_UPLOAD_FOLDER):
    os.makedirs(INSTA_UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. 목록 조회 (누구나 가능) ---
@insta_bp.route('/posts', methods=['GET'])
def get_posts():
    # 최신순으로 7개만 가져오기
    posts = InstaPost.query.order_by(InstaPost.created_at.desc()).limit(7).all()
    
    data = []
    for post in posts:
        data.append({
            'id': post.id,
            # 프론트에서 보여줄 이미지 URL (API 경로)
            'imgUrl': f"/api/instagram/image/{post.img_filename}", 
            'link': post.link_url
        })
    
    # 데이터가 없으면 더미 데이터 반환 (선택사항, 필요 없으면 빈 배열 [])
    if not data:
        return jsonify({'status': 'success', 'data': []})

    return jsonify({'status': 'success', 'data': data})

# --- 2. 게시물 등록 (관리자 전용) ---
@insta_bp.route('', methods=['POST'])
@login_required
def create_post():
    link_url = request.form.get('link_url')
    
    if not link_url or 'file' not in request.files:
        return jsonify({'error': '링크와 이미지는 필수입니다.'}), 400
        
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # 파일명 중복 방지를 위해 시간 등을 붙여도 좋지만, 여기선 간단히 저장
        import time
        filename = f"{int(time.time())}_{filename}"
        
        file.save(os.path.join(INSTA_UPLOAD_FOLDER, filename))
        
        new_post = InstaPost(img_filename=filename, link_url=link_url)
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({'message': '등록 성공'}), 201
        
    return jsonify({'error': '파일 형식이 올바르지 않습니다.'}), 400

# --- 3. 게시물 삭제 (관리자 전용) ---
@insta_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_post(id):
    post = InstaPost.query.get_or_404(id)
    
    # 파일 삭제
    file_path = os.path.join(INSTA_UPLOAD_FOLDER, post.img_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': '삭제 성공'})

# --- 4. 이미지 파일 제공 (GET) ---
@insta_bp.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(INSTA_UPLOAD_FOLDER, filename)