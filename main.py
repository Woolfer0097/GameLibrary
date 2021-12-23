try:
    import sys
    import sqlite3
    import os.path

    from pymorphy2 import MorphAnalyzer
    from PyQt5 import uic
    from PyQt5.QtCore import Qt, QSize
    from PyQt5.QtGui import QPixmap, QFontDatabase
    from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
    from PyQt5.QtWidgets import QApplication, \
        QMainWindow, QWidget, \
        QMessageBox, QTableWidgetItem, \
        QFileDialog, QDialog, QInputDialog

except ModuleNotFoundError as e:
    print(f"Ошибка: {e}")
    sys.exit()
except ImportError as e:
    print(f"Ошибка: {e}")
    sys.exit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.cur_index = 0
        self.connection = sqlite3.connect("./data/games.db")
        self.cursor = self.connection.cursor()
        uic.loadUi('./data/designs/main_window.ui', self)  # Загружаем дизайн главного окна
        self.initUI()

    def initUI(self):
        # Указываем заголовок окна
        self.setWindowTitle('Библиотека Игр')
        # Указываем функции, которые будет вызываться
        self.add_btn.clicked.connect(self.add_game)  # при нажатии на кнопку добавления информации об игре
        self.edit_btn.clicked.connect(self.edit_game)  # при нажатии на кнопку изменения информации об игре
        self.delete_btn.clicked.connect(self.delete_game)  # при нажатии на кнопку удаления информации об игре
        self.view_btn.clicked.connect(self.view_info)

    def add_game(self):
        # ...
        self.widget = GameAdd()
        self.widget.show()

    def edit_game(self):
        # ...
        self.widget = GameEdit()
        self.widget.show()

    def delete_game(self):
        pass

    def view_info(self):
        self.widget = GameInfo()
        self.widget.show()


# Класс окна добавления информации об игре
class GameAdd(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./data/designs/add_game.ui', self)
        self.initUI()

    def initUI(self):
        # Указываем заголовок окна
        self.setWindowTitle('Добавление информации')


class GameEdit(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./data/designs/edit_game.ui', self)
        self.initUI()

    def initUI(self):
        # Указываем заголовок окна
        self.setWindowTitle('Редактирование информации')


class GameInfo(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./data/designs/description.ui', self)
        self.initUI()

    def initUI(self):
        # Указываем заголовок окна
        self.setWindowTitle('Информация об игре')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
