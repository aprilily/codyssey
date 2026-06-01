"""
Javis - Voice Recording and STT System for Mars Mission Log

화성에 고립된 한송희 박사의 일일 기록을 위한 음성 녹음 및 텍스트 변환 시스템.
음성 파일을 STT로 변환하고 CSV 파일로 저장한다.
"""

import os
import csv
import datetime
import wave
import threading

import pyaudio
import whisper


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORDS_DIR = 'records'
STT_MODEL = 'base'


class VoiceRecorder:
    """시스템 마이크를 이용해 음성을 녹음하는 클래스."""

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self._stop_flag = False

    def list_microphones(self):
        """사용 가능한 마이크 장치 목록을 출력하고 반환한다.

        Returns:
            사용 가능한 마이크 장치 인덱스 목록.
        """
        print('사용 가능한 마이크 목록:')
        mic_list = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"  [{i}] {device_info['name']}")
                mic_list.append(i)
        return mic_list

    def _record_thread(self):
        """오디오 데이터를 지속적으로 읽어 frames에 저장하는 스레드 함수."""
        while not self._stop_flag:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception:
                break

    def record_audio(self, device_index=None):
        """Enter 키를 누를 때까지 마이크로 음성을 녹음한다.

        Args:
            device_index: 사용할 마이크 장치 인덱스. None이면 기본 장치 사용.

        Returns:
            녹음된 오디오 프레임 목록.
        """
        self.frames = []
        self._stop_flag = False

        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )

        print('녹음을 시작합니다. Enter 키를 누르면 녹음이 종료됩니다...')

        record_thread = threading.Thread(target=self._record_thread)
        record_thread.start()

        input()

        self._stop_flag = True
        record_thread.join()

        self.stream.stop_stream()
        self.stream.close()
        self.stream = None

        print('녹음이 종료되었습니다.')
        return self.frames

    def save_recording(self, frames):
        """녹음된 프레임을 날짜/시간 기반 파일명으로 WAV 파일에 저장한다.

        파일은 records 폴더 하위에 '년월일-시간분초.wav' 형태로 저장된다.

        Args:
            frames: 저장할 오디오 프레임 목록.

        Returns:
            저장된 파일 경로.
        """
        ensure_records_dir()

        now = datetime.datetime.now()
        filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
        filepath = os.path.join(RECORDS_DIR, filename)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        print(f'녹음 파일이 저장되었습니다: {filepath}')
        return filepath

    def close(self):
        """오디오 리소스를 해제한다."""
        self.audio.terminate()


class SpeechToText:
    """음성 파일에서 텍스트를 추출하는 STT 클래스."""

    def __init__(self, model_name=STT_MODEL):
        print(f'STT 모델({model_name})을 로딩 중입니다...')
        self.model = whisper.load_model(model_name)
        print('STT 모델 로딩 완료.')

    def transcribe_file(self, audio_path):
        """음성 파일을 텍스트 세그먼트 목록으로 변환한다.

        Args:
            audio_path: 변환할 WAV 파일 경로.

        Returns:
            (시작 시간, 인식된 텍스트) 튜플 목록.
        """
        print(f'변환 중: {os.path.basename(audio_path)}')
        result = self.model.transcribe(audio_path, language='ko')
        segments = []
        for segment in result['segments']:
            start_time = round(segment['start'], 2)
            text = segment['text'].strip()
            if text:
                segments.append((start_time, text))
        return segments

    def save_as_csv(self, segments, audio_path):
        """변환된 텍스트 세그먼트를 CSV 파일로 저장한다.

        파일명은 음성 파일과 동일하고 확장자만 .csv로 변경된다.

        Args:
            segments: (시작 시간, 인식된 텍스트) 튜플 목록.
            audio_path: 원본 음성 파일 경로.

        Returns:
            저장된 CSV 파일 경로.
        """
        base_path = os.path.splitext(audio_path)[0]
        csv_path = base_path + '.csv'

        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['시간', '인식된 텍스트'])
            for start_time, text in segments:
                writer.writerow([start_time, text])

        print(f'CSV 파일이 저장되었습니다: {csv_path}')
        return csv_path


def ensure_records_dir():
    """records 디렉토리가 없으면 생성한다."""
    if not os.path.exists(RECORDS_DIR):
        os.makedirs(RECORDS_DIR)


def list_audio_files():
    """records 폴더의 WAV 파일 목록을 출력하고 반환한다.

    Returns:
        WAV 파일명 목록.
    """
    if not os.path.exists(RECORDS_DIR):
        print('녹음 파일이 없습니다.')
        return []

    files = [
        f for f in sorted(os.listdir(RECORDS_DIR))
        if f.endswith('.wav')
    ]

    if files:
        print(f'녹음 파일 목록 ({len(files)}개):')
        for i, filename in enumerate(files):
            csv_name = os.path.splitext(filename)[0] + '.csv'
            csv_exists = os.path.exists(os.path.join(RECORDS_DIR, csv_name))
            status = '[변환됨]' if csv_exists else '[미변환]'
            print(f'  [{i}] {status} {filename}')
    else:
        print('녹음 파일이 없습니다.')

    return files


