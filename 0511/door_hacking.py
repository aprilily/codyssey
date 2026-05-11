"""
door_hacking.py

Emergency Storage Key Unlocker
Brute-forces a 6-character password (lowercase letters + digits, no special chars)
for the encrypted zip file 'emergency_storage_key.zip'.

Bonus: multiprocessing-based parallel brute-force for faster cracking.
"""

import itertools
import multiprocessing
import os
import string
import time
import zipfile
import zlib


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

def _try_password(zf, target, candidate):
    """
    Try a single password against an open ZipFile.

    Python's zip encryption uses a single-byte header check (~1/256
    false-positive rate), so three distinct exceptions can occur:

    * RuntimeError   -- header byte mismatch  -> wrong password
    * zlib.error     -- false positive; decompression failed -> wrong password
    * zipfile.BadZipFile -- false positive; CRC mismatch   -> wrong password
    * No exception   -- password is correct

    Args:
        zf (zipfile.ZipFile): Already-opened zip archive.
        target (str): Name of the file inside the archive to test.
        candidate (str): Password string to attempt.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
    try:
        with zf.open(target, pwd=candidate.encode()) as f:
            f.read()      # full decompression required to confirm success
        return True
    except RuntimeError:
        return False      # wrong password (header check)
    except (zlib.error, zipfile.BadZipFile):
        return False      # false positive; decompression or CRC mismatch


def _save_password(password, output_file):
    """Save the cracked password to a text file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(password)
        print(f'  Saved to       : {output_file}')
    except OSError as e:
        print(f'  [ERROR] Could not save password file: {e}')


# ---------------------------------------------------------------------------
# 수행과제: 기본 브루트포스 (unlock_zip)
# ---------------------------------------------------------------------------

def unlock_zip(zip_path='emergency_storage_key.zip',
               password_length=6,
               output_file='password.txt'):
    """
    Brute-force the password of an encrypted zip file (single process).

    Iterates through every combination of lowercase letters and digits
    (a-z + 0-9) of the given length in lexicographic order.

    Progress is printed every 1,000,000 attempts showing elapsed time,
    attempt count, and current candidate.

    Args:
        zip_path (str): Path to the encrypted zip file.
        password_length (int): Exact length of the password to try.
        output_file (str): Path of the file to write the found password.

    Returns:
        str | None: The cracked password, or None if not found.
    """
    charset = string.ascii_lowercase + string.digits  # a-z0-9
    total = len(charset) ** password_length

    print('=' * 60)
    print('  Emergency Storage Key Unlocker')
    print('=' * 60)
    print(f'  Target : {zip_path}')
    print(f'  Length : {password_length} characters')
    print(f'  Charset: "{charset}"  ({len(charset)} symbols)')
    print(f'  Total  : {total:,} combinations')
    print('=' * 60)

    start_time = time.time()
    print(f'  Start  : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}')
    print('-' * 60)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            target = zf.namelist()[0]

            for attempt, combo in enumerate(
                    itertools.product(charset, repeat=password_length), start=1):

                candidate = ''.join(combo)

                if attempt % 1_000_000 == 0:
                    elapsed = time.time() - start_time
                    speed = attempt / elapsed
                    print(f'  [{attempt:>13,}] elapsed: {elapsed:7.1f}s'
                          f'  speed: {speed:,.0f}/s  trying: {candidate}')

                if _try_password(zf, target, candidate):
                    elapsed = time.time() - start_time
                    print('-' * 60)
                    print(f'  Password found : {candidate}')
                    print(f'  Attempts       : {attempt:,}')
                    print(f'  Elapsed time   : {elapsed:.2f} s')
                    print('=' * 60)
                    _save_password(candidate, output_file)
                    return candidate

    except FileNotFoundError:
        print(f'  [ERROR] File not found: {zip_path}')
        return None

    print('  [FAIL] Password not found in the search space.')
    return None


# ---------------------------------------------------------------------------
# 보너스 과제: 멀티프로세싱 병렬 브루트포스 (unlock_zip_fast)
# ---------------------------------------------------------------------------

