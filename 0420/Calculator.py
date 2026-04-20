"""
iPhone-style Calculator using PyQt5.

Implements the iOS calculator UI with full arithmetic operations (bonus task).
Follows PEP 8 coding style guide.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton,
    QVBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette


STYLE_SHEET = """
    QWidget#MainWindow {
        background-color: #000000;
    }

    QLabel#Display {
        color: #ffffff;
        background-color: #000000;
        padding: 0px 20px 10px 20px;
        qproperty-alignment: AlignRight;
    }

    QPushButton {
        border-radius: 40px;
        font-size: 28px;
        font-weight: 400;
        color: #ffffff;
        border: none;
    }

    QPushButton#btn_function {
        background-color: #a5a5a5;
        color: #000000;
    }

    QPushButton#btn_function:pressed {
        background-color: #d4d4d2;
    }

    QPushButton#btn_operator {
        background-color: #ff9f0a;
        color: #ffffff;
    }

    QPushButton#btn_operator:pressed {
        background-color: #ffcc80;
    }

    QPushButton#btn_operator_active {
        background-color: #ffffff;
        color: #ff9f0a;
    }

    QPushButton#btn_number {
        background-color: #333333;
        color: #ffffff;
    }

    QPushButton#btn_number:pressed {
        background-color: #737373;
    }

    QPushButton#btn_zero {
        background-color: #333333;
        color: #ffffff;
        border-radius: 40px;
        text-align: left;
        padding-left: 30px;
        font-size: 28px;
    }

    QPushButton#btn_zero:pressed {
        background-color: #737373;
    }
