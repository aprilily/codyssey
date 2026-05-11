"""
calculator.py - PyQt5 기반 계산기 애플리케이션

PEP 8 스타일 가이드 준수
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QGridLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor, QPalette


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
MAX_VALUE = 1e15          # 처리 가능한 최대 숫자
MIN_VALUE = -1e15         # 처리 가능한 최소 숫자
DECIMAL_PLACES = 6        # 소수점 반올림 자릿수


class Calculator:
    """사칙연산 및 부가 기능을 담당하는 계산기 클래스."""

    def __init__(self):
        self.reset()

    # ------------------------------------------------------------------
    # 초기화
    # ------------------------------------------------------------------
    def reset(self):
        """계산기 상태를 초기화한다."""
        self._current = '0'
        self._previous = None
        self._operator = None
        self._should_reset_display = False
        self._result_shown = False

    # ------------------------------------------------------------------
    # 숫자 / 소수점 입력
    # ------------------------------------------------------------------
    def input_digit(self, digit: str) -> str:
        """
        숫자 한 자리를 입력받아 현재 표시 값에 누적하고 반환한다.

        Args:
            digit: 입력된 숫자 문자 ('0'~'9')

        Returns:
            업데이트된 현재 표시 문자열
        """
        if self._should_reset_display or self._result_shown:
            self._current = digit
            self._should_reset_display = False
            self._result_shown = False
        else:
            if self._current == '0' and digit != '.':
                self._current = digit
            else:
                self._current += digit
        return self._current

    def input_decimal(self) -> str:
        """
        소수점을 입력한다. 이미 소수점이 있으면 무시한다.

        Returns:
            업데이트된 현재 표시 문자열
        """
        if self._should_reset_display or self._result_shown:
            self._current = '0.'
            self._should_reset_display = False
            self._result_shown = False
            return self._current

        if '.' not in self._current:
            self._current += '.'
        return self._current

    # ------------------------------------------------------------------
    # 사칙연산
    # ------------------------------------------------------------------
    def add(self, a: float, b: float) -> float:
        """덧셈을 수행한다."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """뺄셈을 수행한다."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """곱셈을 수행한다."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """
        나눗셈을 수행한다.

        Args:
            a: 피제수
            b: 제수

        Returns:
            나눗셈 결과

        Raises:
            ZeroDivisionError: b가 0일 때
        """
        if b == 0:
            raise ZeroDivisionError('0으로 나눌 수 없습니다.')
        return a / b

    # ------------------------------------------------------------------
    # 부가 기능
    # ------------------------------------------------------------------
    def negative_positive(self) -> str:
        """
        현재 값의 부호를 반전한다.

        Returns:
            부호가 반전된 현재 표시 문자열
        """
        value = float(self._current)
        value = -value
        self._current = self._format_value(value)
        return self._current

    def percent(self) -> str:
        """
        현재 값을 백분율(÷100)로 변환한다.

        Returns:
            변환된 현재 표시 문자열
        """
        value = float(self._current) / 100
        self._current = self._format_value(value)
        return self._current

    # ------------------------------------------------------------------
    # 연산자 선택 / 결과 출력
    # ------------------------------------------------------------------
    def set_operator(self, operator: str) -> str:
        """
        연산자를 설정하고 이전 연산이 있으면 중간 계산을 수행한다.

        Args:
            operator: '+', '-', '×', '÷' 중 하나

        Returns:
            현재 표시 문자열
        """
        current_value = float(self._current)

        if self._previous is not None and not self._should_reset_display:
            result = self._calculate(self._previous, current_value, self._operator)
            self._current = self._format_value(result)
            self._previous = result
        else:
            self._previous = current_value

        self._operator = operator
        self._should_reset_display = True
        self._result_shown = False
        return self._current

    def equal(self) -> str:
        """
        현재 연산을 수행하고 결과를 반환한다.

        Returns:
            계산 결과 문자열

        Raises:
            ZeroDivisionError: 0으로 나눌 때
            OverflowError: 결과가 처리 범위를 초과할 때
        """
        if self._operator is None or self._previous is None:
            return self._current

        current_value = float(self._current)
        result = self._calculate(self._previous, current_value, self._operator)
        self._current = self._format_value(result)
        self._previous = None
        self._operator = None
        self._result_shown = True
        return self._current

    # ------------------------------------------------------------------
    # 내부 유틸리티
    # ------------------------------------------------------------------
    def _calculate(self, a: float, b: float, operator: str) -> float:
        """
        두 피연산자와 연산자로 계산을 수행한다.

        Args:
            a: 첫 번째 피연산자
            b: 두 번째 피연산자
            operator: 연산자 문자열

        Returns:
            계산 결과

        Raises:
            ZeroDivisionError: 0으로 나누기 시도 시
            OverflowError: 결과가 처리 가능 범위를 벗어날 때
        """
        if operator == '+':
            result = self.add(a, b)
        elif operator == '-':
            result = self.subtract(a, b)
        elif operator == '×':
            result = self.multiply(a, b)
        elif operator == '÷':
            result = self.divide(a, b)
        else:
            result = b

        if result > MAX_VALUE or result < MIN_VALUE:
            raise OverflowError('처리할 수 있는 숫자 범위를 초과했습니다.')

        return result

    @staticmethod
    def _format_value(value: float) -> str:
        """
        float 값을 표시용 문자열로 변환한다.
        소수점 6자리 이하는 반올림해서 출력한다.

        Args:
            value: 변환할 숫자

        Returns:
            포맷된 문자열
        """
        if value == int(value) and '.' not in str(value):
            return str(int(value))

        # 소수 자리가 있는 경우 최대 6자리까지 반올림
        rounded = round(value, DECIMAL_PLACES)
        text = f'{rounded:.{DECIMAL_PLACES}f}'.rstrip('0').rstrip('.')
        return text

    @property
    def current(self) -> str:
        """현재 표시 값을 반환한다."""
        return self._current

    @property
    def operator(self):
        """현재 선택된 연산자를 반환한다."""
        return self._operator


# ---------------------------------------------------------------------------
# PyQt5 UI
# ---------------------------------------------------------------------------
STYLE_SHEET = """
QMainWindow, QWidget#centralWidget {
    background-color: #1a1a1a;
}

