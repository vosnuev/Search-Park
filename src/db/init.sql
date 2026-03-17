-- 프로젝트 DB 초기 구성
create database if not exists car_park;

create table if not exists car_park.address(
    address_code varchar(10) not null comment '법정동 코드',
    sd_name varchar(100) not null comment '시/도 이름',
    ssg_name varchar(100) not null comment '시/군/구 이름',
    gemd_name varchar(100) not null comment '구/읍/면/동 이름',
    CONSTRAINT pk_address PRIMARY KEY (address_code),
    CONSTRAINT uk_address UNIQUE KEY (sd_name, ssg_name, gemd_name)
) ENGINE=INNODB COMMENT '주소';