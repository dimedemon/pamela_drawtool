"""
Порт pan01_set02_Selections.m

Создает виджеты для "GeoSelection" и "Selection".
Реализует сложную логику перекрестного связывания
(обновление одного списка при изменении другого).
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QGroupBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
import numpy as np
def create_selections_widget(app_state: ApplicationState, connector: QtConnector):
    """
    Создает QGroupBox, содержащий лейбл и два выпадающих списка.
    """
    # 1. Создаем виджеты
    widget = QGroupBox("Selection") # Используем GroupBox как в MATLAB
    layout = QHBoxLayout()
    widget.setLayout(layout)

    # Убираем лишние отступы
    layout.setContentsMargins(5, 10, 5, 5) # top=10 для заголовка

    # label = QLabel("Selection:") # Лейбл теперь в заголовке GroupBox
    combo_geo = QComboBox()
    combo_selection = QComboBox()
    
    # Загружаем константы
    GEO_STR = config.GEO_STR
    SELECT_STR = config.SELECT_STR
    GS_ARRAY = config.GS_ARRAY # Матрица связей
    
    combo_geo.addItems(GEO_STR)
    combo_selection.addItems(SELECT_STR)
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding) - это самая сложная часть
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_geo_changed(index):
        if index >= 0:
            app_state.geo_selection = GEO_STR[index]

    def on_selection_changed(index):
        if index >= 0:
            app_state.selection = SELECT_STR[index]

    combo_geo.currentIndexChanged.connect(on_geo_changed)
    combo_selection.currentIndexChanged.connect(on_selection_changed)

    # --- Связь: Ядро -> GUI ---

    def on_core_geo_changed(new_geo_value):
        """
        Вызывается, когда ЯДРО меняет GeoSelection.
        Обновляет комбо-бокс 'Geo' И фильтрует комбо-бокс 'Selection'.
        """
        # 1. Обновляем 'Geo'
        if new_geo_value in GEO_STR:
            geo_idx = GEO_STR.index(new_geo_value)
            
            # Блокируем сигналы, чтобы не вызвать on_geo_changed (бесконечный цикл)
            with QSignalBlocker(combo_geo):
                combo_geo.setCurrentIndex(geo_idx)
            
            # 2. Фильтруем 'Selection'
            current_sel_idx = combo_selection.currentIndex()
            update_popup(
                combo_selection,    # какой список обновляем
                SELECT_STR,         # его опции
                GS_ARRAY[geo_idx, :], # строка из матрицы (какие 'Selection' доступны)
                current_sel_idx
            )

    def on_core_selection_changed(new_selection_value):
        """
        Вызывается, когда ЯДРО меняет Selection.
        Обновляет комбо-бокс 'Selection' И фильтрует комбо-бокс 'Geo'.
        """
        # 1. Обновляем 'Selection'
        if new_selection_value in SELECT_STR:
            sel_idx = SELECT_STR.index(new_selection_value)
            
            with QSignalBlocker(combo_selection):
                combo_selection.setCurrentIndex(sel_idx)

            # 2. Фильтруем 'Geo'
            current_geo_idx = combo_geo.currentIndex()
            update_popup(
                combo_geo,          # какой список обновляем
                GEO_STR,            # его опции
                GS_ARRAY[:, sel_idx], # столбец из матрицы (какие 'Geo' доступны)
                current_geo_idx
            )

    connector.geo_selection_changed.connect(on_core_geo_changed)
    connector.selection_changed.connect(on_core_selection_changed)
    
    # 4. Инициализация
    # Вызываем оба обработчика, чтобы установить начальные значения И применить фильтры
    on_core_geo_changed(app_state.geo_selection)
    on_core_selection_changed(app_state.selection)
    
    # Добавляем виджеты в макет
    # layout.addWidget(label)
    layout.addWidget(combo_geo)
    layout.addWidget(combo_selection)
    
    return widget

def update_popup(combo_box: QComboBox, all_items: list, availability_mask: np.ndarray, current_idx: int):
    """
    Вспомогательная функция для "покраски" недоступных опций в QComboBox.
    (Замена 'HTMLTextColor' из MATLAB)
    """
    gray_color = QColor('gray')
    black_color = QColor('black') # Цвет по умолчанию

    # Блокируем сигналы на время обновления
    with QSignalBlocker(combo_box):
        for i, item_text in enumerate(all_items):
            is_available = availability_mask[i]
            
            if is_available:
                # Включаем опцию и ставим черный цвет
                combo_box.model().item(i).setEnabled(True)
                combo_box.setItemData(i, black_color, Qt.ForegroundRole)
            else:
                # Выключаем опцию и ставим серый цвет
                combo_box.model().item(i).setEnabled(False)
                combo_box.setItemData(i, gray_color, Qt.ForegroundRole)

    # Важно: Проверяем, не оказался ли текущий выбор "серым"
    if not availability_mask[current_idx]:
        # Текущий выбор стал невалидным.
        # Ищем первый доступный и переключаемся на него.
        first_available_idx = np.argmax(availability_mask)
        if availability_mask[first_available_idx]:
            combo_box.setCurrentIndex(int(first_available_idx))
        # (Это автоматически вызовет on_geo_changed или on_selection_changed,
        # что обновит app_state и исправит состояние)
