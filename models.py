# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. 공지사항 테이블
class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), default='여정 학생회')
    views = db.Column(db.Integer, default=0)
    fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    files = db.relationship('NoticeFile', backref='notice', cascade='all, delete-orphan')
    is_public = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'views': self.views,
            'fixed': self.fixed,
            'is_public': self.is_public,
            'date': self.created_at.strftime('%Y-%m-%d'),
            'files': [f.to_dict() for f in self.files]
        }

# 2. [신규] 첨부파일 테이블
class NoticeFile(db.Model):
    __tablename__ = 'notice_files'
    
    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False) # 원본 파일명
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename
        }
    
# 3. 학사일정 테이블 (기존 유지)
class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))

    def to_dict(self):
        return {'name': self.name, 'start': self.start_date, 'end': self.end_date}
    
# 4. [NEW] 인스타그램 대체 테이블
class InstaPost(db.Model):
    __tablename__ = 'insta_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    img_filename = db.Column(db.String(300), nullable=False) # 업로드한 이미지 파일명
    link_url = db.Column(db.String(500), nullable=False)     # 클릭 시 이동할 인스타 주소
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'img_filename': self.img_filename,
            'link_url': self.link_url
        }