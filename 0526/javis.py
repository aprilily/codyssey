"""
Javis - Voice Recording System for Mars Mission Log

화성에 고립된 한송희 박사의 일일 기록을 위한 음성 녹음 시스템.
마이크를 인식하고 음성을 녹음하여 날짜/시간 기반 파일명으로 저장한다.
"""

import os
import datetime
import wave
import threading

import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORDS_DIR = 'records'


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


def ensure_records_dir():
    """records 디렉토리가 없으면 생성한다."""
    if not os.path.exists(RECORDS_DIR):
        os.makedirs(RECORDS_DIR)


def list_recordings_by_date_range(start_date, end_date):
    """특정 날짜 범위의 녹음 파일 목록을 출력하고 반환한다. (보너스 과제)

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


def show_menu():
    """메인 메뉴 옵션을 출력한다."""
    print('\n=== Javis 음성 녹음 시스템 ===')
    print('1. 마이크 목록 확인')
    print('2. 음성 녹음')
    print('3. 녹음 파일 목록 (날짜 범위 검색)')
    print('4. 종료')


def main():
    """음성 녹음 시스템의 메인 함수."""
    recorder = VoiceRecorder()

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
                print('프로그램을 종료합니다.')
                break

            else:
                print('올바른 메뉴를 선택하세요.')

    finally:
        recorder.close()


if __name__ == '__main__':
    main()
