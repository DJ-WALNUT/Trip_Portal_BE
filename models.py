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

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'views': self.views,
            'fixed': self.fixed,
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