"""
Порт pan00_InputDataSource.m

Создает виджет для выбора "Input data source".
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from core import config
from desktop_app.qt_connector import QtConnector

def create_input_data_source_widget(app_state, connector):
    """
    Создает QWidget, содержащий лейбл и выпадающий список.
    Возвращает: QWidget
    """
    # 1. Создаем виджеты
    widget = QWidget()
    # Используем QHBoxLayout для горизонтального расположения
    layout = QHBoxLayout()
    # Убираем лишние отступы
    layout.setContentsMargins(0, 0, 0, 0) 
    widget.setLayout(layout)
    
    label = QLabel("Input data source:")
    combo_box = QComboBox()
    
    # 2. Заполняем данными из config
    # Мы загружаем DATA_SOURCE_STR из нашего config.py
    combo_box.addItems(config.DATA_SOURCE_STR)
    
    # 3. Связываем виджет с "клеем" (QtConnector)
    
    # Связь: GUI -> Ядро
    # Когда пользователь меняет значение в QComboBox...
    def on_combo_box_changed(index):
        # ...мы обновляем app_state
        # +1, т.к. в MATLAB 'Value' начинается с 1
        app_state.gen = index + 1 
    
    combo_box.currentIndexChanged.connect(on_combo_box_changed)

    # Связь: Ядро -> GUI
    # Когда connector (клей) говорит, что 'gen' изменился...
    def on_gen_changed(new_gen_value):
        # ...мы обновляем QComboBox
        # -1, т.к. индексы QComboBox начинаются с 0
        combo_box.setCurrentIndex(new_gen_value - 1) 

    connector.gen_changed.connect(on_gen_changed)
    
    # 4. Инициализация (установка начального значения)
    # Устанавливаем текущее значение из app_state
    on_gen_changed(app_state.gen)

    # Добавляем виджеты в макет
    layout.addWidget(label)
    layout.addWidget(combo_box)
    layout.addStretch() # Прижимает виджеты влево
    
    return widget
