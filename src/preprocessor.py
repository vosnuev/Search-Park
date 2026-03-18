from process.address import importRawAddress
from process.parking_lot import load_parking_lot
from process.operation_time import run as op_run
from process.payment import run as pay_run
from process.address import mapping_parking_lot
from collect.naver_logic import run as collect_run
from db.db import init_review_table

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

# 네이버 댓글 관련 처리
init_review_table()
collect_run()

print("모든 전처리가 완료되었습니다!")

