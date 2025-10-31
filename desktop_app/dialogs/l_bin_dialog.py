"""
Порт диалога ShowLbin из pan04_set01_L.m
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QAbstractItemView)
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

class LBinDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.selected_l_values = []
        self.selected_l_max_values = []
        
        self.setWindowTitle(f"L Bins (L{self.app_state.lb})")
        self.setGeometry(250, 250, 300, 500)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 1. Таблица
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        # 2. Кнопки
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.on_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(btn_cancel)
        main_layout.addLayout(button_layout)
        
        # 3. Заполнение
        self.populate_table()
        
        # 4. Настройки
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Позволяем выбирать несколько строк
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def populate_table(self):
        """
        Заполняет таблицу L-бинами из config.BIN_INFO
        """
        try:
            # -1 т.к. Lb в MATLAB начинается с 1
            l_bins = config.BIN_INFO['Lbin'][self.app_state.lb - 1]
        except (IndexError, TypeError):
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Ошибка: L-bin {self.app_state.lb} не найден."))
            return

        l_min_col = l_bins[:-1]
        l_max_col = l_bins[1:]
        
        self.table.setRowCount(len(l_min_col))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["L_min, RE", "L_max, RE"])
        
        for row in range(len(l_min_col)):
            self.table.setItem(row, 0, QTableWidgetItem(f"{l_min_col[row]:.3f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{l_max_col[row]:.3f}"))

    def on_selection_changed(self):
        """Вызывается при изменении выбора в таблице."""
        self.btn_ok.setEnabled(True)
        
    def on_ok(self):
        """
        Сохраняет выбранные значения в app_state.
        """
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        
        if not selected_rows:
            self.reject()
            return
            
        try:
            l_bins = config.BIN_INFO['Lbin'][self.app_state.lb - 1]
            
            # Собираем L (L_min) и L_max (L_max)
            l_values = [l_bins[row] for row in selected_rows]
            l_max_values = [l_bins[row + 1] for row in selected_rows]
            
            # Сохраняем в app_state
            self.app_state.l = l_values
            # Если выбрано одно значение, обновляем Lmax
            if len(l_max_values) == 1:
                self.app_state.l_max = l_max_values[0]
            
            self.accept() # Закрываем
            
        except Exception as e:
            print(f"Ошибка при выборе L-бина: {e}")
            self.reject()
