CREATE TABLE car_park.parking_lot AS
SELECT
    주차장관리번호,
    주차장명,
    주차장구분,
    주차장유형,
    소재지도로명주소,
    소재지지번주소,
    주차구획수,
    운영요일,
    평일운영시작시각,
    평일운영종료시각,
    토요일운영시작시각,
    토요일운영종료시각,
    공휴일운영시작시각,
    공휴일운영종료시각,
    요금정보,
    주차기본시간,
    주차기본요금,
    추가단위시간,
    추가단위요금,
    1일주차권요금적용시간,
    1일주차권요금,
    월정기권요금,
    결제방법,
    특기사항,
    위도,
    경도,
    장애인전용주차구역보유여부
FROM parking_db.national_parking;

SELECT DISTINCT 운영요일
FROM car_park.parking_lot;

-- 주차장관리번호 int로 변경
ALTER TABLE car_park.parking_lot
ADD COLUMN pl_id BIGINT UNSIGNED;
ALTER TABLE car_park.parking_lot
ADD COLUMN pl_id_str VARCHAR(20);

UPDATE car_park.parking_lot
SET pl_id_str = REPLACE(REPLACE(TRIM(주차장관리번호),'-',''),' ','');

UPDATE car_park.parking_lot
SET pl_id = CAST(pl_id_str AS UNSIGNED);

ALTER TABLE car_park.parking_lot
DROP COLUMN pl_id_str,
DROP COLUMN 주차장관리번호;

ALTER TABLE car_park.parking_lot
MODIFY COLUMN pl_id BIGINT UNSIGNED FIRST;


ALTER TABLE car_park.parking_lot
CHANGE COLUMN 주차장명 pl_name VARCHAR(200),
CHANGE COLUMN 주차장유형 pl_type ENUM('노상','노외','부설'),
CHANGE COLUMN 소재지도로명주소 road_address VARCHAR(255),
CHANGE COLUMN 소재지지번주소 lot_address VARCHAR(255),
CHANGE COLUMN 주차구획수 capacity INT,
CHANGE COLUMN 운영요일 op_days VARCHAR(50);

-- 중복 숫자때문에 primary key 안됨 일단 보류
ALTER TABLE car_park.parking_lot
ADD PRIMARY KEY(pl_id);

-- 공영이면 true 반환 
ALTER TABLE car_park.parking_lot
ADD COLUMN is_public BOOLEAN AFTER 주차장구분;

UPDATE car_park.parking_lot
SET is_public = CASE
    WHEN 주차장구분 = '공영' THEN TRUE
    ELSE FALSE
END;

ALTER TABLE car_park.parking_lot
DROP COLUMN 주차장구분;

-- 시간 일단은 그냥 문자열로
ALTER TABLE car_park.parking_lot
CHANGE COLUMN 평일운영시작시각 week_start VARCHAR(5),
CHANGE COLUMN 평일운영종료시각 week_end VARCHAR(5),
CHANGE COLUMN 토요일운영시작시각 sat_start VARCHAR(5),
CHANGE COLUMN 토요일운영종료시각 sat_end VARCHAR(5),
CHANGE COLUMN 공휴일운영시작시각 holiday_start VARCHAR(5),
CHANGE COLUMN 공휴일운영종료시각 holiday_end VARCHAR(5);

ALTER TABLE car_park.parking_lot
ADD COLUMN is_free BOOLEAN AFTER 요금정보;
UPDATE car_park.parking_lot
SET is_free = IF(요금정보 LIKE '%무료%', 1, 0);


