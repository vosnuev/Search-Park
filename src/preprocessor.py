from process.address import importRawAddress
from process.parking_lot import load_parking_lot
from process.operation_time import run as op_run
from process.payment import run as pay_run
from process.address import mapping_parking_lot
from collect.naver_logic import run as collect_run
from db.db import initNaverTable

# 만약 파일명이 forth.py이고 함수가 run_new라면:

from pages.forth import run_new

print("데이터 전처리를 시작합니다...")

importRawAddress()
load_parking_lot()

# 주차장 기본 정보 처리
op_run('./src/data/전국주차장정보표준데이터_1.csv')
pay_run('./src/data/전국주차장정보표준데이터_1.csv')

# 주소 매핑 처리
mapping_parking_lot()
<<<<<<< HEAD

# 2. 질문자님이 만든 기능을 여기서 실행합니다.
# 보통 모든 기본 데이터 세팅이 끝난 마지막에 넣는 것이 안전합니다.
print("새로운 메뉴 기능을 실행합니다...")
run_new() 

print("모든 전처리가 완료되었습니다!")
=======
initNaverTable()
collect_run()
>>>>>>> 9672e29ace8feabc80e2ea633b2d699f6b75483e
