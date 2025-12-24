"""
LBinDialog - Crash-Proof Version
"""
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QAbstractItemView, QLabel)
from core import config
from core.state import ApplicationState
import traceback

class LBinDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        # Оборачиваем весь init в try, чтобы окно открылось даже при ошибке
        try:
            super().__init__(parent)
            
            self.app_state = app_state
            self.selected_l_values = []
            self.selected_l_max_values = []
            
            self.setWindowTitle(f"L Bins (Current setting: L{self.app_state.lb})")
            self.resize(400, 600)
            
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            
            # 1. Таблица
            self.table = QTableWidget()
            self.layout.addWidget(self.table)
            
            # 2. Кнопки
            btn_layout = QHBoxLayout()
            self.btn_ok = QPushButton("OK")
            self.btn_ok.setEnabled(False)
            self.btn_ok.clicked.connect(self.on_ok)
            
            btn_cancel = QPushButton("Cancel")
            btn_cancel.clicked.connect(self.reject)
            
            btn_layout.addStretch()
            btn_layout.addWidget(self.btn_ok)
            btn_layout.addWidget(btn_cancel)
            self.layout.addLayout(btn_layout)
            
            # 3. Настройки таблицы
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setSelectionMode(QAbstractItemView.MultiSelection)
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

            # 4. ЗАПОЛНЕНИЕ (Самое опасное место)
            self.populate_table_safe()

        except Exception as e:
            print("!!! CRITICAL ERROR IN DIALOG INIT !!!")
            traceback.print_exc()

    def populate_table_safe(self):
        """
        Пытается заполнить таблицу любыми способами, диагностируя структуру данных.
        """
        print("\n--- DEBUG: STARTING POPULATE ---")
        try:
            # 1. Достаем сырые данные
            # В config.BIN_INFO теперь точно есть ключ 'Lbin', даже если пустой
            raw_data = config.BIN_INFO.get('Lbin', [])
            
            print(f"DEBUG: Raw Lbin type: {type(raw_data)}")
            
            if hasattr(raw_data, 'shape'):
                print(f"DEBUG: Shape: {raw_data.shape}")
            elif isinstance(raw_data, list):
                print(f"DEBUG: List len: {len(raw_data)}")
            
            # 2. Пытаемся найти нужный биннинг
            # app_state.lb - это число (например, 4). Индекс = 3.
            target_idx = self.app_state.lb - 1
            print(f"DEBUG: Looking for index {target_idx}")

            target_bins = None

            # СЦЕНАРИЙ А: Это список массивов (обычный случай)
            # Или объектный массив numpy (array of arrays)
            try:
                if len(raw_data) > target_idx:
                    possible_item = raw_data[target_idx]
                    # Проверяем, похоже ли это на массив границ
                    if hasattr(possible_item, '__len__') and len(possible_item) > 1:
                        target_bins = possible_item
                        print("DEBUG: Found via direct indexing.")
            except:
                pass

            # СЦЕНАРИЙ Б: Это один единственный массив (если в файле всего 1 вариант)
            if target_bins is None:
                # Если сырые данные сами похожи на массив чисел (границ)
                # Проверяем, что внутри числа, а не другие массивы
                first_el = raw_data[0] if len(raw_data) > 0 else None
                if isinstance(first_el, (int, float, np.number)):
                     target_bins = raw_data
                     print("DEBUG: Raw data is the array itself.")

            # Если всё еще пусто
            if target_bins is None:
                raise ValueError(f"Не удалось извлечь биннинг №{self.app_state.lb}. Данные: {str(raw_data)[:50]}...")

            # 3. Обработка массива границ
            # Убеждаемся, что это numpy array и он плоский
            edges = np.array(target_bins).flatten()
            print(f"DEBUG: Edges found. Length: {len(edges)}. Values: {edges[:5]}...")

            if len(edges) < 2:
                self.show_error_in_table("Массив границ пуст или слишком мал")
                return

            l_min = edges[:-1]
            l_max = edges[1:]

            # 4. Рисуем в таблице
            self.table.setRowCount(len(l_min))
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["L_min", "L_max"])

            for i in range(len(l_min)):
                self.table.setItem(i, 0, QTableWidgetItem(f"{l_min[i]:.4f}"))
                self.table.setItem(i, 1, QTableWidgetItem(f"{l_max[i]:.4f}"))
            
            print("DEBUG: Table populated successfully.")

        except Exception as e:
            print(f"!!! ERROR IN POPULATE: {e}")
            traceback.print_exc()
            self.show_error_in_table(f"Error: {e}")

    def show_error_in_table(self, msg):
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setItem(0, 0, QTableWidgetItem(msg))
        self.table.resizeColumnsToContents()

    def on_selection_changed(self):
        self.btn_ok.setEnabled(True)

    def on_ok(self):
        # Простая логика сохранения
        try:
            selected_rows = sorted(list(set(idx.row() for idx in self.table.selectedIndexes())))
            if not selected_rows:
                self.reject()
                return

            # Считываем значения прямо из таблицы (так надежнее)
            l_vals = []
            l_max_vals = []
            for row in selected_rows:
                v_min = float(self.table.item(row, 0).text())
                v_max = float(self.table.item(row, 1).text())
                l_vals.append(v_min)
                l_max_vals.append(v_max)
            
            self.app_state.l = l_vals
            self.app_state.l_max = l_max_vals
            self.accept()
            
        except Exception as e:
            print(f"Error saving selection: {e}")
            self.reject()
