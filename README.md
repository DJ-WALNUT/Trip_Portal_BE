## ✈️ 가톨릭대 4대 공과대학 학생회 [여정] 포털 (Backend)

가톨릭대학교 공과대학 학생회 **여정**의 홈페이지 및 물품 대여 웹 서비스 백엔드 API 레포지토리입니다.
별도의 복잡한 데이터베이스 구축 없이 **Excel(Pandas) 및 CSV 파일**을 DB로 활용하여 유지보수 편의성을 극대화하였으며, **React SPA(Single Page Application) 정적 파일을 통합 서빙**할 수 있도록 설계되었습니다.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)</br>
[![Synology](https://img.shields.io/badge/Synology_NAS-Deployment-B0B3B8?style=flat-square&logo=synology&logoColor=white)](https://www.synology.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

### ✨ 주요 기능

#### 🌐 서버 및 공통 (Server & Common)
- **Excel & CSV Database**: `pandas`와 `csv` 모듈을 활용하여 파일을 직접 읽고 쓰는 방식으로 데이터 영속성 관리.
- **SPA 라우팅 지원**: React 빌드 결과물(`static`)을 Flask에서 직접 서빙하며, API가 아닌 모든 요청을 `index.html`로 리다이렉트하여 404 에러 방지.
- **타임존 처리 (KST)**: 서버/Docker 환경에 구애받지 않고 한국 시간(UTC+9) 기준으로 정확한 로그 타임스탬프 기록.

#### 👤 사용자 (User)
- **물품 대여 시스템**: 실시간 재고 확인 및 대여 신청 (이름, 학번, 학과, 연락처 기반).
- **티저 이벤트**: 축제/행사 기대평 작성 및 응모 기능 (CSV 기반 별도 격리 저장).
- **개인 조회**: 별도 회원가입 없이 본인의 대여 현황 및 반납 기한(D-Day) 조회.

#### ⚙️ 관리자 (Admin)
- **대시보드**: 금일 대여 건수 요약 및 최근 로그(5건) 프리뷰 제공.
- **스마트 반납 로직**:
  - **일회용품 자동 처리**: 승인 시 재고 차감 없이 상태만 변경.
  - **비품 재고 관리**: 반납 처리 시에만 물리적 재고 수량(+1) 자동 복구.
- **로그 다운로드**: 전체 대여/반납 이력을 **현재 시각이 포함된 파일명**의 엑셀 파일로 다운로드.

### 🛠️ 기술 스택 (Tech Stack)
- **Language**: Python 3.9
- **Framework**: Flask
- **Data Handling**: Pandas, OpenPyXL, CSV
- **Deployment**: Docker, Docker Compose

### 🚀 설치 및 실행 (Installation)

#### 로컬 환경 (Local)
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
시놀로지 Container Manager 또는 일반 Docker 환경에서 배포합니다.
1. 이미지 빌드 및 실행
```bash
docker-compose up -d --build
```
2. 설정 확인 : `docker-compose.yml`에서 포트(기본 5050) 및 볼륨 마운트 설정을 확인하세요.

### 📂 데이터 관리 (Data Structure)

이 프로젝트는 `data/` 폴더 내의 엑셀 파일을 DB로 사용합니다.
서버 재시작 시 데이터 유실을 방지하기 위해 **Docker Volume** 설정이 필수적입니다.

|파일명|설명|
|:---|:---|
|`stuff_ongoing.xlsx`|현재 물품 재고 현황 및 카테고리(반납물품/일회용품) 정보|
|`borrow_log.xlsx`|대여 신청, 승인, 반납 등 모든 이력 로그|
|`major.xlsx`|학과 목록 데이터 (신청 페이지 드롭다운 연동)|

### 🔧 API 엔드포인트 요약
|구분|Method|Endpoint|비고|
|:---|:---|:---|:---|
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

Copyright © 2025 Catholic University of Korea,</br>
CUK Engineering Student 4th Council [Trip] (최원서).
