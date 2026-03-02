import sys
import os
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog)
from PyQt6.QtCore import Qt
from main_window.ui import Ui_MainWindow
from coffee_dialog.ui import Ui_Dialog


class CoffeeEditDialog(QDialog, Ui_Dialog):
    def __init__(self, parent=None, coffee_data=None):
        super().__init__(parent)
        self.setupUi(self)
        self.coffee_data = coffee_data
        if coffee_data:
            self.load_data()

    def load_data(self):
        self.nameEdit.setText(self.coffee_data[1])
        self.roastCombo.setCurrentText(self.coffee_data[2])
        self.typeCombo.setCurrentText(self.coffee_data[3])
        self.tasteEdit.setText(self.coffee_data[4] if self.coffee_data[4] else "")
        self.priceEdit.setText(str(self.coffee_data[5]))
        self.volumeEdit.setText(str(self.coffee_data[6]))

    def get_data(self):
        try:
            return {
                'name': self.nameEdit.text(),
                'roast_degree': self.roastCombo.currentText(),
                'ground_or_beans': self.typeCombo.currentText(),
                'taste_description': self.tasteEdit.toPlainText(),
                'price': float(self.priceEdit.text()),
                'package_volume': int(self.volumeEdit.text())
            }
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Проверьте правильность ввода")
            return None


class CoffeeApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        data_dir = os.path.join(base_path, 'data')
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, 'coffee.db')
        self.conn = sqlite3.connect(db_path)

        self.setup_table()
        self.create_database()
        self.insert_sample_data()
        self.connect_signals()
        self.load_data()

    def setup_table(self):
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels([
            "ID", "Название сорта", "Степень обжарки",
            "Молотый/В зернах", "Описание вкуса", "Цена", "Объём упаковки"
        ])
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

    def connect_signals(self):
        self.addButton.clicked.connect(self.add_record)
        self.editButton.clicked.connect(self.edit_record)
        self.refreshButton.clicked.connect(self.load_data)
        self.tableWidget.itemDoubleClicked.connect(self.edit_record)

    def create_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coffee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roast_degree TEXT NOT NULL,
                ground_or_beans TEXT NOT NULL,
                taste_description TEXT,
                price REAL NOT NULL,
                package_volume INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def insert_sample_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coffee")
        if cursor.fetchone()[0] == 0:
            sample_data = [
                ("Эфиопский Иргачефф", "Светлая", "Молотый", "Цитрусовые нотки, цветочный аромат", 850.0, 250),
                ("Колумбия Супремо", "Средняя", "В зернах", "Карамель, орехи, шоколад", 950.0, 500),
                ("Бразилия Сантос", "Тёмная", "Молотый", "Шоколад, орехи, низкая кислотность", 780.0, 250),
                ("Кения АА", "Светлая", "В зернах", "Ягодные нотки, вино, цитрус", 1200.0, 300),
                ("Суматра Манделинг", "Тёмная", "Молотый", "Пряности, травы, полное тело", 1100.0, 400)
            ]
            cursor.executemany('''
                INSERT INTO coffee (name, roast_degree, ground_or_beans, taste_description, price, package_volume)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', sample_data)
            self.conn.commit()

    def load_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM coffee ORDER BY id")
        rows = cursor.fetchall()
        
        self.tableWidget.setRowCount(0)
        for row_number, row_data in enumerate(rows):
            self.tableWidget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.tableWidget.setItem(row_number, column_number, item)

    def add_record(self):
        dialog = CoffeeEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO coffee (name, roast_degree, ground_or_beans, taste_description, price, package_volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (data['name'], data['roast_degree'], data['ground_or_beans'],
                      data['taste_description'], data['price'], data['package_volume']))
                self.conn.commit()
                self.load_data()

    def edit_record(self):
        current_row = self.tableWidget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись")
            return
        
        record_id = int(self.tableWidget.item(current_row, 0).text())
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM coffee WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        
        if record:
            dialog = CoffeeEditDialog(self, record)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                if data:
                    cursor.execute('''
                        UPDATE coffee SET name=?, roast_degree=?, ground_or_beans=?, 
                            taste_description=?, price=?, package_volume=? WHERE id=?
                    ''', (data['name'], data['roast_degree'], data['ground_or_beans'],
                          data['taste_description'], data['price'], data['package_volume'], record_id))
                    self.conn.commit()
                    self.load_data()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CoffeeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
