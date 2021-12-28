try:
    import sys
    import sqlite3

    from os import listdir, remove
    from os.path import isfile, join
    from datetime import datetime
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

DEFAULT_IMAGE_SIZE = [200, 200]
IMAGES_PATH = "./data/images"
datetime = datetime.now()


# Функция обработки исключений
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.id = None
        # Первое подключение к БД
        self.connection = sqlite3.connect("./data/games.db")
        self.cursor = self.connection.cursor()
        # Загружаем дизайн главного окна
        uic.loadUi('./data/designs/main_window.ui', self)
        self.initUI()

    def initUI(self):  # Функция инициализации работы главного окна
        self.update_connection()
        # Указываем заголовок окна
        self.setWindowTitle('Библиотека Игр')
        data = self.get_data()
        # Заполняем таблицу данными из БД
        self.fill_table(data)
        # Фиксируем ширину столбцов таблицы
        self.games_table.resizeColumnsToContents()
        # Заполняем выпадающий список жанров для поиска
        self.fill_genres_box()
        # Указываем функции, которые будет вызываться
        self.add_btn.clicked.connect(self.add_widget_show)  # при нажатии на кнопку добавления информации об игре
        self.edit_btn.clicked.connect(self.edit_widget_show)  # при нажатии на кнопку изменения информации об игре
        self.delete_btn.clicked.connect(self.delete_game)  # при нажатии на кнопку удаления информации об игре
        self.view_btn.clicked.connect(self.view_info)  # при нажатии на кнопку просмотра информации об игре
        self.search_btn.clicked.connect(self.search)  # при нажатии на кнопку поиска игр
        self.update_btn.clicked.connect(self.update_table)  # при нажатии на кнопку обновления

    # Обновление соединения с БД
    def update_connection(self):
        self.connection = sqlite3.connect("./data/games.db")
        self.cursor = self.connection.cursor()

    # Функция, отвечающая за загрузку жанров в выпадающий список жанров главного окна
    def main_window_genres_load(self):
        data = [str(*i) for i in self.cursor.execute("SELECT title FROM genres")]
        self.genres_box.addItem("Все жанры")
        for i in range(len(data)):
            self.genres_box.addItem(data[i])
        self.genres_box.setCurrentIndex(self.cur_index)

    # Функция заполнения таблицы игр
    def fill_table(self, data):
        data_length = len(data)
        # Устанавливаем количество рядов(строк) в таблице
        self.games_table.setRowCount(data_length)
        # Заполняем таблицу
        for i in range(data_length):
            id_, name, author, year = str(data[i][0]), data[i][1], data[i][2], str(data[i][4])
            sql_request = f"SELECT genres.title FROM games LEFT JOIN genres " \
                          f"ON genres.id = games.genre_id WHERE games.id = {int(id_)}"
            genre = str(*[str(*i) for i in self.cursor.execute(sql_request)])
            self.games_table.setItem(i, 0, QTableWidgetItem(name))
            self.games_table.setItem(i, 1, QTableWidgetItem(author))
            self.games_table.setItem(i, 2, QTableWidgetItem(genre))
            self.games_table.setItem(i, 3, QTableWidgetItem(year))
        morph = MorphAnalyzer()
        game_word = morph.parse("игра")[0]
        # Выводим на экран кол-во найденных по запросу игр и склоняем слово игра в зависимости от числа игр
        if data_length != 0:
            # Также если число найденных игр оканчивается на 1, то склоняем слово "найдено"
            if str(data_length)[-1] == "1":
                label = f"Найдена: {data_length} {game_word.make_agree_with_number(data_length).word}".upper()
            else:
                label = f"Найдено: {data_length} {game_word.make_agree_with_number(data_length).word}".upper()
        else:
            label = "Игр с такими характеристиками не найдено".upper()
        self.info_label.setText(label)

    def fill_genres_box(self):
        data = [str(*i) for i in self.cursor.execute("SELECT title FROM genres")]  # Получаем все жанры
        # Добаляем жанры в выпадающих список жанров
        self.genres_box.addItem("Все жанры")
        for i in range(len(data)):
            self.genres_box.addItem(data[i])

    def add_widget_show(self):
        self.widget = GameAddWidget()
        self.widget.show()

    def edit_widget_show(self):
        if self.games_table.selectedItems():
            self.widget = GameEditWidget()
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
                    self.id = str(*[str(*i) for i in self.cursor.execute(sql_request)])
                    self.delete_image()
                    sql_request = f"DELETE FROM games WHERE id = {self.id}"
                    self.cursor.execute(sql_request)
                    self.connection.commit()
                    self.games_table.removeRow(self.games_table.currentRow())
                    self.update_table()
        else:
            QMessageBox.critical(self, "Ошибка ", "Выберите элемент", QMessageBox.Ok)

    def delete_image(self):
        sql_request = f"SELECT image_link FROM games WHERE id = {self.id}"
        image_link = str(*[str(*i) for i in self.cursor.execute(sql_request)])
        remove(image_link)

    def view_info(self):
        if self.games_table.selectedItems():
            self.widget = GameInfoWidget()
            self.widget.show()
        else:
            QMessageBox.critical(self, "Ошибка ", "Выберите элемент", QMessageBox.Ok)

    def search(self):
        genre = self.genres_box.currentText()
        if genre == "Все жанры":
            genre = None
        author, title = self.search_author.text(), self.search_name.text()
        if "".join([i for i in author if i not in "1234567890"]) == author:
            self.update_connection()
            sql_request = f"SELECT * FROM games WHERE game_name LIKE '%{title}%' " \
                          f"AND author LIKE '%{author}%'"
            if genre is not None:
                self.update_connection()
                tmp_sql_request = f"SELECT id FROM genres WHERE title = '{genre}'"
                genre_id = int(*[str(*i) for i in self.cursor.execute(tmp_sql_request)])
                sql_request += f" AND genre_id = {genre_id}"
            data = [list(i) for i in self.cursor.execute(sql_request)]
            self.fill_table(data)
        else:
            QMessageBox.critical(self, "Ошибка ", "Неправильные данные", QMessageBox.Ok)

    def update_table(self):
        self.update_connection()
        data = self.get_data()
        self.fill_table(data)

    def get_data(self):
        sql_request = "SELECT * FROM games"
        data = [list(i) for i in self.cursor.execute(sql_request)]
        return data


