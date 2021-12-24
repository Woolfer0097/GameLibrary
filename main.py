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
        QFileDialog, QDialog, QInputDialog, \
        QHeaderView

except ModuleNotFoundError as e:
    print(f"Ошибка: {e}")
    sys.exit()
except ImportError as e:
    print(f"Ошибка: {e}")
    sys.exit()


# Функция обработки исключений
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


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
        self.update_connection()
        # Указываем заголовок окна
        self.setWindowTitle('Библиотека Игр')
        data = self.get_data()
        # Заполняем таблицу данными из БД
        self.fill_table(data)
        # Указываем функции, которые будет вызываться
        self.add_btn.clicked.connect(self.add_widget_show)  # при нажатии на кнопку добавления информации об игре
        self.edit_btn.clicked.connect(self.edit_widget_show)  # при нажатии на кнопку изменения информации об игре
        self.delete_btn.clicked.connect(self.delete_game)  # при нажатии на кнопку удаления информации об игре
        self.view_btn.clicked.connect(self.view_info)  # при нажатии на кнопку просмотра информации об игре

    # Обновление соединения с БД
    def update_connection(self):
        self.connection = sqlite3.connect("./data/games.db")
        self.cursor = self.connection.cursor()

    # Функция заполнения таблицы игр
    def fill_table(self, data):
        data_length = len(data)
        self.games_table.setRowCount(data_length)
        for i in range(data_length):
            id_, name, year = str(data[i][0]), data[i][1], str(data[i][4])
            sql_request = f"SELECT genres.title FROM games LEFT JOIN genres " \
                          f"ON genres.id = games.genre_id WHERE games.id = {int(id_)}"
            genre = str(*[str(*i) for i in self.cursor.execute(sql_request)])
            sql_request = f"SELECT authors.title FROM games LEFT JOIN authors " \
                          f"ON authors.id = games.author_id WHERE games.id = {int(id_)}"
            author = str(*[str(*i) for i in self.cursor.execute(sql_request)])
            self.games_table.setItem(i, 0, QTableWidgetItem(name))
            self.games_table.setItem(i, 1, QTableWidgetItem(author))
            self.games_table.setItem(i, 2, QTableWidgetItem(genre))
            self.games_table.setItem(i, 3, QTableWidgetItem(year))
        morph = MorphAnalyzer()
        game_word = morph.parse("игра")[0]
        if data_length != 0:
            # Выводим кол-во найденных по запросу игр и склоняем слово игра в зависимости от числа игр
            self.info_label.setText(f"Найдено: {data_length} "
                                    f"{game_word.make_agree_with_number(data_length).word}")
        else:
            self.info_label.setText("Книг с такими характеристиками не найдено")
        self.games_table.resizeColumnsToContents()

    def add_widget_show(self):
        self.widget = GameAdd()
        self.widget.show()

    def edit_widget_show(self):
        if self.games_table.selectedItems():
            self.widget = GameEdit()
            self.widget.show()
        else:
            QMessageBox.critical(self, "Ошибка ", "Выберите элемент", QMessageBox.Ok)

    def delete_game(self):
        if self.games_table.selectedItems():
            warning = QMessageBox().warning(self, "Предупреждение",
                                            "Вы уверены, что хотите удалить эту игру?",
                                            QMessageBox.Ok, QMessageBox.Cancel)
            if warning == QMessageBox.Ok:
                self.update_table()
                if self.games_table.selectedItems():
                    game_name = self.games_table.item(self.games_table.currentRow(), 0).text()
                    sql_request = f"SELECT id FROM games WHERE game_name = '{game_name}'"
                    id_ = str(*[str(*i) for i in self.cursor.execute(sql_request)])
                    sql_request = f"DELETE FROM games WHERE id = {id_}"
                    self.cursor.execute(sql_request)
                    self.connection.commit()
                    self.games_table.removeRow(self.games_table.currentRow())
                    self.update_table()
        else:
            QMessageBox.critical(self, "Ошибка ", "Выберите элемент", QMessageBox.Ok)

    def view_info(self):
        if self.games_table.selectedItems():
            self.widget = GameInfo()
            self.widget.show()
        else:
            QMessageBox.critical(self, "Ошибка ", "Выберите элемент", QMessageBox.Ok)

    def update_table(self):
        self.update_connection()
        data = self.get_data()
        self.fill_table(data)

    def get_data(self):
        sql_request = "SELECT * FROM games"
        data = [list(i) for i in self.cursor.execute(sql_request)]
        return data


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
    sys.excepthook = except_hook
    sys.exit(app.exec())
