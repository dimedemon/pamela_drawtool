"""
Порт pan01_set03_Binnings.m (ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ)

Исправлена логика парсинга (regex) и регистр (lb, eb).
"""
import re
import numpy as np
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QGroupBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

# --- (Код _get_available_binnings остается тем же) ---
try:
    _META_DATA = config._load_mat_file(config.METADATA_FILE)
    if _META_DATA is None:
        print("Binnings.py: Не удалось загрузить file_metadata.mat. Фильтрация будет отключена.")
        _META_DATA = {}
except Exception as e:
    print(f"Binnings.py: Ошибка загрузки file_metadata.mat: {e}. Фильтрация будет отключена.")
    _META_DATA = {}

def _get_available_binnings(flux_version_str: str) -> set:
    if not _META_DATA:
        return set(config.BINNING_STR)
    try:
        version_num = float(flux_version_str.replace('v', ''))
        version_matches = (_META_DATA['fluxVersions'] == version_num) & \
                          (_META_DATA['stdbinnings'] != '')
        available = np.unique(_META_DATA['stdbinnings'][version_matches])
        return set(available)
    except Exception as e:
        print(f"Ошибка фильтрации биннингов: {e}")
        return set(config.BINNING_STR)
# --- (Конец _get_available_binnings) ---


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
    BINNING_STR = config.BINNING_STR
    combo_binnings.addItems(BINNING_STR)
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_binnings_changed(index):
        """Вызывается, когда пользователь меняет биннинг в GUI."""
        if index < 0:
            return
            
        selected_binning = combo_binnings.itemText(index)
        
        # Проверяем, не "серая" ли опция.
        item_data = combo_binnings.itemData(index, Qt.ForegroundRole)
        if item_data == QColor('gray'):
            first_available_idx = 0
            for i in range(combo_binnings.count()):
                if combo_binnings.itemData(i, Qt.ForegroundRole) != QColor('gray'):
                    first_available_idx = i
                    break
            with QSignalBlocker(combo_binnings):
                combo_binnings.setCurrentIndex(first_available_idx)
            on_binnings_changed(first_available_idx)
            return

        # --- ИСПРАВЛЕННАЯ ЛОГИКА ПАРСИНГА ---
        
        # Пытаемся распознать '...E...' (Energy)
        matches_E = re.match(r'P(\d+)L(\d+)E(\d+)', selected_binning)
        
        # Пытаемся распознать '...R...' (Rigidity)
        matches_R = re.match(r'P(\d+)L(\d+)R(\d+)', selected_binning)

        if matches_E:
            print(f"Binnings: Распознан E-биннинг: {selected_binning}")
            app_state.update_multiple(
                stdbinning=selected_binning,
                pitchb=int(matches_E.group(1)),
                lb=int(matches_E.group(2)),   # <--- ИСПРАВЛЕНО: 'lb'
                ror_e=1, # 1 = E
                eb=int(matches_E.group(3))    # <--- ИСПРАВЛЕНО: 'eb'
            )
        elif matches_R:
            print(f"Binnings: Распознан R-биннинг: {selected_binning}")
            app_state.update_multiple(
                stdbinning=selected_binning,
                pitchb=int(matches_R.group(1)),
                lb=int(matches_R.group(2)),   # <--- ИСПРАВЛЕНО: 'lb'
                ror_e=2, # 2 = R
                eb=int(matches_R.group(3))    # <--- ИСПРАВЛЕНО: 'eb' (eb и rb - это один и тот же параметр)
            )
        else:
            # Если не распознали, обновляем только строку
            print(f"Binnings: Не удалось распознать {selected_binning}, обновляем только строку.")
            app_state.stdbinning = selected_binning
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---

    combo_binnings.currentIndexChanged.connect(on_binnings_changed)

    # --- Связь: Ядро -> GUI ---

    def on_core_stdbinning_changed(new_stdbinning):
        if new_stdbinning in BINNING_STR:
            idx = BINNING_STR.index(new_stdbinning)
            with QSignalBlocker(combo_binnings):
                combo_binnings.setCurrentIndex(idx)

    def on_core_flux_version_changed(new_flux_version):
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
                        first_available_idx = i
                    combo_binnings.model().item(i).setEnabled(True)
                    combo_binnings.setItemData(i, black_color, Qt.ForegroundRole)
                    if item_text == current_selection:
                        selection_is_still_valid = True
                else:
                    combo_binnings.model().item(i).setEnabled(False)
                    combo_binnings.setItemData(i, gray_color, Qt.ForegroundRole)
        
        if not selection_is_still_valid:
            # Обновляем GUI...
            combo_binnings.setCurrentIndex(first_available_idx)
            # ...и принудительно обновляем Ядро
            on_binnings_changed(first_available_idx)

    connector.stdbinning_changed.connect(on_core_stdbinning_changed)
    connector.flux_version_changed.connect(on_core_flux_version_changed)
    
    # 4. Инициализация
    on_core_flux_version_changed(app_state.flux_version)
    on_core_stdbinning_changed(app_state.stdbinning)
    
    layout.addWidget(combo_binnings)
    
    return widget
