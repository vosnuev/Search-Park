-- Active: 1773024353491@@127.0.0.1@3306@car_park_raw
create table if not exists car_park_raw.address(
    address_code varchar(10),
    val varchar(256)
) ENGINE=INNODB COMMENT '주소 원본';