def _worker(args):
    """
    Subprocess worker: searches a slice of the password space.

    The full search space is partitioned by the first character of the
    password, so this worker only iterates combinations that start with
    ``prefix``.  No inter-process communication occurs inside the loop.

    Args:
        args (tuple): (zip_path, charset, password_length, prefix)
            zip_path (str): Path to the encrypted zip file.
            charset (str): Characters used in the password.
            password_length (int): Total length of the password.
            prefix (str): Fixed leading character(s) for this partition.

    Returns:
        str | None: The found password, or None if not in this partition.
    """
    zip_path, charset, password_length, prefix = args
    remaining = password_length - len(prefix)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            target = zf.namelist()[0]
            for combo in itertools.product(charset, repeat=remaining):
                candidate = prefix + ''.join(combo)
                if _try_password(zf, target, candidate):
                    return candidate
    except FileNotFoundError:
        pass

    return None


def unlock_zip_fast(zip_path='emergency_storage_key.zip',
                    password_length=6,
                    output_file='password.txt'):
    """
    Parallel brute-force using multiprocessing (bonus algorithm).

    Algorithm
    ---------
    The search space (36^6 ≈ 2.2 billion combinations) is divided into
    36 partitions, one per possible first character.  Each partition is
    dispatched to a worker process via ``multiprocessing.Pool``.

    ``pool.imap_unordered`` yields worker results as they complete.  The
    moment one worker returns the correct password the pool is terminated,
    stopping all remaining workers immediately.  On average, only half the
    full search space needs to be explored.

    Speed advantage over single-process brute-force
    ------------------------------------------------
    * Linear scaling: N physical cores -> ~N× faster.
    * Early termination: password found after ~50 % of combinations on
      average, giving an additional ~2× speedup.
    * No shared memory or locks inside the hot loop -> minimal overhead.

    Args:
        zip_path (str): Path to the encrypted zip file.
        password_length (int): Exact length of the password.
        output_file (str): Path of the file to write the found password.

    Returns:
        str | None: The cracked password, or None if not found.
    """
    charset = string.ascii_lowercase + string.digits
    cpu_count = multiprocessing.cpu_count()
    tasks = [(zip_path, charset, password_length, ch) for ch in charset]
    total = len(charset) ** password_length

    print('=' * 60)
    print('  Emergency Storage Key Unlocker  [PARALLEL MODE]')
    print('=' * 60)
    print(f'  Target    : {zip_path}')
    print(f'  Length    : {password_length} characters')
    print(f'  Charset   : "{charset}"  ({len(charset)} symbols)')
    print(f'  Total     : {total:,} combinations')
    print(f'  Workers   : {cpu_count} CPU cores')
    print(f'  Partitions: {len(tasks)} (split by 1st character)')
    print('=' * 60)

    start_time = time.time()
    print(f'  Start     : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}')
    print('-' * 60)

    found_password = None

    try:
        with multiprocessing.Pool(processes=cpu_count) as pool:
            for result in pool.imap_unordered(_worker, tasks):
                if result is not None:
                    pool.terminate()
                    found_password = result
                    break
    except Exception as e:
        print(f'  [ERROR] Multiprocessing error: {e}')
        return None

    elapsed = time.time() - start_time

    if found_password:
        print(f'  Password found : {found_password}')
        print(f'  Elapsed time   : {elapsed:.2f} s')
        print('=' * 60)
        _save_password(found_password, output_file)
    else:
        print('  [FAIL] Password not found.')

    return found_password


# ---------------------------------------------------------------------------
# 실행 진입점
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    ZIP_PATH = 'emergency_storage_key.zip'
    PASSWORD_LENGTH = 6
    OUTPUT_FILE = 'password.txt'

    cpu_count = os.cpu_count() or 1
    use_parallel = cpu_count > 1

    if use_parallel:
        print(f'\n[보너스] 멀티프로세싱 병렬 모드로 실행합니다. (CPU: {cpu_count}코어)\n')
        result = unlock_zip_fast(ZIP_PATH, PASSWORD_LENGTH, OUTPUT_FILE)
    else:
        print('\n[기본] 단일 프로세스 모드로 실행합니다.\n')
        result = unlock_zip(ZIP_PATH, PASSWORD_LENGTH, OUTPUT_FILE)

    if result:
        print(f'\n최종 결과: 비밀번호 = "{result}"')
    else:
        print('\n비밀번호를 찾지 못했습니다.')
