-- mars_weather 테이블 생성 스크립트 (MySQL Workbench에서 실행)
CREATE TABLE mars_weather (
    weather_id INT AUTO_INCREMENT PRIMARY KEY,
    mars_date DATETIME NOT NULL,
    temp INT,
    storm INT
);
