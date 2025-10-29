"""
Модуль конфигурации (Фаза 1)

Хранит константы, пути и загрузчики метаданных.
(Портировано из getGUIConstants.m)
"""

import os
import numpy as np
from scipy.io import loadmat

# --- Пути ---
# TODO: В будущем это можно вынести в .env или config.ini
# Мы будем использовать относительный путь 'data/'
# (Предполагается, что папка 'data' лежит в корне проекта)

BASE_DATA_PATH = 'data' 
GEN_PATH = os.path.join(BASE_DATA_PATH, 'dirflux_newStructure')
METADATA_FILE = os.path.join(GEN_PATH, 'file_metadata.mat')

# --- Константы GUI ---

HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

GEN_STR = [
    'Alt1sec', 'Babs1sec', 'BB01sec', 'Blaz', 'Blzen', 'L1sec',
    'Lat1sec', 'Lon1sec', 'Roll1sec', 'SPitch1sec', 'Yaw1sec',
    'aTime', 'eqpitchlim', 'LocPitch', 'maxgyro', 'mingyro',
    'TimeGap1sec', 'TimeGap2sec', 'trkMaskI1sec', 'trkMaskS1sec',
    'Trig1sec'
]

GEN_X_STR = ['aTime', 'aTime', 'L1sec', 'BB01sec', 'Alt1sec', 'Lat1sec', 'Lon1sec']

WHAT_X_VARS = [
    'Date & time', 'time from entrance', 'L', 'B/B0', 'Altitude',
    'latitude', 'longitude'
]

WHAT_Y_VARS = [
    'Altitude', 'Babs', 'B/B_0', 'Baz loc', 'Bzen loc', 'L', 'latitude',
    'longitude', 'Roll', 'SPitch', 'Yaw', 'absolute time',
    'maximum eqpitch', 'Local Pitch', 'maximum gyroangle',
    'minimum gyroangle', 'TimeGap1', 'TimeGap2', 'TrkMaskI', 'TrkMaskS',
    'Trigger'
]

UNIT_X_STR = ['m', 's', 'Re', '', 'km', '^{\circ}', '^{\circ}']

UNIT_STR = [
    'km', 'G', '', 'G', 'G', 'Re', '^{\circ}', '^{\circ}', '^{\circ}',
    '^{\circ}', '^{\circ}', 's', '^{\circ}', '^{\circ}', '^{\circ}',
    '^{\circ}', 's', 's', '', '', ''
]

# --- Загрузчики метаданных ---

def _load_metadata(file_path=METADATA_FILE):
    """Приватная функция для загрузки .mat файла метаданных."""
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл метаданных не найден по пути: {file_path}")
        print("         Убедитесь, что папка 'data/' существует в корне проекта.")
        return None
    try:
        return loadmat(file_path)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def get_unique_stdbinnings():
    """Портировано из getUniqueStdbinnings."""
    loaded_data = _load_metadata()
    if loaded_data is None:
        return []
    
    stdbinnings = loaded_data.get('stdbinnings', [])
    if stdbinnings is None or stdbinnings.size == 0:
        return []
        
    # loadmat загружает ячейки строк MATLAB как 2D-массив объектов
    # Нам нужно извлечь строки [0][0]
    non_empty = [
        s[0] for s in stdbinnings.flatten() 
        if s.size > 0 and isinstance(s[0], str) and s[0].strip()
    ]
    unique_binnings = sorted(list(set(non_empty)))
    return unique_binnings

def get_selection_coexistence():
    """Портировано из getSelectionCoexistence."""
    loaded_data = _load_metadata()
    if loaded_data is None:
        return [], [], np.array([])
    
    geo_selections_raw = loaded_data.get('GeoSelections', [])
    selections_raw = loaded_data.get('Selections', [])

    # Извлекаем строки из массива ячеек
    geo_list = [g[0] for g in geo_selections_raw.flatten() if g.size > 0 and isinstance(g[0], str)]
    sel_list = [s[0] for s in selections_raw.flatten() if s.size > 0 and isinstance(s[0], str)]
    
    # Убедимся, что у нас одинаковое количество строк
    min_len = min(len(geo_list), len(sel_list))
    
    # Фильтрация 'None'
    valid_pairs = [
        (g, s) for g, s in zip(geo_list[:min_len], sel_list[:min_len])
        if g != 'None' and s != 'None'
    ]
    
    if not valid_pairs:
        return [], [], np.array([])
        
    valid_geo, valid_sel = zip(*valid_pairs)

    geo_str = sorted(list(set(valid_geo)))
    select_str = sorted(list(set(valid_sel)))
    
    # Создание карты индексов
    geo_map = {name: i for i, name in enumerate(geo_str)}
    sel_map = {name: i for i, name in enumerate(select_str)}
    
    # Создание матрицы сосуществования
    coexistence_matrix = np.zeros((len(geo_str), len(select_str)), dtype=bool)
    
    for g, s in zip(valid_geo, valid_sel):
        if g in geo_map and s in sel_map:
            coexistence_matrix[geo_map[g], sel_map[s]] = True
            
    return geo_str, select_str, coexistence_matrix

# --- Динамические константы (загружаются при импорте) ---
# Эти переменные будут загружены один раз, когда модуль будет импортирован

print("Загрузка метаданных PAMELA (config.py)...")
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY = get_selection_coexistence()
print("Метаданные загружены.")