"""


class Calculator(QWidget):
    """Main calculator widget mimicking the iPhone calculator UI."""

    def __init__(self):
        super().__init__()
        self.current_input = '0'
        self.previous_input = ''
        self.operator = ''
        self.reset_next = False
        self.result_shown = False
        self._init_ui()

    def _init_ui(self):
        """Initialize the calculator UI layout and widgets."""
        self.setObjectName('MainWindow')
        self.setWindowTitle('Calculator')
        self.setFixedSize(380, 650)
        self.setStyleSheet(STYLE_SHEET)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(10, 40, 10, 10)

        # Display label
        self.display = QLabel('0')
        self.display.setObjectName('Display')
        self.display.setFont(QFont('Helvetica Neue', 72, QFont.Light))
        self.display.setMinimumHeight(120)
        self.display.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.display)

        # Button grid
        grid = QGridLayout()
        grid.setSpacing(10)

        # Button definitions: (label, row, col, colspan, object_name, action)
        buttons = [
            ('AC', 0, 0, 1, 'btn_function', self._press_ac),
            ('+/-', 0, 1, 1, 'btn_function', self._press_sign),
            ('%', 0, 2, 1, 'btn_function', self._press_percent),
            ('÷', 0, 3, 1, 'btn_operator', lambda: self._press_operator('/')),
            ('7', 1, 0, 1, 'btn_number', lambda: self._press_number('7')),
            ('8', 1, 1, 1, 'btn_number', lambda: self._press_number('8')),
            ('9', 1, 2, 1, 'btn_number', lambda: self._press_number('9')),
            ('×', 1, 3, 1, 'btn_operator', lambda: self._press_operator('*')),
            ('4', 2, 0, 1, 'btn_number', lambda: self._press_number('4')),
            ('5', 2, 1, 1, 'btn_number', lambda: self._press_number('5')),
            ('6', 2, 2, 1, 'btn_number', lambda: self._press_number('6')),
            ('−', 2, 3, 1, 'btn_operator', lambda: self._press_operator('-')),
            ('1', 3, 0, 1, 'btn_number', lambda: self._press_number('1')),
            ('2', 3, 1, 1, 'btn_number', lambda: self._press_number('2')),
            ('3', 3, 2, 1, 'btn_number', lambda: self._press_number('3')),
            ('+', 3, 3, 1, 'btn_operator', lambda: self._press_operator('+')),
            ('0', 4, 0, 2, 'btn_zero', lambda: self._press_number('0')),
            ('.', 4, 2, 1, 'btn_number', self._press_decimal),
            ('=', 4, 3, 1, 'btn_operator', self._press_equals),
        ]

        self.operator_buttons = {}

        for label, row, col, colspan, obj_name, action in buttons:
            btn = QPushButton(label)
            btn.setObjectName(obj_name)
            btn.setMinimumHeight(80)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            if obj_name == 'btn_zero':
                btn.setMinimumWidth(170)

            btn.clicked.connect(action)
            grid.addWidget(btn, row, col, 1, colspan)

            if obj_name == 'btn_operator' and label != '=':
                self.operator_buttons[label] = btn

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def _update_display(self):
        """Update the display label with formatted current input."""
        text = self.current_input
        try:
            number = float(text)
            if number == int(number) and '.' not in text:
                formatted = '{:,}'.format(int(number))
            else:
                formatted = text
        except ValueError:
            formatted = text

        # Adjust font size based on length
        length = len(formatted)
        if length <= 6:
            font_size = 72
        elif length <= 9:
            font_size = 54
        else:
            font_size = 40

        self.display.setFont(QFont('Helvetica Neue', font_size, QFont.Light))
        self.display.setText(formatted)

    def _reset_operator_styles(self):
        """Reset all operator button styles to default orange."""
        for label, btn in self.operator_buttons.items():
            btn.setObjectName('btn_operator')
            btn.setStyleSheet('')
            btn.setStyle(btn.style())

    def _highlight_operator(self, label_map):
        """Highlight the active operator button."""
        self._reset_operator_styles()
        symbol_to_label = {'/': '÷', '*': '×', '-': '−', '+': '+'}
        display_label = symbol_to_label.get(self.operator, '')
        if display_label in self.operator_buttons:
            btn = self.operator_buttons[display_label]
            btn.setObjectName('btn_operator_active')
            btn.setStyleSheet(
                'background-color: #ffffff; color: #ff9f0a;'
                'border-radius: 40px; font-size: 28px;'
            )

    def _press_number(self, digit):
        """Handle number button press."""
        self._reset_operator_styles()
        if self.reset_next or self.current_input == '0':
            self.current_input = digit
            self.reset_next = False
        else:
            if len(self.current_input) < 9:
                self.current_input += digit
        self.result_shown = False
        self._update_display()

    def _press_decimal(self):
        """Handle decimal point button press."""
        self._reset_operator_styles()
        if self.reset_next:
            self.current_input = '0.'
            self.reset_next = False
        elif '.' not in self.current_input:
            self.current_input += '.'
        self._update_display()

    def _press_operator(self, op):
        """Handle operator button press (+, -, *, /)."""
        if self.operator and not self.reset_next and not self.result_shown:
            self._calculate()
        self.previous_input = self.current_input
        self.operator = op
        self.reset_next = True
        self.result_shown = False
        self._highlight_operator(op)

    def _press_equals(self):
        """Handle equals button press to compute the result."""
        self._reset_operator_styles()
        if self.operator and self.previous_input:
            self._calculate()
            self.operator = ''
            self.previous_input = ''
            self.result_shown = True

    def _calculate(self):
        """Perform the pending arithmetic calculation."""
        try:
            a = float(self.previous_input)
            b = float(self.current_input)
            if self.operator == '+':
                result = a + b
            elif self.operator == '-':
                result = a - b
            elif self.operator == '*':
                result = a * b
            elif self.operator == '/':
                if b == 0:
                    self.current_input = 'Error'
                    self._update_display()
                    self.operator = ''
                    self.previous_input = ''
                    return
                result = a / b
            else:
                return

            # Format result: remove trailing zeros for whole numbers
            if result == int(result):
                self.current_input = str(int(result))
            else:
                self.current_input = str(round(result, 9))

            self.reset_next = True
            self._update_display()

        except (ValueError, ZeroDivisionError):
            self.current_input = 'Error'
            self._update_display()

    def _press_ac(self):
        """Handle AC (All Clear) button press."""
        self._reset_operator_styles()
        self.current_input = '0'
        self.previous_input = ''
        self.operator = ''
        self.reset_next = False
        self.result_shown = False
        self._update_display()

    def _press_sign(self):
        """Handle +/- (sign toggle) button press."""
        if self.current_input not in ('0', 'Error'):
            if self.current_input.startswith('-'):
                self.current_input = self.current_input[1:]
            else:
                self.current_input = '-' + self.current_input
            self._update_display()

    def _press_percent(self):
        """Handle % (percentage) button press."""
        try:
            value = float(self.current_input) / 100
            if value == int(value):
                self.current_input = str(int(value))
            else:
                self.current_input = str(value)
            self._update_display()
        except ValueError:
            pass


def main():
    """Entry point for the calculator application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()