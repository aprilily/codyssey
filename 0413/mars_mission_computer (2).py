import time
import json
import threading
import datetime
import random
import platform
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

SETTINGS_FILE = 'setting.txt'

DEFAULT_INFO_FIELDS = ['os', 'os_version', 'cpu_type', 'cpu_cores', 'memory_size']
DEFAULT_LOAD_FIELDS = ['cpu_usage', 'memory_usage']


def load_settings():
    """setting.txt 파일에서 출력 항목 설정을 불러온다."""
    settings = {
        'info_fields': DEFAULT_INFO_FIELDS[:],
        'load_fields': DEFAULT_LOAD_FIELDS[:],
    }

    if not os.path.exists(SETTINGS_FILE):
        return settings

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        current_section = None
        info_fields = []
        load_fields = []

        for line in lines:
            if line == '[info_fields]':
                current_section = 'info'
            elif line == '[load_fields]':
                current_section = 'load'
            elif current_section == 'info':
                info_fields.append(line)
            elif current_section == 'load':
                load_fields.append(line)

        if info_fields:
            settings['info_fields'] = info_fields
        if load_fields:
            settings['load_fields'] = load_fields

    except Exception as e:
        print(f'[설정 파일 오류] setting.txt 읽기 실패: {e}')
        print('기본 설정으로 실행합니다.')

    return settings


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
        self._stop = False
        self._history = {key: [] for key in self.env_values}
        self.settings = load_settings()

    def get_sensor_data(self):
        ds = DummySensor()

        def wait_for_stop():
            input()
            self._stop = True

        stop_thread = threading.Thread(target=wait_for_stop, daemon=True)
        stop_thread.start()

        print('센서 데이터 수집을 시작합니다. 멈추려면 Enter 키를 누르세요.\n')

        last_avg_time = time.time()
        avg_interval = 300

        while not self._stop:
            ds.set_env()
            sensor_data = ds.get_env()

            for key in self.env_values:
                self.env_values[key] = sensor_data[key]

            for key in self.env_values:
                self._history[key].append(self.env_values[key])

            print(json.dumps(self.env_values, indent=4))

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
                self._history = {key: [] for key in self.env_values}
                last_avg_time = now

            for _ in range(50):
                if self._stop:
                    break
                time.sleep(0.1)

        print('System stopped....')

    def get_mission_computer_info(self):
        """
        미션 컴퓨터의 시스템 정보를 수집하여 JSON 형식으로 출력한다.

        수집 항목:
            os           : 운영체계
            os_version   : 운영체계 버전
            cpu_type     : CPU 타입
            cpu_cores    : CPU 물리 코어 수
            memory_size  : 전체 메모리 크기 (GB)
        """
        all_info = {}

        try:
            all_info['os'] = platform.system()
        except Exception as e:
            all_info['os'] = f'Unknown (오류: {e})'

        try:
            all_info['os_version'] = platform.version()
        except Exception as e:
            all_info['os_version'] = f'Unknown (오류: {e})'

        try:
            all_info['cpu_type'] = platform.processor() or platform.machine()
        except Exception as e:
            all_info['cpu_type'] = f'Unknown (오류: {e})'

        try:
            if PSUTIL_AVAILABLE:
                all_info['cpu_cores'] = psutil.cpu_count(logical=False)
            else:
                all_info['cpu_cores'] = os.cpu_count()
        except Exception as e:
            all_info['cpu_cores'] = f'Unknown (오류: {e})'

        try:
            if PSUTIL_AVAILABLE:
                total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
                all_info['memory_size'] = f'{total_gb} GB'
            else:
                all_info['memory_size'] = 'psutil 라이브러리 필요'
        except Exception as e:
            all_info['memory_size'] = f'Unknown (오류: {e})'

        filtered = {k: v for k, v in all_info.items() if k in self.settings['info_fields']}

        print(json.dumps(filtered, indent=4, ensure_ascii=False))
        return filtered

    def get_mission_computer_load(self):
        """
        미션 컴퓨터의 실시간 부하 정보를 수집하여 JSON 형식으로 출력한다.

        수집 항목:
            cpu_usage    : CPU 실시간 사용량 (%)
            memory_usage : 메모리 실시간 사용량 (%)
        """
        all_load = {}

        try:
            if PSUTIL_AVAILABLE:
                cpu_percent = psutil.cpu_percent(interval=1)
                all_load['cpu_usage'] = f'{cpu_percent} %'
            else:
                all_load['cpu_usage'] = 'psutil 라이브러리 필요'
        except Exception as e:
            all_load['cpu_usage'] = f'Unknown (오류: {e})'

        try:
            if PSUTIL_AVAILABLE:
                mem_percent = psutil.virtual_memory().percent
                all_load['memory_usage'] = f'{mem_percent} %'
            else:
                all_load['memory_usage'] = 'psutil 라이브러리 필요'
        except Exception as e:
            all_load['memory_usage'] = f'Unknown (오류: {e})'

        filtered = {k: v for k, v in all_load.items() if k in self.settings['load_fields']}

        print(json.dumps(filtered, indent=4, ensure_ascii=False))
        return filtered


runComputer = MissionComputer()

if __name__ == '__main__':
    print('=== 미션 컴퓨터 시스템 정보 ===')
    runComputer.get_mission_computer_info()

    print('\n=== 미션 컴퓨터 실시간 부하 ===')
    runComputer.get_mission_computer_load()
