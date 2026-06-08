"""
Mars Weather Summary - Mars Mission Weather Data Loader

화성 미션 컴퓨터에 백업된 날씨 데이터(csv)를 읽어
MySQL의 mars_weather 테이블에 입력하는 프로그램.
"""

import csv
import os

import mysql.connector


CSV_FILE_NAME = 'mars_weathers_data.csv'
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'mars_mission',
}


class MySQLHelper:
    """MySQL 연결과 쿼리 실행을 손쉽게 처리하기 위한 헬퍼 클래스. (보너스 과제)"""

    def __init__(self, config):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self):
        """설정값을 이용해 데이터베이스에 연결하고 커서를 생성한다."""
        self.connection = mysql.connector.connect(**self.config)
        self.cursor = self.connection.cursor()

    def execute(self, query, params=None):
        """단일 쿼리를 실행한다.

        Args:
            query: 실행할 SQL 쿼리 문자열.
            params: 쿼리에 바인딩할 매개변수 튜플.
        """
        self.cursor.execute(query, params)

    def commit(self):
        """현재까지의 변경 사항을 커밋한다."""
        self.connection.commit()

    def close(self):
        """커서와 연결을 안전하게 종료한다."""
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()


def read_weather_csv(file_path):
    """csv 파일을 읽어서 날씨 데이터 목록으로 반환한다.

    Args:
        file_path: 읽어들일 csv 파일 경로.

    Returns:
        (mars_date, temp, storm) 형태의 튜플 목록.
    """
    rows = []
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for row in reader:
            mars_date = row[1]
            temp = int(float(row[2]))
            storm = int(row[3])
            rows.append((mars_date, temp, storm))
    return rows


def print_weather_preview(rows, count=5):
    """읽어들인 데이터의 개수와 일부 내용을 출력해서 확인한다.

    Args:
        rows: 출력할 (mars_date, temp, storm) 튜플 목록.
        count: 미리 보여줄 행의 개수.
    """
    print(f'csv에서 읽은 날씨 데이터: 총 {len(rows)}건')
    for mars_date, temp, storm in rows[:count]:
        print(f'  날짜: {mars_date}, 온도: {temp}, 모래폭풍 지수: {storm}')


def insert_weather_rows(helper, rows):
    """날씨 데이터를 mars_weather 테이블에 INSERT 쿼리로 반복 입력한다.

    Args:
        helper: 연결된 MySQLHelper 인스턴스.
        rows: 입력할 (mars_date, temp, storm) 튜플 목록.
    """
    insert_query = (
        'INSERT INTO mars_weather (mars_date, temp, storm) '
        'VALUES (%s, %s, %s)'
    )
    for mars_date, temp, storm in rows:
        helper.execute(insert_query, (mars_date, temp, storm))
    helper.commit()
    print(f'mars_weather 테이블에 {len(rows)}건을 입력했습니다.')


def main():
    """csv를 읽고 mars_weather 테이블에 적재하는 전체 과정을 수행한다."""
    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILE_NAME)
    rows = read_weather_csv(csv_path)
    print_weather_preview(rows)

    helper = MySQLHelper(DB_CONFIG)
    try:
        helper.connect()
        insert_weather_rows(helper, rows)
    finally:
        helper.close()


if __name__ == '__main__':
    main()
