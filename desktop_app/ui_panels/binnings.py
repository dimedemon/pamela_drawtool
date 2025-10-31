"""
Порт pan01_set03_Binnings.m (ОБНОВЛЕННЫЙ)

Реализована полная логика фильтрации (серая подсветка)
в зависимости от 'fluxVersion'.
"""
import re
import numpy as np
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QGroupBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

# --- Загружаем данные из file_metadata.mat ОДИН РАЗ ---
# Это более эффективно, чем загружать его в функции
try:
    _META_DATA = config._load_mat_file(config.METADATA_FILE)
    if _META_DATA is None:
        print("Binnings.py: Не удалось загрузить file_metadata.mat. Фильтрация будет отключена.")
        _META_DATA = {}
except Exception as e:
    print(f"Binnings.py: Ошибка загрузки file_metadata.mat: {e}. Фильтрация будет отключена.")
    _META_DATA = {}

def _get_available_binnings(flux_version_str: str) -> set:
    """
    Возвращает набор (set) доступных биннингов для этой версии
    на основе загруженного file_metadata.mat.
    """
    if not _META_DATA:
        return set(config.BINNING_STR) # Возвращаем все, если метаданные не загружены

    try:
        # 'v09' -> 9.0
        version_num = float(flux_version_str.replace('v', ''))
        
        # Находим индексы, где версия совпадает
        version_matches = (_META_DATA['fluxVersions'] == version_num) & \
                          (_META_DATA['stdbinnings'] != '')
        
        # Получаем уникальные биннинги для этой версии
        available = np.unique(_META_DATA['stdbinnings'][version_matches])
        return set(available)
    except Exception as e:
        print(f"Ошибка фильтрации биннингов: {e}")
        # Возвращаем все как запасной вариант
        return set(config.BINNING_STR)


def create_binnings_widget(app_state: ApplicationState, connector: QtConnector):
    """
    Создает QGroupBox, содержащий лейбл и выпадающий список для биннингов.
    """
    # 1. Создаем виджеты
    widget = QGroupBox("Binnings")
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    combo_binnings = QComboBox()
    
    # 2. Загружаем константы
    BINNING_STR = config.BINNING_STR
    combo_binnings.addItems(BINNING_STR)
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_binnings_changed(index):
        if index < 0:
            return
            
        selected_binning = combo_binnings.itemText(index)
        
        # Проверяем, не "серая" ли опция.
        item_data = combo_binnings.itemData(index, Qt.ForegroundRole)
        if item_data == QColor('gray'):
            # Пользователь выбрал неактивный элемент. Найти первый активный.
            first_available_idx = 0
            for i in range(combo_binnings.count()):
                if combo_binnings.itemData(i, Qt.ForegroundRole) != QColor('gray'):
                    first_available_idx = i
                    break
            # Принудительно возвращаем на первый активный
            with QSignalBlocker(combo_binnings):
                combo_binnings.setCurrentIndex(first_available_idx)
            # Вызываем on_binnings_changed рекурсивно для *нового* индекса
            on_binnings_changed(first_available_idx)
            return

        # Парсим P(d)L(d)E(d)
        matches = re.match(r'P(\d+)L(\d+)E(\d+)', selected_binning)
        
        if matches:
            # Обновляем все поля в app_state
            app_state.update_multiple(
                stdbinning=selected_binning,
                pitchb=int(matches.group(1)),
                Lb=int(matches.group(2)),
                Eb=int(matches.group(3))
            )
        else:
            app_state.stdbinning = selected_binning

    combo_binnings.currentIndexChanged.connect(on_binnings_changed)

    # --- Связь: Ядро -> GUI ---

    def on_core_stdbinning_changed(new_stdbinning):
        """
        Вызывается, когда ЯДРО меняет stdbinning.
        Обновляет комбо-бокс 'Binnings'.
        """
        if new_stdbinning in BINNING_STR:
            idx = BINNING_STR.index(new_stdbinning)
            with QSignalBlocker(combo_binnings):
                combo_binnings.setCurrentIndex(idx)

    def on_core_flux_version_changed(new_flux_version):
        """
        Вызывается, когда ЯДРО меняет fluxVersion.
        Фильтрует (красит серым) комбо-бокс 'Binnings'.
        """
        # --- ИСПРАВЛЕНО: Убрана ЗАГЛУШКА ---
        available_stdbinnings = _get_available_binnings(new_flux_version)
        
        gray_color = QColor('gray')
        black_color = QColor('black')
        
        current_selection = app_state.stdbinning
        selection_is_still_valid = False
        first_available_idx = 0
        
        with QSignalBlocker(combo_binnings):
            for i, item_text in enumerate(BINNING_STR):
                is_available = item_text in available_stdbinnings
                
                if is_available:
                    if first_available_idx == 0:
                        first_available_idx = i # Запоминаем первый доступный
                    
                    combo_binnings.model().item(i).setEnabled(True)
                    combo_binnings.setItemData(i, black_color, Qt.ForegroundRole)
                    
                    if item_text == current_selection:
                        selection_is_still_valid = True
                else:
                    combo_binnings.model().item(i).setEnabled(False)
                    combo_binnings.setItemData(i, gray_color, Qt.ForegroundRole)
        
        # Если текущий выбор стал "серым", принудительно меняем его
        if not selection_is_still_valid:
            combo_binnings.setCurrentIndex(first_available_idx)
            # Обновляем ядро, так как GUI принудительно изменил значение
            on_binnings_changed(first_available_idx)


    connector.stdbinning_changed.connect(on_core_stdbinning_changed)
    connector.flux_version_changed.connect(on_core_flux_version_changed)
    
    # 4. Инициализация
    on_core_flux_version_changed(app_state.flux_version) # Сначала фильтруем
    on_core_stdbinning_changed(app_state.stdbinning) # Затем выбираем
    
    # Добавляем виджеты в макет
    layout.addWidget(combo_binnings)
    
    return widget
