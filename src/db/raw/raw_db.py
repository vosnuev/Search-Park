import mysql.connector

Conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='gwpark',
    password='p@ssw0rd',
    database='car_park_raw'
)