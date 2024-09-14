import json
import sqlite3
import csv
from typing import List
import chardet


class FileHandler:
    def __init__(self, file_path: str, delimiter: str = ','):
        self.file_path = file_path
        self.delimiter = delimiter

    def detect_encoding(self) -> str:
        """ Функция для определения кодировки файла
        """
        with open(self.file_path, 'rb') as file:
            raw_data = file.read(10000)
        result = chardet.detect(raw_data)
        return result['encoding']

    def read_file(self) -> List[List[str]]:
        """ Функция для чтения данных из файлов
        """
        try:
            encoding = self.detect_encoding()
            with open(self.file_path, mode='r', encoding=encoding, errors='replace') as file:
                reader = csv.reader(file, delimiter=self.delimiter)
                data = [[cell.strip().strip('"') for cell in row] for row in reader]
            return data
        except Exception as e:
            print(f"Ошибка при чтении файла {self.file_path}: {e}")
            return []


class DataManager:
    def __init__(self, file1_data: List[List[str]], file2_data: List[List[str]]):
        self.data = file1_data + file2_data
        self.sorted_data = []

    def merge_and_sort(self):
        """ Функция для объединения данных и их сортировки по второму столбцу
        """
        try:
            # Сортировка данных по второму столбцу
            self.sorted_data = sorted([row for row in self.data if len(row) > 1], key=lambda x: x[1])
        except Exception as e:
            print(f"Ошибка при объединении и сортировке данных: {e}")

    def save_to_json(self, json_file_path: str) -> str:
        """ Функция для сохранения данных в JSON-файл
        """
        try:
            # Сохраняем именно отсортированные данные
            if not self.sorted_data:
                print("Нет отсортированных данных для сохранения в JSON.")
                return ""
            json_data = json.dumps(self.sorted_data, ensure_ascii=False, indent=4)
            with open(json_file_path, mode='w', encoding='utf-8') as file:
                file.write(json_data)
            return json_data
        except Exception as e:
            print(f"Ошибка при сохранении в JSON: {e}")
            return ""


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """ Функция для создания таблицы в базе данных SQLite
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка при создании таблицы: {e}")

    def json_exists_in_db(self, json_data: str) -> bool:
        """ Функция для проверки: существует ли такой же JSON в базе данных
        """
        try:
            self.cursor.execute('SELECT COUNT(1) FROM json_data WHERE data = ?', (json_data,))
            result = self.cursor.fetchone()[0]
            return result > 0
        except Exception as e:
            print(f"Ошибка при проверке данных в базе: {e}")
            return False

    def save_json_to_db(self, json_data: str):
        """ Функция для сохранения JSON в базу данных
        """
        if not json_data:
            print("Нет данных для добавления в базу данных. Сохранение отменено.")
            return
        if self.json_exists_in_db(json_data):
            print("Данные уже существуют в базе данных. Сохранение отменено.")
            return

        try:
            self.cursor.execute('INSERT INTO json_data (data) VALUES (?)', (json_data,))
            self.conn.commit()
            print(f"Данные успешно сохранены в базу данных {self.db_path}")
        except Exception as e:
            print(f"Ошибка при сохранении в базу данных: {e}")

    def close(self):
        """ Функция закрытия подключения к базе данных
        """
        self.conn.close()


def main():
    file1 = 'Тестовый файл1.txt'
    file2 = 'Тестовый файл2.txt'
    output_json = 'data.json'
    db_path = 'data.db'

    # Создание объектов классов
    file1_handler = FileHandler(file1, delimiter=',')
    file2_handler = FileHandler(file2, delimiter=';')

    # Чтение данных из файлов
    file1_data = file1_handler.read_file()
    file2_data = file2_handler.read_file()

    # Объединение и сортировка данных
    data_manager = DataManager(file1_data, file2_data)
    data_manager.merge_and_sort()

    # Сохранение данных в JSON-файл
    json_data = data_manager.save_to_json(output_json)

    # Работа с базой данных
    db_manager = DatabaseManager(db_path)
    db_manager.save_json_to_db(json_data)
    db_manager.close()


if __name__ == "__main__":
    main()
