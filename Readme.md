# 🅿️ Car Park Search Park — 주차장 찾기 + 주차장 통계 지표 대시보드

> Python · Streamlit · BeautifulSoup4 · MySQL 기반의 주차장 찾기 + 통계 대시보드

---

## 📌 프로젝트 개요

공공데이터포털 데이터를 기반으로 주차장 정보, 지역 정보를 저장
- 검색 조건에 맞는 주차장 정보를 찾는 검색창을 제공합니다.
- 지역별 주차장 정보 통계를 확인할 수 있는 대시보드를 제공합니다. 

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.12 |
| 웹 UI | Streamlit |
| 크롤링 | BeautifulSoup4 · selenium · requests |
| 데이터베이스 | MySQL 8.0 |

---

## ✨ 주요 기능

- **주차장 정보 수집** — 공공데이터를 통해 주차장 정보 수집
- **주소 정보 수집** — 행정표준코드관리시스템을 통해 주소 정보 수집
- **키워드 검색** — 지역명 또는 주차장명으로 검색 기능 제공
- **혼잡도 표시** — 지역별 주차장 포화상태 확인 통계 제공

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
#:Fixme
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



## 👤 개발자

| 항목 | 내용 |
|------|------|
| 이름 | 박건우 |
| 이메일 | shepherdpkw@gmail.com |
| GitHub | https://github.com/92shepherd |
TODO: 아래에 개별 정보 작성

---

## 📄 라이선스
