"""
Модуль конфигурации (Фаза 1) - EXTERNAL DRIVE EDITION

Хранит константы, пути, загрузчики метаданных И БИННИНГОВ.
Настроен для работы с внешним накопителем.
"""

import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics  # Импортируем наш модуль кинематики

# --- Константы (из DrawTool3.m) ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 

# --- ПУТИ (Настройка внешнего диска) ---
# Путь к корню папки с данными на внешнем диске
BASE_DATA_PATH = '/Volumes/T7 Touch/dirflux_newStructure'

# GEN_PATH - это корень структуры данных (совпадает с BASE_DATA_PATH)
GEN_PATH = BASE_DATA_PATH

# Путь к файлу метаданных (предполагается, что он в корне dirflux_newStructure)
METADATA_FILE = os.path.join(GEN_PATH, 'file_metadata.mat')

# Путь к BinningInfo.mat
# Логика: сначала смотрим на диске, если нет — берем из папки проекта data/
_ext_bin_path = os.path.join(BASE_DATA_PATH, 'BinningInfo.mat')
_loc_bin_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'BinningInfo.mat')

if os.path.exists(_ext_bin_path):
    BINNING_INFO_FILE = _ext_bin_path
else:
    # Fallback на локальный файл, если на диске нет
    BINNING_INFO_FILE = os.path.abspath(_loc_bin_path)

# --- Константы GUI (из getGUIConstants.m) ---
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
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation',
                   'Anisotropic flux simulation','External exp. data',
                   'Empyrical models','Space weather data']
TBIN_STR = ['passage','day','month','3months','6months','year','bartels',
            'Separate Periods']
DISTR_VARS = ['Flux','Number of events','Gathering power','livetime',
              'Countrate','Relative error of flux','Four entities at once']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution',
              'Radial distribution','Temporal variations','Variations along orbit',
              'Fluxes Histogram','L-pitch map','E-pitch map','E-L map',
              'Auxiliary parameters','pitch-arcs']
SP_WEATHER_STR = ['f10p7','SSN','Dst','Kp','Ap']

# --- Загрузчики метаданных ---

def _load_mat_file(file_path):
    """Общая функция-загрузчик .mat файлов."""
    if not os.path.exists(file_path):
        # print(f"ВНИМАНИЕ: Файл не найден по пути: {file_path}")
        return None
    try:
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def get_selection_coexistence(file_path=METADATA_FILE):
    """Портировано из getSelectionCoexistence."""
    loaded_data = _load_mat_file(file_path)
    if loaded_data is None:
        print(f"Warning: Metadata file not found at {file_path}")
        return [], [], np.array([])
    
    # Проверка наличия полей
    if not hasattr(loaded_data, 'GeoSelections') or not hasattr(loaded_data, 'Selections'):
        return [], [], np.array([])

    valid_indices = (loaded_data.GeoSelections != 'None') & \
                    (loaded_data.Selections != 'None')
    
    valid_geo = loaded_data.GeoSelections[valid_indices]
    valid_sel = loaded_data.Selections[valid_indices]
    
    geo_str = sorted(list(np.unique(valid_geo)))
    select_str = sorted(list(np.unique(valid_sel)))
    
    geo_map = {name: i for i, name in enumerate(geo_str)}
    sel_map = {name: i for i, name in enumerate(select_str)}
    
    coexistence_matrix = np.zeros((len(geo_str), len(select_str)), dtype=bool)
    
    for g, s in zip(valid_geo, valid_sel):
        if g in geo_map and s in sel_map:
            coexistence_matrix[geo_map[g], sel_map[s]] = True
            
    return geo_str, select_str, coexistence_matrix

def get_unique_stdbinnings(file_path=METADATA_FILE):
    """Портировано из getUniqueStdbinnings."""
    loaded_data = _load_mat_file(file_path)
    if loaded_data is None:
        return []
    
    if not hasattr(loaded_data, 'stdbinnings'):
        return []

    stdbinnings = loaded_data.stdbinnings
    non_empty = stdbinnings[stdbinnings != '']
    unique_binnings = sorted(list(np.unique(non_empty)))
    return unique_binnings

