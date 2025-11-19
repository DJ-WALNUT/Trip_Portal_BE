## ✈️ 가톨릭대 4대 공과대학 학생회 [여정] 포털 (Backend)

가톨릭대학교 공과대학 학생회 **여정**의 홈페이지 및 물품 대여 웹 서비스 백엔드 API 레포지토리입니다.
별도의 데이터베이스 구축 없이 **Excel 파일(Pandas)을 DB로 활용**하여 유지보수 편의성을 극대화하였으며, Docker를 통해 시놀로지 NAS 등 어떤 환경에서도 쉽게 배포 가능합니다.
### ✨ 주요 기능

#### 👤 사용자 (User)
- Excel Database: pandas를 활용하여 엑셀 파일(xlsx)을 직접 읽고 쓰는 방식으로 데이터 영속성 관리.
- RESTful API: 프론트엔드(React)와 JSON 형식으로 통신.
- 스마트 반납 로직:
  - 일회용품 자동 처리: 대여 승인 시 '일회용품' 카테고리는 즉시 '반납완료'로 처리되며 재고가 복구되지 않습니다.
  - 비품 재고 관리: 일반 비품은 반납 확인 시에만 재고가 +1 복구됩니다.
- 관리자 인증: 세션 기반의 관리자 로그인 및 권한 체크.
- 타임존 처리: Docker 환경에서도 한국 시간(KST) 기준으로 정확한 로그 기록.

#### 🛠️ 기술 스택 (Tech Stack)
- Language: Python 3.9
- Framework: Flask
- Data Handling: Pandas, OpenPyXL
- Deployment: Docker, Docker Compose

#### 🚀 설치 및 실행 (Installation)
**로컬 환경 (Local)**
```
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 실행 (기본 포트: 5000)
python app.py
```

**도커 배포 (Docker Deployment)**

시놀로지 Container Manager 또는 일반 Docker 환경에서 배포합니다.

1. 이미지 빌드 및 실행
```
docker-compose up -d --build
```
2. 포트 설정 `docker-compose.yml` 파일에서 외부 포트를 설정합니다 (기본: 5050).

#### 📂 데이터 관리 (Data Structure)

이 프로젝트는 `data/` 폴더 내의 엑셀 파일을 DB로 사용합니다.
서버 재시작 시 데이터 유실을 방지하기 위해 **Docker Volume** 설정이 필수적입니다.

|파일명|설명|
|:---|:---|
|`stuff_ongoing.xlsx`|현재 물품 재고 현황 및 카테고리(반납물품/일회용품) 정보|
|`borrow_log.xlsx`|대여 신청, 승인, 반납 등 모든 이력 로그|
|`major.xlsx`|학과 목록 데이터 (신청 페이지 드롭다운 연동)|

#### 🔧 API 엔드포인트 예시
|Method|Endpoint|Description|
|:---|:---|:---|
|`GET`|`/api/items`|전체 물품 및 재고 조회|
|`GET`|`/api/departments`|학과 목록 조회|
|`POST`|`/api/borrow`|물품 대여 신청|
|`POST`|`/api/check`|개인별 대여 현황 조회|
|`POST`|`/api/admin/approve`|대여 승인 (일회용품 자동 처리 포함)|
|`POST`|`/api/admin/return`|반납 처리 (관리자)|

Copyright © 2025 Catholic University of Korea, CUK Engineering Student 4th Council [Trip] (최원서).
