"""
caesar_cipher.py

Reads the encoded text from password.txt, then attempts to decode it using
every possible Caesar cipher shift (1-26). Each result is printed so the
user can visually identify the correct shift. Once the user enters the
correct shift number, the decoded result is saved to result.txt.

Bonus: an English word dictionary is used to automatically detect the
correct shift when a known word appears in the decoded text.
"""

import sys


# ---------------------------------------------------------------------------
# 보너스: 영어 단어 사전
# ---------------------------------------------------------------------------

ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
    'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
    'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
    'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
    'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could',
    'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come',
    'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how',
    'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
    'any', 'these', 'give', 'day', 'most', 'us', 'open', 'door', 'mars',
    'base', 'emergency', 'storage', 'mission', 'computer', 'password',
    'hello', 'world', 'access', 'granted', 'welcome', 'coffee', 'alive',
}


# ---------------------------------------------------------------------------
# 카이사르 암호 해독 함수
# ---------------------------------------------------------------------------

def caesar_cipher_decode(target_text):
    """
    Attempt to decode a Caesar-ciphered string using all 26 possible shifts.

    For each shift value (1 through 26) the function:
    1. Shifts every alphabetic character by that amount (wrapping A-Z / a-z).
    2. Leaves spaces and non-alphabetic characters unchanged.
    3. Prints the shift number and the decoded candidate so the user can
       visually identify the correct one.
    4. (Bonus) Checks whether any word in the decoded text matches the
       built-in English dictionary; if so, prints a detection notice and
       returns the shift and decoded text automatically.

    Args:
        target_text (str): The encrypted text to decode.

    Returns:
        tuple[int, str] | tuple[None, None]:
            (shift, decoded_text) if auto-detected via dictionary,
            (None, None) otherwise (user must choose manually).
    """
    print('=' * 60)
    print('  Caesar Cipher Decoder')
    print('=' * 60)
    print(f'  Encrypted : {target_text}')
    print('=' * 60)
    print(f'  {"Shift":<6}  Decoded text')
    print('-' * 60)

    for shift in range(1, 27):
        decoded_chars = []
        for ch in target_text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                decoded_chars.append(chr((ord(ch) - base - shift) % 26 + base))
            else:
                decoded_chars.append(ch)

        decoded = ''.join(decoded_chars)
        print(f'  [{shift:>2}]    {decoded}')

        # 보너스: 사전 단어 자동 감지
        words = decoded.lower().split()
        for word in words:
            clean = word.strip('.,!?;:\'"')
            if clean in ENGLISH_WORDS and len(clean) >= 3:
                print('-' * 60)
                print(f'  [AUTO] Dictionary word "{clean}" found at shift {shift}!')
                print(f'  [AUTO] Decoded text: {decoded}')
                print('=' * 60)
                return shift, decoded

    return None, None


# ---------------------------------------------------------------------------
# 파일 입출력
# ---------------------------------------------------------------------------

def read_password_file(file_path='password.txt'):
    """
    Read the encrypted text from a file.

    Args:
        file_path (str): Path to the password file.

    Returns:
        str | None: File contents stripped of leading/trailing whitespace,
                    or None if the file could not be read.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f'  [ERROR] File not found: {file_path}')
        return None
    except OSError as e:
        print(f'  [ERROR] Could not read file: {e}')
        return None


def save_result(decoded_text, shift, file_path='result.txt'):
    """
    Save the decoded result to a text file.

    Args:
        decoded_text (str): The successfully decoded plaintext.
        shift (int): The Caesar shift value that produced this result.
        file_path (str): Destination file path.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'Shift : {shift}\n')
            f.write(f'Result: {decoded_text}\n')
        print(f'  Saved to: {file_path}')
    except OSError as e:
        print(f'  [ERROR] Could not save result: {e}')


# ---------------------------------------------------------------------------
# 실행 진입점
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    encrypted = read_password_file('password.txt')
    if encrypted is None:
        sys.exit(1)

    auto_shift, auto_decoded = caesar_cipher_decode(encrypted)

    if auto_shift is not None:
        # 보너스: 자동 감지 성공
        save_result(auto_decoded, auto_shift)
        print(f'\n최종 결과 (shift={auto_shift}): {auto_decoded}')
    else:
        # 수동 선택
        print('\n눈으로 확인 후 올바른 shift 번호를 입력하세요 (1-26): ', end='')
        try:
            user_shift = int(input().strip())
            if not 1 <= user_shift <= 26:
                print('  [ERROR] 1에서 26 사이의 숫자를 입력하세요.')
                sys.exit(1)
        except ValueError:
            print('  [ERROR] 숫자를 입력하세요.')
            sys.exit(1)

        # 선택한 shift로 다시 디코딩
        result_chars = []
        for ch in encrypted:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result_chars.append(
                    chr((ord(ch) - base - user_shift) % 26 + base)
                )
            else:
                result_chars.append(ch)
        final_result = ''.join(result_chars)

        save_result(final_result, user_shift)
        print(f'\n최종 결과 (shift={user_shift}): {final_result}')
