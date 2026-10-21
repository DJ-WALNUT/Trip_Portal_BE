## ✈️ 가톨릭대 4대 공과대학 학생회 [여정] 포털 (Backend)

가톨릭대학교 공과대학 학생회 **여정**의 통합 포털 웹 서비스 백엔드 API 레포지토리입니다.
기존의 유연한 **Excel/CSV 데이터 처리** 장점을 유지하면서, **SQLite(SQLAlchemy)**를 도입하여 공지사항 및 게시판 데이터의 안정적인 트랜잭션 관리를 구현하였습니다.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)</br>
[![Synology](https://img.shields.io/badge/Synology_NAS-Deployment-B0B3B8?style=flat-square&logo=synology&logoColor=white)](https://www.synology.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

### ✨ 주요 기능

#### 🌐 서버 및 공통 (Server & Common)
- **Hybrid Database**: 
  - **SQLite**: 공지사항, 학사일정 등 구조화된 데이터 및 관계형 데이터 관리.
  - **Excel/CSV**: 물품 재고, 대여 로그 등 레거시 데이터 및 엑셀 다운로드 기능 지원.
- **Modular Architecture**: `Blueprint`를 활용하여 기능별(공지사항, 인스타, 대여 등)로 라우트 및 로직 분리.
- **Rate Limiting**: `Flask-Limiter`를 적용하여 매크로 및 무분별한 API 호출 방지.
- **Security**: `.env`를 통한 환경변수 관리 및 관리자 세션 기반 인증.

#### 📢 게시판 및 정보 (Board & Info)
- **공지사항 관리 (CMS)**: 
  - 서식 있는 텍스트 및 **다중 파일 업로드** 지원 (폴더 기반 격리 저장).
  - **공개/비공개(임시저장)** 설정 및 상단 고정(Pin) 기능.
  - 조회수 중복 방지 로직 적용.
- **인스타그램 연동**: Instagram Graph API를 활용하여 최신 게시물 피드 자동 동기화.
- **학사일정 (D-Day)**: 주요 학사 일정을 DB화하여 메인 페이지 D-Day 자동 계산 제공.

#### 👤 사용자 (User) - 물품 대여
- **물품 대여 시스템**: 실시간 재고 확인 및 대여 신청.
- **티저 이벤트**: 축제/행사 기대평 작성 및 응모 (CSV 격리 저장).
- **개인 조회**: 본인의 대여 현황 및 반납 기한 조회.

#### ⚙️ 관리자 (Admin)
- **통합 대시보드**: 대여 현황 요약 및 최근 로그 프리뷰.
- **게시물 관리**: 공지사항 작성, 수정, 삭제 및 첨부파일 관리.
- **스마트 반납 로직**: 일회용품 자동 처리 및 비품 재고 자동 복구.
- **로그 다운로드**: 대여/반납 이력을 타임스탬프가 포함된 엑셀 파일로 추출.

---

### 🛠️ 기술 스택 (Tech Stack)
- **Language**: Python 3.9+
- **Framework**: Flask, Flask-SQLAlchemy
- **Data Handling**: Pandas, OpenPyXL, CSV
- **Security**: Flask-Limiter, Dotenv
- **Deployment**: Docker, Docker Compose

---

### 📂 프로젝트 구조 (Directory Structure)

```text
backend/
├── data/                  # 엑셀/CSV 데이터 (재고, 로그, 학과정보)
├── uploads/               # 공지사항 첨부파일 (업로드 시 ID별 폴더 생성)
├── routes/                # API 라우트 (Blueprint)
│   ├── notice_routes.py   # 공지사항 API
│   ├── instagram_routes.py# 인스타그램 API
│   └── ...
├── models.py              # DB 모델 정의 (SQLAlchemy)
├── extensions.py          # 공용 모듈 (Limiter, Login Decorator)
├── app.py                 # 앱 엔트리 포인트 & 설정
├── requirements.txt       # 의존성 패키지 목록
└── database.db            # SQLite 데이터베이스 파일 (자동 생성)
```

### 🚀 설치 및 실행 (Installation)

#### 1. 환경 변수 설정 (.env)
프로젝트 루트에 `.env`파일을 생성하고 아래 내용을 입력해야 합니다.
```Ini, TOML
FLASK_SECRET_KEY=your_secret_key
ADMIN_PASSWORD=your_admin_password
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_USER_ID=your_user_id
```

#### 2. 로컬 실행 (Local)
```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 실행 (기본 포트: 5000)
python app.py
```

#### 도커 배포 (Docker Deployment)
데이터 영속성을 위해 `data/`, `uploads/`, `database.db`가 위치한 경로를 반드시 볼륨 마운트해야 합니다.
1. 이미지 빌드 및 실행
```bash
docker-compose up -d --build
```
2. 설정 확인 : `docker-compose.yml`에서 포트(기본 5050) 및 볼륨 마운트 설정을 확인하세요.

### 🔧 API 엔드포인트
|구분|Method|Endpoint|비고|
|:---|:---|:---|:---|
|공지사항|`GET`|`/api/notices`|공지사항 목록 조회 (옵션: `include_private`)|
||`GET`|`/api/notices/<id>`|상세 조회 (옵션: `increment`)|
||`POST`|`/api/notices`|공지사항 등록 (Multipart/form-data)|
||`PUT`|`/api/notices/<id>`|공지사항 수정|
||`DELETE`|`/api/notices/<id>`|공지사항 삭제|
||`GET`|`/api/notices/download/...`|첨부파일 다운로드|
|SNS|`GET`|`/api/instagram/posts`|인스타그램 최신 피드 조회|
|일정|`GET`|`/api/schedule`|학사일정 데이터 조회|
|공통|`GET`|`/api/items`|전체 물품 및 재고 조회|
||`GET`|`/api/departments`|학과 목록 조회|
|사용자|`POST`|`/api/borrow`|물품 대여 신청|
||`POST`|`/api/check`|개인별 대여 현황 조회|
||`POST`|`/api/teaser/entry`|티저 이벤트 응모|
|관리자|`POST`|`/api/admin/login`|관리자 로그인|
||`GET`|`/api/admin/dashboard`|관리자 대시보드 데이터|
||`GET`|`/api/admin/ongoing`|미반납자 목록 조회 (연락처 포함)|
||`POST`|`/api/admin/approve`|대여 승인 (일회용품 자동 처리 포함)|
||`POST`|`/api/admin/return`|반납 처리 (관리자)|
||`GET`|`/api/admin/download_log`|전체 로그 엑셀 다운로드 (Timestamp 적용)|

### ⚙️ 사이트 정보 관리 API
|구분|Method|Endpoint|비고|
|:---|:---|:---|:---|
|설정|`GET`|`/api/site-info`|공개. 연락처·SNS·링크·문구·대여 설정 전체 조회|
||`PUT`|`/api/admin/site-info`|마스터 전용. 일부 키만 전송 가능, 오류가 있으면 저장 없이 `400 {status:'fail', errors}`|
|학사일정|`GET`|`/api/schedule`|항목마다 `id` 포함|
||`POST`|`/api/admin/schedule`|마스터 전용. `{name, start, end}` → `201`|
||`PUT`|`/api/admin/schedule/<id>`|마스터 전용. `200` / `400` / `404`|
||`DELETE`|`/api/admin/schedule/<id>`|마스터 전용. `200` / `404`|

`rental.enabled`가 꺼져 있으면 `POST /api/borrow`는 `403`을 반환합니다. 테스트는 `pip install -r requirements-dev.txt` 후 `python -m pytest -q`로 실행합니다.

#### 배포 시 유의사항
- 백엔드를 먼저 배포합니다. (새 API가 없어도 프론트는 기본값으로 동작)
- 배포 전(선택): 기존 컨테이너의 눈송이 설정 파일을 꺼내 둡니다. `docker cp trip-backend:/app/settings.json ./settings.json`
- 배포: `docker-compose up -d --build` 로 컨테이너를 다시 만듭니다. 볼륨 설정이 바뀌며 `uploads/`는 볼륨으로 보존됩니다.
- `settings.json`은 컨테이너 내부 파일이라 재생성 시 사라질 수 있어 눈송이 값이 자동 이전되지 않을 수 있습니다. 배포 후 관리자 대시보드의 눈송이 토글을 확인하고 필요하면 다시 설정하세요.

Copyright © 2025 Catholic University of Korea,</br>
CUK Engineering Student 4th Council [Trip] (최원서).
