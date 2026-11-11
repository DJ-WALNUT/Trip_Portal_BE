# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta

db = SQLAlchemy()
# 한국 시간(KST) 정의 추가
KST = timezone(timedelta(hours=9))

# 1. 공지사항 테이블
class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(50), default='여정 학생회')
    views = db.Column(db.Integer, default=0)
    fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))
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
        return {'id': self.id, 'name': self.name, 'start': self.start_date, 'end': self.end_date}
    
# 4. [NEW] 인스타그램 대체 테이블
class InstaPost(db.Model):
    __tablename__ = 'insta_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    img_filename = db.Column(db.String(300), nullable=False) # 업로드한 이미지 파일명
    link_url = db.Column(db.String(500), nullable=False)     # 클릭 시 이동할 인스타 주소
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))

    def to_dict(self):
        return {
            'id': self.id,
            'img_filename': self.img_filename,
            'link_url': self.link_url
        }

# 5. 사이트 설정 테이블 (키-값, 값은 JSON 직렬화)
class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))
    updated_by = db.Column(db.String(20))


def today_kst():
    """한국 시간 기준 오늘 날짜."""
    return datetime.now(KST).date()


# 6. 설문조사 테이블
class Survey(db.Model):
    __tablename__ = 'surveys'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    deadline = db.Column(db.Date)            # 비어 있으면 상시
    duration = db.Column(db.String(30))      # 예상 소요시간
    reward = db.Column(db.String(50))        # 보상
    author = db.Column(db.String(50), default='여정 학생회')
    views = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(KST))

    @property
    def is_closed(self):
        # 마감일 당일(KST)까지는 진행중
        return self.deadline is not None and today_kst() > self.deadline

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'link_url': self.link_url,
            'deadline': self.deadline.strftime('%Y-%m-%d') if self.deadline else None,
            'duration': self.duration,
            'reward': self.reward,
            'author': self.author,
            'views': self.views,
            'is_public': self.is_public,
            'date': self.created_at.strftime('%Y-%m-%d'),
            'is_closed': self.is_closed,
        }
