# -*- coding: utf-8 -*-

import sys
import os
import tempfile
import traceback
import subprocess

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QMenu,
)

from PyQt6.QtGui import (
    QAction,
    QTextCursor,
    QFont,
    QKeySequence,
)

from PyQt6.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
)

import compiler_c

# RTL CODE EDITOR ============================================================

class ArabicCodeEditor(QTextEdit):

    def __init__(self):
        super().__init__()

        self.setAcceptRichText(False)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.setFont(QFont("Consolas", 13))

        self.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #ffffff;
                border: 1px solid #444;
                padding: 10px;
            }
        """)

        self.setup_actions()


    def setup_actions(self):

        self.undo_action = QAction("تراجع", self)
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction("إعادة", self)
        self.redo_action.triggered.connect(self.redo)

        self.copy_action = QAction("نسخ", self)
        self.copy_action.triggered.connect(self.copy)

        self.cut_action = QAction("قص", self)
        self.cut_action.triggered.connect(self.cut)

        self.paste_action = QAction("لصق", self)
        self.paste_action.triggered.connect(self.paste)

        self.select_all_action = QAction("تحديد الكل", self)
        self.select_all_action.triggered.connect(self.selectAll)

        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)

        self.addAction(self.undo_action)
        self.addAction(self.redo_action)
        self.addAction(self.copy_action)
        self.addAction(self.cut_action)
        self.addAction(self.paste_action)
        self.addAction(self.select_all_action)


    def contextMenuEvent(self, event):

        menu = QMenu(self)

        menu.addAction(self.undo_action)
        menu.addAction(self.redo_action)

        menu.addSeparator()

        menu.addAction(self.copy_action)
        menu.addAction(self.cut_action)
        menu.addAction(self.paste_action)

        menu.addSeparator()

        menu.addAction(self.select_all_action)

        menu.exec(event.globalPos())

# OUTPUT CONSOLE ============================================================

class ConsoleWidget(QTextEdit):

    inputSubmitted = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setAcceptRichText(False)

        self.setFont(QFont("Consolas", 12))

        self.setStyleSheet("""
            QTextEdit {
                background: #111111;
                color: #00ff88;
                border: 1px solid #444;
                padding: 10px;
            }
        """)

        self.input_mode = False
        self.input_start = 0

        self.setup_actions()


    def setup_actions(self):

        self.copy_action = QAction("Copy", self)
        self.copy_action.triggered.connect(self.copy)

        self.paste_action = QAction("Paste", self)
        self.paste_action.triggered.connect(self.paste)

        self.select_all_action = QAction("Select All", self)
        self.select_all_action.triggered.connect(self.selectAll)


    def contextMenuEvent(self, event):

        menu = QMenu(self)

        menu.addAction(self.copy_action)
        menu.addAction(self.paste_action)

        menu.addSeparator()

        menu.addAction(self.select_all_action)

        menu.exec(event.globalPos())


    def append_text(self, text):

        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)


    def enable_input_mode(self):

        self.input_mode = True

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        self.setTextCursor(cursor)

        self.input_start = cursor.position()


    def keyPressEvent(self, event):

        if self.input_mode:

            cursor = self.textCursor()

            if event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter
            ):

                full_text = self.toPlainText()

                user_input = full_text[self.input_start:]

                self.append_text("\n")

                self.input_mode = False

                self.inputSubmitted.emit(user_input)

                return

            if event.key() == Qt.Key.Key_Backspace:

                if cursor.position() <= self.input_start:
                    return

        super().keyPressEvent(event)


# EXECUTION THREAD ============================================================

class ExecutionThread(QThread):

    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    request_input_signal = pyqtSignal()
    finished_signal = pyqtSignal()

    def __init__(self, source_code):
        super().__init__()

        self.source_code = source_code

        self.process = None

        self.temp_dir = None


    def run(self):

        try:

            self.temp_dir = tempfile.mkdtemp()

            cpp_path = os.path.join(
                self.temp_dir,
                "program.cpp"
            )

            exe_path = os.path.join(
                self.temp_dir,
                "program.exe"
            )

            # LEXER=================================================

            self.output_signal.emit(
                "=== Scanning ===\n"
            )

            tokens = compiler_c.scan(
                self.source_code
            )

            self.output_signal.emit(
                f"Tokens Generated: {len(tokens)}\n\n"
            )

            # PARSER =================================================

            self.output_signal.emit(
                "=== Parsing ===\n"
            )

            parser = compiler_c.Parser(tokens)

            tree = parser.parse()

            self.output_signal.emit(
                "Parsing Successful\n\n"
            )

            # SEMANTIC ANALYSIS =================================================

            self.output_signal.emit(
                "=== Semantic Analysis ===\n"
            )

            analyzer = compiler_c.SemanticAnalyzer()

            analyzer.analyze(tree)

            self.output_signal.emit(
                "Semantic Analysis Successful\n\n"
            )

            # GENERATE CPP=================================================

            self.output_signal.emit(
                "=== Generating C++ ===\n"
            )

            analyzer.write_cpp_file(cpp_path)

            self.output_signal.emit(
                f"C++ File: {cpp_path}\n\n"
            )

            # COMPILE C++=================================================

            self.output_signal.emit(
                "=== Compiling ===\n"
            )

            compile_cmd = [
                "g++",
                cpp_path,
                "-o",
                exe_path,
                "-std=c++17"
            ]

            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            if compile_result.stdout:
                self.output_signal.emit(
                    compile_result.stdout
                )

            if compile_result.stderr:
                self.error_signal.emit(
                    compile_result.stderr
                )

            if compile_result.returncode != 0:

                self.error_signal.emit(
                    "\nCompilation Failed\n"
                )

                return

            self.output_signal.emit(
                "Compilation Successful\n\n"
            )

            #  RUN PROGRAM=================================================
            self.output_signal.emit(
                "=== Running Program ===\n\n"
            )

            self.process = subprocess.Popen(
                [exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1
            )

            while True:

                output = self.process.stdout.readline()

                if output:
                    self.output_signal.emit(output)

                    # detect cin wait
                    self.request_input_signal.emit()

                error = self.process.stderr.readline()

                if error:
                    self.error_signal.emit(error)

                if (
                    output == ""
                    and error == ""
                    and self.process.poll() is not None
                ):
                    break

            self.output_signal.emit(
                "\n=== Program Finished ===\n"
            )

        except Exception as e:

            self.error_signal.emit(
                "\n=== ERROR ===\n"
            )

            self.error_signal.emit(
                str(e) + "\n\n"
            )

            self.error_signal.emit(
                traceback.format_exc()
            )

        finally:

            self.finished_signal.emit()

    def send_input(self, text):

        try:

            if (
                self.process
                and self.process.stdin
            ):

                self.process.stdin.write(
                    text + "\n"
                )

                self.process.stdin.flush()

        except Exception as e:

            self.error_signal.emit(
                str(e)
            )


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.thread = None

        self.setWindowTitle(
            "Arabic Programming Language IDE"
        )

        self.resize(1300, 850)

        self.setup_ui()

    # user interface ========================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout()

        central.setLayout(layout)

        # TOP BAR ====================================================

        top_bar = QHBoxLayout()

        self.run_button = QPushButton(
            "تشغيل"
        )

        self.run_button.setStyleSheet("""
            QPushButton {
                background: #0d6efd;
                color: white;
                font-size: 20px;
                padding: 12px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background: #0b5ed7;
            }
        """)

        self.run_button.clicked.connect(
            self.run_program
        )

        top_bar.addWidget(
            self.run_button
        )

        layout.addLayout(top_bar)

        # CODE EDITOR====================================================

        editor_label = QLabel(
            "محرر الكود"
        )

        editor_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)

        layout.addWidget(editor_label)

        self.editor = ArabicCodeEditor()

        self.editor.setPlainText(
            '''رقم رئيسي(){
   اطبع("مرحبا").}
'''
        )

        layout.addWidget(
            self.editor,
            3
        )

        # OUTPUT ====================================================

        output_label = QLabel(
            "المخرجات"
        )

        output_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)

        layout.addWidget(output_label)

        self.console = ConsoleWidget()

        self.console.inputSubmitted.connect(
            self.send_input
        )

        layout.addWidget(
            self.console,
            2
        )

    def append_output(self, text):

        self.console.append_text(text)

    def append_error(self, text):

        self.console.append_text(text)

    def run_program(self):

        source_code = (
            self.editor.toPlainText()
        )

        if not source_code.strip():

            QMessageBox.warning(
                self,
                "Warning!",
                "No code entered."
            )

            return

        self.console.clear()

        self.thread = ExecutionThread(
            source_code
        )

        self.thread.output_signal.connect(
            self.append_output
        )

        self.thread.error_signal.connect(
            self.append_error
        )

        self.thread.request_input_signal.connect(
            self.enable_input
        )

        self.thread.finished_signal.connect(
            self.execution_finished
        )

        self.run_button.setEnabled(False)

        self.thread.start()

    def enable_input(self):

        self.console.enable_input_mode()

    def send_input(self, text):

        if self.thread:
            self.thread.send_input(text)

    def execution_finished(self):

        self.run_button.setEnabled(True)

# MAIN========================================================

def main():

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()