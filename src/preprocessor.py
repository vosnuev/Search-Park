from process.address import importRawAddress
from process.parking_lot import load_parking_lot
from process.operation_time import run as op_run
from process.payment import run as pay_run

importRawAddress()
load_parking_lot()
op_run('./src/data/전국주차장정보표준데이터_1.csv')
pay_run('./src/data/전국주차장정보표준데이터_1.csv')