def load_binning_info(file_path=BINNING_INFO_FILE):
    """
    Загружает BinningInfo.mat и воссоздает структуры bininfo и bb.
    """
    print(f"Загрузка BinningInfo.mat из {file_path}...")
    bininfo_mat = _load_mat_file(file_path)
    if bininfo_mat is None:
        raise IOError(f"Критическая ошибка: BinningInfo.mat не найден по пути {file_path}")

    bininfo = {}
    bb = {}
    
    binnings = ['pitchbin', 'Lbin', 'Ebin']
    binningsdesc = ['pitchbdesc', 'Lbindesc', 'Ebindesc']

    # Извлекаем данные (в файле они лежат как поля объекта)
    for b, desc in zip(binnings, binningsdesc):
        if not hasattr(bininfo_mat, b):
            raise KeyError(f"Ключ '{b}' не найден в BinningInfo.mat")
        
        # Получаем данные
        bininfo[b] = getattr(bininfo_mat, b)
        bininfo[desc] = getattr(bininfo_mat, desc)

    # Добавляем Rig (конвертация)
    bininfo['Rig'] = []
    e_bins_data = bininfo['Ebin']
    
    # Обработка структуры (иногда это массив массивов)
    if isinstance(e_bins_data, np.ndarray) and e_bins_data.dtype == object:
        # Если это массив объектов (cell array в Matlab)
        iter_data = e_bins_data
    elif not isinstance(e_bins_data, (list, np.ndarray)):
        iter_data = [e_bins_data]
    else:
        iter_data = e_bins_data
        
    # Если это просто массив чисел (один биннинг), заворачиваем в список
    if isinstance(iter_data, np.ndarray) and iter_data.dtype != object and iter_data.ndim == 1:
        iter_data = [iter_data]

    temp_rig_list = []
    for e_bin_array in iter_data:
        e_arr = np.asarray(e_bin_array)
        M = 0.938 * np.ones_like(e_arr)
        Z = np.ones_like(e_arr)
        rig_array = kinematics.convert_T_to_R(e_arr, M, Z, Z)
        temp_rig_list.append(rig_array)
    bininfo['Rig'] = np.array(temp_rig_list, dtype=object)

    # Формируем структуру bb для GUI
    for i, b_name in enumerate(binnings):
        b_data = bininfo[b_name]
        b_desc = bininfo[binningsdesc[i]]
        
        # Нормализация входных данных в список массивов
        if isinstance(b_data, np.ndarray) and b_data.dtype == object:
            data_list = b_data
            desc_list = b_desc
        elif isinstance(b_data, np.ndarray) and b_data.ndim == 1:
             data_list = [b_data]
             desc_list = [b_desc] if not isinstance(b_desc, (list, np.ndarray)) else b_desc
        else:
             data_list = [b_data]
             desc_list = [b_desc]

        # Находим макс длину для паддинга
        max_len = 0
        for arr in data_list:
            if hasattr(arr, '__len__'): max_len = max(max_len, len(arr))
            else: max_len = max(max_len, 1)
        
        bb_list = []
        
        for j, arr in enumerate(data_list):
            # Описание
            if j < len(desc_list):
                desc_val = desc_list[j]
            else: 
                desc_val = "Unknown"
                
            arr = np.atleast_1d(arr)
            row_str = np.array(arr, dtype=str)
            
            padded_row = np.full(max_len + 1, '', dtype=object)
            padded_row[0] = desc_val
            padded_row[1:len(row_str)+1] = row_str
            bb_list.append(padded_row)
            
            # Для Ebin добавляем Rigidity
            if b_name == 'Ebin':
                rig_arr = np.atleast_1d(bininfo['Rig'][j])
                rig_row = np.array(rig_arr, dtype=str)
                padded_rig = np.full(max_len + 1, '', dtype=object)
                padded_rig[0] = 'Corresponding rigidities'
                padded_rig[1:len(rig_row)+1] = rig_row
                bb_list.append(padded_rig)
        
        bb[b_name] = np.array(bb_list, dtype=object)

    print("BinningInfo.mat загружен и обработан.")
    return bininfo, bb

# --- Динамические константы ---
print("Загрузка метаданных PAMELA (config.py)...")

# Пытаемся загрузить метаданные
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY = get_selection_coexistence()

# Если метаданные не загрузились (например, диск не подключен), ставим заглушки
if not BINNING_STR:
    BINNING_STR = ['P3L4E4'] 
if not GEO_STR:
    GEO_STR = ['RB3']
if not SELECT_STR:
    SELECT_STR = ['ItalianH']

# Загружаем биннинги
try:
    BIN_INFO, BB_INFO = load_binning_info()
except Exception as e:
    print(f"Критическая ошибка при загрузке биннингов: {e}")
    BIN_INFO, BB_INFO = {}, {}

print("Модуль config.py инициализирован.")
