-- Active: 1773024375814@@127.0.0.1@3306@mysql
-- 자동차 등록 현황 정제 테이블 생성
create table if not exists car_park.car_registration (
    address_code varchar(10)  null    comment '법정동 코드',
    sd_name      varchar(100) not null comment '시/도 이름',
    ssg_name     varchar(100) not null comment '시/군/구 이름',
    gemd_name    varchar(100) not null comment '구/읍/면/동 이름',
    total_gov    int default 0 comment '관용 자동차수',
    total_prv    int default 0 comment '자가용 자동차수',
    total_com    int default 0 comment '영업용 자동차수',
    CONSTRAINT uq_car_registration UNIQUE KEY (sd_name, ssg_name, gemd_name),
    INDEX idx_address_code (address_code)
) ENGINE=INNODB COMMENT '자동차 등록 현황';


SELECT * FROM car_park.car_registration LIMIT 256;