# Класс окна добавления информации об игре
class GameAddWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.checked = None
        self.id = None
        self.genre_id = None
        self.game_name = None
        self.year = None
        self.author = None
        self.description = None
        self.image_link = "./data/images/default_image.jpg"
        # Первое подключение к БД
        self.connection = sqlite3.connect("./data/games.db")
        self.cursor = self.connection.cursor()
        # Загружаем дизайн окна
        uic.loadUi('./data/designs/add_game.ui', self)
        self.initUI()

    def initUI(self):  # Функция инициализации работы окна добавления игры
        # Указываем заголовок окна
        self.set_image()
        self.setWindowTitle('Добавление информации')
        self.fill_genres_box()
        self.commit_btn.clicked.connect(self.add_game)
        self.add_image_btn.clicked.connect(self.load_image)

    # Добавляем игру в БД
    def add_game(self):
        self.check()
        if self.checked:
            sql_request = "INSERT INTO games(id,game_name,author,genre_id," \
                          "year,game_description,image_link) VALUES(" + \
                          f"{self.id},'{self.game_name}','{self.author}'," \
                          f"{self.genre_id},{self.year},'{self.description}'," \
                          f"'{self.image_link}')"
            self.cursor.execute(sql_request)
            self.connection.commit()
            GameAddWidget.close(self)

    # Функция, отвечающая за взятие данных из строк ввода
    def data_get(self):
        sql_request = "SELECT id FROM games WHERE ID = (SELECT MAX(id) FROM games)"
        self.id = int(*[str(*i) for i in self.cursor.execute(sql_request)]) + 1
        if self.line_author:
            self.author = self.line_author.text()
        sql_request = f"SELECT DISTINCT genres.id FROM games LEFT JOIN genres ON " \
                      f"genres.id = games.genre_id WHERE genres.title = " \
                      f"'{self.genres_box.currentText()}'"
        self.genre_id = str(*([str(*i) for i in self.cursor.execute(sql_request)]))
        self.game_name = self.line_name.text()
        self.year = int(self.line_year.text())
        self.description = self.description_plain.toPlainText()

    # Функция, проверяющая введённые данные
    def check(self):
        self.data_get()
        if not self.author:
            QMessageBox.critical(self, "Ошибка ", "Введите автора", QMessageBox.Ok)
            self.checked = False
        elif not self.game_name:
            QMessageBox.critical(self, "Ошибка ", "У игры должно быть название",
                                 QMessageBox.Ok)
            self.checked = False
        elif 1952 > int(self.year) > datetime.year:
            QMessageBox.critical(self, "Ошибка ", f"Игры не могли быть созданы в "
                                                  f"{self.year} году",
                                 QMessageBox.Ok)
            self.checked = False
        else:
            self.checked = True

    # Наполняем выпадающий список жанров
    def fill_genres_box(self):
        # Получаем все жанры
        data = [str(*i) for i in self.cursor.execute("SELECT title FROM genres")]
        # Добаляем жанры в выпадающий список жанров
        for i in range(len(data)):
            self.genres_box.addItem(data[i])

    # Загружаем изображение
    def load_image(self):
        self.image_link = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                                      'Картинка (*.jpg)')[0]
        if self.image_link:
            self.check_image.setCheckState(1)
        else:
            self.check_image.setCheckState(0)
        self.set_image()
        self.copy_image_to_project()

    # Функция, копирующая изображение в папку проекта
    def copy_image_to_project(self):
        files = [file for file in listdir(IMAGES_PATH) if isfile(join(IMAGES_PATH, file))]
        self.image_link = self.image_link.split("/")[-1]
        # Проверка на наличие такого же файла в папке
        if self.image_link in files:
            splitted_link = self.image_link.split(".")
            self.image_link = splitted_link[0] + \
                              f"-{datetime.day}-{datetime.month}-{datetime.year}-" \
                              f"{datetime.hour}-{datetime.minute}-{datetime.second}" \
                              + f".{splitted_link[1]}"
        self.image_link = f"./data/images/{self.image_link}"
        print(self.image_link)
        self.image_label.pixmap().save(self.image_link)

    # Устанавливаем изображение на image_label
    def set_image(self):
        image = QPixmap(self.image_link).scaled(QSize(*DEFAULT_IMAGE_SIZE))
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setPixmap(image)

    # Функция, сообщающая о закрытии окна и проверяющая раннюю загрузку изображения
    def closeEvent(self, event):
        # Если закрыто нажатием на крестик - просто закрывать окно (Исключение)
        if Qt.WA_QuitOnClose:
            return
        if self.check_image.checkState() == 0:
            warning_box = QMessageBox().warning(self, "Предупреждение",
                                                "Вы не загрузили изображение",
                                                QMessageBox.Ok, QMessageBox.Cancel)
            if warning_box == QMessageBox.Cancel:
                self.load_image()


class GameEditWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./data/designs/edit_game.ui', self)
        self.initUI()

    def initUI(self):  # Функция инициализации работы окна изменения игры
        # Указываем заголовок окна
        self.setWindowTitle('Редактирование информации')


class GameInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('./data/designs/description.ui', self)
        self.initUI()

    def initUI(self):  # Функция инициализации работы окна просмотра информации
        # Указываем заголовок окна
        self.setWindowTitle('Информация об игре')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
