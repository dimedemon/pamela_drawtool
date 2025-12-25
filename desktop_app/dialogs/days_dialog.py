"""
Диалог выбора дней (UPDATED for Config 2.0)
Берет список дней из config.FILE_INFO, который мы наполнили данными из MagParam.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QWidget, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from core import config

class DaysDialog(QDialog):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_days = set(self.app_state.pam_pers) if self.app_state.pam_pers else set()
        
        self.setWindowTitle("Select Days (Source: MagParam2)")
        self.resize(900, 600)
        
        # Основной лейаут
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 1. Информация
        info_layout = QHBoxLayout()
        self.lbl_info = QLabel("Loading...")
        info_layout.addWidget(self.lbl_info)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # 2. Область прокрутки с кнопками
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        self.grid_widget.setLayout(self.grid_layout)
        self.scroll.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll)

        # 3. Кнопки управления
        btn_layout = QHBoxLayout()
        
        btn_all = QPushButton("Select All")
        btn_all.clicked.connect(self.select_all)
        btn_layout.addWidget(btn_all)
        
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_selection)
        btn_layout.addWidget(btn_clear)
        
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept_selection)
        btn_layout.addWidget(self.btn_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        main_layout.addLayout(btn_layout)
        
        # 4. Заполнение (безопасное)
        self.populate_days()

    def populate_days(self):
        # Достаем данные из config.FILE_INFO (куда мы их загрузили из MagParam)
        file_info = getattr(config, 'FILE_INFO', {})
        
        # Проверка на наличие ключей (работаем со словарем)
        if not isinstance(file_info, dict) or 'RunDays' not in file_info:
            self.lbl_info.setText("Error: No 'RunDays' in config.FILE_INFO")
            print("DEBUG: FILE_INFO keys:", file_info.keys() if isinstance(file_info, dict) else "Not a dict")
            return

        days = file_info['RunDays']
        # Completeness может не быть, тогда считаем все хорошими
        completeness = file_info.get('Completeness', [1.0] * len(days))
        
        if len(days) == 0:
            self.lbl_info.setText("List of days is empty!")
            return

        self.lbl_info.setText(f"Available Days: {len(days)}")
        
        # Рисуем сетку
        row, col = 0, 0
        max_cols = 20 # Количество кнопок в строке
        
        self.buttons = {} # day_num -> button
        
        for i, day in enumerate(days):
            day_num = int(day)
            qual = completeness[i] if i < len(completeness) else 0
            
            btn = QPushButton(str(day_num))
            btn.setCheckable(True)
            btn.setFixedSize(40, 25)
            
            # Логика цвета (Зеленый = ОК, Красный = Плохо)
            if qual > 0.9:
                color = "#cfc" # Light Green
            elif qual > 0.5:
                color = "#ffc" # Yellow
            else:
                color = "#fcc" # Red
                
            # Если выбран
            if day_num in self.selected_days:
                btn.setChecked(True)
                btn.setStyleSheet(f"background-color: #aaf; font-weight: bold;")
            else:
                btn.setStyleSheet(f"background-color: {color};")
            
            # Привязываем ID дня к кнопке
            btn.clicked.connect(lambda checked, d=day_num: self.on_btn_clicked(d))
            
            self.grid_layout.addWidget(btn, row, col)
            self.buttons[day_num] = btn
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def on_btn_clicked(self, day_num):
        btn = self.buttons[day_num]
        if btn.isChecked():
            self.selected_days.add(day_num)
            btn.setStyleSheet("background-color: #aaf; font-weight: bold;")
        else:
            self.selected_days.discard(day_num)
            # Возвращаем цвет (упрощенно зеленый, т.к. MagParam говорит что все ок)
            btn.setStyleSheet("background-color: #cfc;")

    def select_all(self):
        for day, btn in self.buttons.items():
            if not btn.isChecked():
                btn.click() # Эмулируем клик

    def clear_selection(self):
        for day, btn in self.buttons.items():
            if btn.isChecked():
                btn.click()

    def accept_selection(self):
        # Сохраняем в state
        self.app_state.pam_pers = sorted(list(self.selected_days))
        print(f"DEBUG: Selected days count: {len(self.app_state.pam_pers)}")
        self.accept()
