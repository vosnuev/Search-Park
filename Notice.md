## 팀원들에게 공지하고 싶은 내용을 기록합니다.

이 공지를 최초로 확인했다면 아래의 과정을 따라주세요.
파워쉘 터미널에서 해당 프로젝트 루트로 이동 아래의 명령어를 실행해주세요.

### 전처리
* pip install -r requirements.txt
* python src\preprocessor.py
* (선택) 크롤링 데이터 적재 : src\collect\02.naver_map_db.sql 실행

### 프로그램 시작
streamlit run src\main.py