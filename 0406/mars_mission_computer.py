import time
import json
import threading
import datetime
import random


class DummySensor:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0,
        }

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = (
            f"{timestamp}, "
            f"{self.env_values['mars_base_internal_temperature']}, "
            f"{self.env_values['mars_base_external_temperature']}, "
            f"{self.env_values['mars_base_internal_humidity']}, "
            f"{self.env_values['mars_base_external_illuminance']}, "
            f"{self.env_values['mars_base_internal_co2']}, "
            f"{self.env_values['mars_base_internal_oxygen']}"
        )
        with open('mars_base_log.csv', 'a', encoding='utf-8') as log_file:
            log_file.write(log_line + '\n')
        return self.env_values


class MissionComputer:
    def __init__(self):
        self.env_values = {
            'mars_base_internal_temperature': 0,
            'mars_base_external_temperature': 0,
            'mars_base_internal_humidity': 0,
            'mars_base_external_illuminance': 0,
            'mars_base_internal_co2': 0,
            'mars_base_internal_oxygen': 0,
        }
        # 보너스: 정지 플래그
        self._stop = False
        # 보너스: 5분 평균 계산용 누적 데이터
        self._history = {key: [] for key in self.env_values}

    def get_sensor_data(self):
        ds = DummySensor()

        # 보너스: 별도 스레드에서 키 입력 감지 (q 입력 시 정지)
        def wait_for_stop():
            input()  # 엔터 키 입력 대기
            self._stop = True

        stop_thread = threading.Thread(target=wait_for_stop, daemon=True)
        stop_thread.start()

        print('센서 데이터 수집을 시작합니다. 멈추려면 Enter 키를 누르세요.\n')

        # 보너스: 5분 평균 출력 주기 관리
        last_avg_time = time.time()
        avg_interval = 300  # 5분 = 300초

        while not self._stop:
            # 1. 센서 값 갱신 및 가져오기
            ds.set_env()
            sensor_data = ds.get_env()

            # 2. env_values에 저장
            for key in self.env_values:
                self.env_values[key] = sensor_data[key]

            # 보너스: 평균 계산용 히스토리에 누적
            for key in self.env_values:
                self._history[key].append(self.env_values[key])

            # 3. JSON 형태로 출력
            print(json.dumps(self.env_values, indent=4))

            # 보너스: 5분마다 평균값 출력
            now = time.time()
            if now - last_avg_time >= avg_interval:
                print('\n===== 최근 5분 평균값 =====')
                avg_values = {
                    key: round(sum(vals) / len(vals), 4)
                    for key, vals in self._history.items()
                    if vals
                }
                print(json.dumps(avg_values, indent=4))
                print('===========================\n')
                # 평균 출력 후 히스토리 및 타이머 초기화
                self._history = {key: [] for key in self.env_values}
                last_avg_time = now

            # 4. 5초 대기 (0.1초 간격으로 정지 신호 확인)
            for _ in range(50):
                if self._stop:
                    break
                time.sleep(0.1)

        print('System stopped....')


RunComputer = MissionComputer()
RunComputer.get_sensor_data()