QLabel#display {
    background-color: #1a1a1a;
    color: #f5f5f5;
    padding: 8px 18px 4px 18px;
    qproperty-alignment: AlignRight | AlignBottom;
}

QLabel#expression {
    background-color: #1a1a1a;
    color: #888888;
    padding: 0px 18px;
    qproperty-alignment: AlignRight | AlignVCenter;
    font-size: 14px;
}

QPushButton {
    border: none;
    border-radius: 50px;
    font-size: 22px;
    font-weight: 500;
}

QPushButton:pressed {
    opacity: 0.7;
}

QPushButton.func {
    background-color: #333333;
    color: #f5f5f5;
}

QPushButton.func:pressed {
    background-color: #555555;
}

QPushButton.operator {
    background-color: #ff9500;
    color: #ffffff;
}

QPushButton.operator:pressed {
    background-color: #ffb04d;
}

QPushButton.operator_active {
    background-color: #ffffff;
    color: #ff9500;
}

QPushButton.num {
    background-color: #333333;
    color: #f5f5f5;
}

QPushButton.num:pressed {
    background-color: #505050;
}

QPushButton#btn_zero {
    border-radius: 36px;
    text-align: left;
    padding-left: 26px;
}

QPushButton#btn_equal {
    background-color: #ff9500;
    color: #ffffff;
}

