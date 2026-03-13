# 🅿️ ParkFinder — 주차장 빈자리 탐색 앱

> Python · Streamlit · BeautifulSoup4 · MySQL · Folium  기반 주차장 빈자리 실시간 조회 웹 애플리케이션

---

## 📌 프로젝트 개요

모두의 주차장 웹페이지를 통해 주차장 정보를 수집하고, MySQL에 저장·관리한 뒤 Streamlit과 Folium 지도를 통해 시각화하는 웹 앱입니다.

사용자는 지역 또는 주차장 이름으로 검색하여 현재 빈자리 수, 요금 정보, 위치를 한눈에 확인할 수 있습니다.

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.12 |
| 웹 UI | Streamlit |
| 크롤링 | BeautifulSoup4 · requests |
| 데이터베이스 | MySQL 8.0 |
| ORM / DB 연결 | mysql-connector-python |
| 지도 시각화 | Folium · streamlit-folium |

---

## ✨ 주요 기능

- **주차장 정보 수집** — 모두의 주차장 웹페이지를 통해 주차장 정보 수집
- **주소 정보 수집** — 행정표준코드관리시스템을 통해 법정동 코드별 주소 정보 수집
- **키워드 검색** — 지역명 또는 주차장명으로 빠른 검색
- **지도 시각화** — Folium 기반 인터랙티브 지도에 주차장 위치 및 잔여 현황 표시
- **혼잡도 표시** — 빈자리 비율에 따라 여유 / 보통 / 혼잡 상태 색상 구분
- **이력 관리** — 시간대별 빈자리 추이를 DB에 저장하여 통계 조회 가능

---

## 📁 프로젝트 구조

```

```

---

## 🗄️ 데이터베이스 스키마

```sql
-- 주차장 기본 정보

```

---

## ⚙️ 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN28-1st-2team.git
```

### 2. 가상환경 생성 및 패키지 설치

```bash
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 DB 접속 정보를 입력합니다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=parkfinder
DB_USER=root
DB_PASSWORD=your_password

```

### 4. DB 초기화

```bash
mysql -u root -p < db/init_db.sql
```

### 5. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 🔧 requirements.txt

```
streamlit>=1.35.0
requests>=2.31.0
beautifulsoup4>=4.12.0
mysql-connector-python>=8.3.0
python-dotenv>=1.0.0
apscheduler>=3.10.0
folium>=0.16.0
streamlit-folium>=0.20.0
pandas>=2.2.0
```

---

## 📸 화면 구성

| 화면 | 설명 |
|------|------|
| 메인 대시보드 | 지도 위에 주차장 마커 표시, 클릭 시 상세 정보 팝업 |
| 목록 뷰 | 검색·필터 기능이 있는 테이블 형태 리스트 |
| 통계 페이지 | 시간대별 빈자리 추이 라인 차트 |


## 👤 개발자

| 항목 | 내용 |
|------|------|
| 이름 | 박건우 |
| 이메일 | shepherdpkw@gmail.com |
| GitHub | https://github.com/92shepherd |

---

## 📄 라이선스
