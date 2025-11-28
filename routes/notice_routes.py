# routes/notice_routes.py
from flask import Blueprint, request, jsonify, send_from_directory
import os
import shutil 
from models import db, Notice, NoticeFile
from extensions import limiter, login_required

notice_bp = Blueprint('notice', __name__, url_prefix='/api/notices')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'hwp', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. 목록 조회 (GET) ---
@notice_bp.route('', methods=['GET'])
@limiter.limit("30 per minute")
def get_notices():
    # 고정 공지 우선, 그 다음 최신순 정렬
    notices = Notice.query.order_by(Notice.fixed.desc(), Notice.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notices])

# --- 2. 상세 조회 + 조회수 증가 (GET) ---
@notice_bp.route('/<int:id>', methods=['GET'])
@limiter.limit("30 per minute")
def get_notice_detail(id):
    notice = Notice.query.get_or_404(id)
    
    # [확인 완료] URL 파라미터가 'true'일 때만 조회수 증가
    # 프론트엔드에서 /api/notices/1?increment=false 로 요청하면 절대 안 오름
    if request.args.get('increment') == 'true':
        notice.views += 1
        db.session.commit()
    
    return jsonify(notice.to_dict())

# --- 3. 공지 등록 (POST) ---
@notice_bp.route('', methods=['POST'])
@login_required
def create_notice():
    title = request.form.get('title')
    content = request.form.get('content')
    author = request.form.get('author', '여정 학생회')
    fixed = request.form.get('fixed') == 'true'
    
    if not title or not content:
        return jsonify({'error': '제목과 내용은 필수입니다.'}), 400

    try:
        new_notice = Notice(title=title, content=content, author=author, fixed=fixed)
        db.session.add(new_notice)
        db.session.flush() # ID 생성
        notice_id = str(new_notice.id)

        # [수정] 다중 파일 처리
        if 'files' in request.files:
            files = request.files.getlist('files') # 리스트로 받기
            
            save_path = os.path.join(UPLOAD_FOLDER, notice_id)
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = os.path.basename(file.filename)
                    file.save(os.path.join(save_path, filename))
                    
                    # DB에 파일 정보 추가
                    new_file = NoticeFile(notice_id=new_notice.id, filename=filename)
                    db.session.add(new_file)

        db.session.commit()
        return jsonify({'message': '등록 성공', 'data': new_notice.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 4. 공지 수정 (PUT) ---
@notice_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_notice(id):
    notice = Notice.query.get_or_404(id)
    
    notice.title = request.form.get('title')
    notice.content = request.form.get('content')
    notice.fixed = request.form.get('fixed') == 'true'
    
    # [수정] 추가 파일 업로드
    if 'files' in request.files:
        files = request.files.getlist('files')
        save_path = os.path.join(UPLOAD_FOLDER, str(id))
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = os.path.basename(file.filename)
                file.save(os.path.join(save_path, filename))
                
                # 중복 방지 (같은 이름이 없을 때만 DB 추가)
                exists = NoticeFile.query.filter_by(notice_id=id, filename=filename).first()
                if not exists:
                    new_file = NoticeFile(notice_id=id, filename=filename)
                    db.session.add(new_file)
            
    db.session.commit()
    return jsonify({'message': '수정 성공'})

# --- 5. [신규] 개별 파일 삭제 API (수정 페이지에서 사용) ---
@notice_bp.route('/file/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    file_record = NoticeFile.query.get_or_404(file_id)
    notice_id = str(file_record.notice_id)
    filename = file_record.filename
    
    # 1. 실제 파일 삭제
    file_path = os.path.join(UPLOAD_FOLDER, notice_id, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 2. DB 삭제
    db.session.delete(file_record)
    db.session.commit()
    return jsonify({'message': '파일 삭제 성공'})

# --- 6. 공지 삭제 (DELETE) ---
@notice_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_notice(id):
    notice = Notice.query.get_or_404(id)
    db.session.delete(notice)
    db.session.commit()

    folder_path = os.path.join(UPLOAD_FOLDER, str(id))
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    return jsonify({'message': '삭제 성공'})

# --- 7. 파일 다운로드 (GET) ---
@notice_bp.route('/download/<int:notice_id>/<filename>')
def download_file(notice_id, filename):
    target_dir = os.path.join(UPLOAD_FOLDER, str(notice_id))
    return send_from_directory(target_dir, filename, as_attachment=True)