def list_recordings_by_date_range(start_date, end_date):
    """특정 날짜 범위의 녹음 파일 목록을 출력하고 반환한다.

    Args:
        start_date: 시작 날짜 문자열 (YYYYMMDD 형식).
        end_date: 종료 날짜 문자열 (YYYYMMDD 형식).

    Returns:
        해당 날짜 범위의 녹음 파일명 목록.
    """
    if not os.path.exists(RECORDS_DIR):
        print('녹음 파일이 없습니다.')
        return []

    try:
        start = datetime.datetime.strptime(start_date, '%Y%m%d')
        end = datetime.datetime.strptime(end_date, '%Y%m%d')
        end = end.replace(hour=23, minute=59, second=59)
    except ValueError:
        print('날짜 형식이 올바르지 않습니다. YYYYMMDD 형식으로 입력하세요.')
        return []

    files = []
    for filename in sorted(os.listdir(RECORDS_DIR)):
        if not filename.endswith('.wav'):
            continue
        try:
            date_str = filename[:8]
            file_date = datetime.datetime.strptime(date_str, '%Y%m%d')
            if start <= file_date <= end:
                files.append(filename)
        except (ValueError, IndexError):
            continue

    if files:
        print(f'{start_date} ~ {end_date} 기간의 녹음 파일:')
        for f in files:
            print(f'  {f}')
    else:
        print('해당 기간에 녹음된 파일이 없습니다.')

    return files


def search_keyword_in_csv(keyword):
    """저장된 CSV 파일에서 키워드를 검색하여 결과를 출력한다. (보너스 과제)

    Args:
        keyword: 검색할 키워드 문자열.

    Returns:
        (파일명, 시간, 텍스트) 튜플 목록.
    """
    if not os.path.exists(RECORDS_DIR):
        print('변환된 CSV 파일이 없습니다.')
        return []

    csv_files = [
        f for f in sorted(os.listdir(RECORDS_DIR))
        if f.endswith('.csv')
    ]

    if not csv_files:
        print('변환된 CSV 파일이 없습니다.')
        return []

    results = []
    for csv_file in csv_files:
        csv_path = os.path.join(RECORDS_DIR, csv_file)
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 2 and keyword in row[1]:
                    results.append((csv_file, row[0], row[1]))

    if results:
        print(f"'{keyword}' 검색 결과 ({len(results)}건):")
        for filename, time_val, text in results:
            print(f'  [{filename}] {time_val}초: {text}')
    else:
        print(f"'{keyword}'에 해당하는 결과가 없습니다.")

    return results


def run_stt(stt, files):
    """선택한 음성 파일에 STT를 실행하고 CSV로 저장한다.

    Args:
        stt: SpeechToText 인스턴스.
        files: 변환 대상 WAV 파일명 목록.
    """
    print('변환할 파일 번호를 입력하세요. (전체 변환: a, 취소: q)')
    choice = input('선택: ').strip().lower()

    if choice == 'q':
        return

    if choice == 'a':
        target_files = files
    else:
        try:
            idx = int(choice)
            if 0 <= idx < len(files):
                target_files = [files[idx]]
            else:
                print('올바른 번호를 입력하세요.')
                return
        except ValueError:
            print('올바른 입력이 아닙니다.')
            return

    for filename in target_files:
        audio_path = os.path.join(RECORDS_DIR, filename)
        segments = stt.transcribe_file(audio_path)
        if segments:
            stt.save_as_csv(segments, audio_path)
        else:
            print(f'{filename}: 인식된 텍스트가 없습니다.')


def show_menu():
    """메인 메뉴 옵션을 출력한다."""
    print('\n=== Javis 음성 녹음 및 STT 시스템 ===')
    print('1. 마이크 목록 확인')
    print('2. 음성 녹음')
    print('3. 녹음 파일 목록 (날짜 범위 검색)')
    print('4. 음성 파일 목록 불러오기')
    print('5. 음성 → 텍스트 변환 (STT)')
    print('6. 키워드 검색')
    print('7. 종료')


def main():
    """음성 녹음 및 STT 시스템의 메인 함수."""
    recorder = VoiceRecorder()
    stt = None

    try:
        while True:
            show_menu()
            choice = input('선택: ').strip()

            if choice == '1':
                recorder.list_microphones()

            elif choice == '2':
                mics = recorder.list_microphones()
                if not mics:
                    print('사용 가능한 마이크가 없습니다.')
                    continue

                mic_input = input(
                    '마이크 번호를 입력하세요 (기본값 사용: Enter): '
                ).strip()

                device_index = None
                if mic_input:
                    try:
                        device_index = int(mic_input)
                    except ValueError:
                        print('올바른 마이크 번호를 입력하세요.')
                        continue

                frames = recorder.record_audio(device_index)
                if frames:
                    recorder.save_recording(frames)
                else:
                    print('녹음된 내용이 없습니다.')

            elif choice == '3':
                start = input('시작 날짜를 입력하세요 (YYYYMMDD): ').strip()
                end = input('종료 날짜를 입력하세요 (YYYYMMDD): ').strip()
                list_recordings_by_date_range(start, end)

            elif choice == '4':
                list_audio_files()

            elif choice == '5':
                files = list_audio_files()
                if files:
                    if stt is None:
                        stt = SpeechToText()
                    run_stt(stt, files)

            elif choice == '6':
                keyword = input('검색할 키워드를 입력하세요: ').strip()
                if keyword:
                    search_keyword_in_csv(keyword)
                else:
                    print('키워드를 입력하세요.')

            elif choice == '7':
                print('프로그램을 종료합니다.')
                break

            else:
                print('올바른 메뉴를 선택하세요.')

    finally:
        recorder.close()


if __name__ == '__main__':
    main()