QPushButton#btn_equal:pressed {
    background-color: #ffb04d;
}
"""


class CalculatorWindow(QMainWindow):
    """계산기 메인 윈도우."""

    BUTTON_SIZE = 72
    BUTTON_GAP = 12

    def __init__(self):
        super().__init__()
        self._calc = Calculator()
        self._active_operator_btn = None
        self._init_ui()

    # ------------------------------------------------------------------
    # UI 초기화
    # ------------------------------------------------------------------
    def _init_ui(self):
        self.setWindowTitle('Calculator')
        self.setFixedSize(340, 580)
        self.setStyleSheet(STYLE_SHEET)

        central = QWidget()
        central.setObjectName('centralWidget')
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 16)
        root_layout.setSpacing(0)

        # 수식 표시 레이블 (작은 글씨, 이전 연산 표시)
        self._expression_label = QLabel('')
        self._expression_label.setObjectName('expression')
        self._expression_label.setFixedHeight(28)
        root_layout.addWidget(self._expression_label)

        # 메인 숫자 표시 레이블
        self._display = QLabel('0')
        self._display.setObjectName('display')
        self._display.setMinimumHeight(100)
        self._display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._update_display_font('0')
        root_layout.addWidget(self._display)

        # 버튼 그리드
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(12, 12, 12, 0)
        grid.setSpacing(self.BUTTON_GAP)
        root_layout.addWidget(grid_widget)

        self._create_buttons(grid)

    def _create_buttons(self, grid: QGridLayout):
        """버튼을 생성하고 그리드에 배치한다."""
        bs = self.BUTTON_SIZE

        # (행, 열, colspan, 레이블, 클래스, 객체명)
        button_map = [
            # 행 0
            (0, 0, 1, 'AC',  'func',     'btn_ac'),
            (0, 1, 1, '+/-', 'func',     'btn_neg'),
            (0, 2, 1, '%',   'func',     'btn_pct'),
            (0, 3, 1, '÷',   'operator', 'btn_div'),
            # 행 1
            (1, 0, 1, '7',   'num',      ''),
            (1, 1, 1, '8',   'num',      ''),
            (1, 2, 1, '9',   'num',      ''),
            (1, 3, 1, '×',   'operator', 'btn_mul'),
            # 행 2
            (2, 0, 1, '4',   'num',      ''),
            (2, 1, 1, '5',   'num',      ''),
            (2, 2, 1, '6',   'num',      ''),
            (2, 3, 1, '-',   'operator', 'btn_sub'),
            # 행 3
            (3, 0, 1, '1',   'num',      ''),
            (3, 1, 1, '2',   'num',      ''),
            (3, 2, 1, '3',   'num',      ''),
            (3, 3, 1, '+',   'operator', 'btn_add'),
            # 행 4
            (4, 0, 2, '0',   'num',      'btn_zero'),
            (4, 2, 1, '.',   'num',      'btn_dot'),
            (4, 3, 1, '=',   'operator', 'btn_equal'),
        ]

        self._operator_buttons = {
            '÷': None, '×': None, '-': None, '+': None
        }

        for row, col, span, label, cls, obj_name in button_map:
            btn = QPushButton(label)
            btn.setProperty('class', cls)
            if obj_name:
                btn.setObjectName(obj_name)
            if span == 2:
                btn.setFixedSize(bs * 2 + self.BUTTON_GAP, bs)
            else:
                btn.setFixedSize(bs, bs)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, lbl=label: self._on_button_click(lbl))
            grid.addWidget(btn, row, col, 1, span)

            if label in self._operator_buttons:
                self._operator_buttons[label] = btn

    # ------------------------------------------------------------------
    # 버튼 클릭 핸들러
    # ------------------------------------------------------------------
    def _on_button_click(self, label: str):
        """버튼 레이블에 따라 적절한 Calculator 메서드를 호출한다."""
        try:
            if label == 'AC':
                self._calc.reset()
                self._set_display('0')
                self._expression_label.setText('')
                self._clear_operator_highlight()

            elif label == '+/-':
                result = self._calc.negative_positive()
                self._set_display(result)

            elif label == '%':
                result = self._calc.percent()
                self._set_display(result)

            elif label in ('+', '-', '×', '÷'):
                result = self._calc.set_operator(label)
                self._set_display(result)
                self._highlight_operator(label)

            elif label == '=':
                # 수식 레이블 업데이트용
                prev = self._calc._previous
                op = self._calc.operator
                cur = self._calc.current
                if prev is not None and op:
                    prev_str = self._calc._format_value(prev)
                    self._expression_label.setText(f'{prev_str} {op} {cur} =')
                result = self._calc.equal()
                self._set_display(result)
                self._clear_operator_highlight()

            elif label == '.':
                result = self._calc.input_decimal()
                self._set_display(result)

            else:
                # 숫자
                result = self._calc.input_digit(label)
                self._set_display(result)
                if self._calc.operator is None:
                    self._clear_operator_highlight()

        except ZeroDivisionError:
            self._set_display('0으로 나누기 불가')
            self._calc.reset()
        except OverflowError:
            self._set_display('범위 초과')
            self._calc.reset()

    # ------------------------------------------------------------------
    # 디스플레이 갱신
    # ------------------------------------------------------------------
    def _set_display(self, text: str):
        """디스플레이 레이블을 갱신하고 폰트 크기를 동적으로 조정한다."""
        self._display.setText(text)
        self._update_display_font(text)

    def _update_display_font(self, text: str):
        """
        출력 값의 길이에 따라 폰트 크기를 조정한다. (보너스 과제)

        Args:
            text: 화면에 표시할 문자열
        """
        length = len(text)
        if length <= 6:
            size = 64
        elif length <= 9:
            size = 52
        elif length <= 12:
            size = 40
        elif length <= 15:
            size = 30
        else:
            size = 22
        font = QFont('SF Pro Display', size, QFont.Light)
        self._display.setFont(font)

    # ------------------------------------------------------------------
    # 연산자 버튼 하이라이트
    # ------------------------------------------------------------------
    def _highlight_operator(self, operator: str):
        """선택된 연산자 버튼을 강조 표시한다."""
        self._clear_operator_highlight()
        btn = self._operator_buttons.get(operator)
        if btn:
            btn.setProperty('class', 'operator_active')
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self._active_operator_btn = btn

    def _clear_operator_highlight(self):
        """연산자 버튼 강조 표시를 해제한다."""
        if self._active_operator_btn:
            self._active_operator_btn.setProperty('class', 'operator')
            self._active_operator_btn.style().unpolish(self._active_operator_btn)
            self._active_operator_btn.style().polish(self._active_operator_btn)
            self._active_operator_btn = None


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()