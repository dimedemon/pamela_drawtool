"""
Модуль конфигурации (Фаза 1) - ОБНОВЛЕННЫЙ

Хранит константы, пути, загрузчики метаданных И БИННИНГОВ.
(Портировано из getGUIConstants.m и DrawTool3.m)
"""

import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics  # Импортируем наш новый модуль

# --- Константы (из DrawTool3.m) ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 # juliandate(datetime(2005,12,31))

# --- Пути ---
BASE_DATA_PATH = 'data' 
GEN_PATH = os.path.join(BASE_DATA_PATH, 'dirflux_newStructure')
METADATA_FILE = os.path.join(GEN_PATH, 'file_metadata.mat')
BINNING_INFO_FILE = os.path.join(BASE_DATA_PATH, 'BinningInfo.mat') # Путь к BinningInfo.mat

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
        print(f"ВНИМАНИЕ: Файл не найден по пути: {file_path}")
        return None
    try:
        # character_set='windows-1251' может понадобиться, если есть кириллица
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def get_selection_coexistence(file_path=METADATA_FILE):
    """Портировано из getSelectionCoexistence."""
    loaded_data = _load_mat_file(file_path)
    if loaded_data is None:
        return [], [], np.array([])
    
    # .mat файлы, загруженные с squeeze_me=True, ведут себя иначе
    valid_indices = (loaded_data['GeoSelections'] != 'None') & \
                    (loaded_data['Selections'] != 'None')
    
    valid_geo = loaded_data['GeoSelections'][valid_indices]
    valid_sel = loaded_data['Selections'][valid_indices]
    
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
    
    stdbinnings = loaded_data['stdbinnings']
    non_empty = stdbinnings[stdbinnings != '']
    unique_binnings = sorted(list(np.unique(non_empty)))
    return unique_binnings

def load_binning_info(file_path=BINNING_INFO_FILE):
    """
    Загружает BinningInfo.mat и воссоздает структуры bininfo и bb.
    (Портировано из setOptions в DrawTool3.m)
    """
    print(f"Загрузка BinningInfo.mat из {file_path}...")
    bininfo_mat = _load_mat_file(file_path)
    if bininfo_mat is None:
        raise IOError(f"Критическая ошибка: BinningInfo.mat не найден по пути {file_path}")

    bininfo = {}
    bb = {}
    
    binnings = ['pitchbin', 'Lbin', 'Ebin']
    binningsdesc = ['pitchbdesc', 'Lbindesc', 'Ebindesc']

    # bininfo (оригинальные данные из .mat)
    for b, desc in zip(binnings, binningsdesc):
        bininfo[b] = bininfo_mat['bininfo'].(b)
        bininfo[desc] = bininfo_mat['bininfo'].(desc)

    # Добавляем Rig (конвертация)
    bininfo['Rig'] = []
    for e_bin_array in bininfo['Ebin']:
        M = 0.938 * np.ones_like(e_bin_array)
        Z = np.ones_like(e_bin_array)
        rig_array = kinematics.convert_T_to_R(e_bin_array, M, Z, Z)
        bininfo['Rig'].append(rig_array)

    # bb (структура для GUI, как в MATLAB)
    for i, b_name in enumerate(binnings):
        b_data = bininfo[b_name]
        b_desc = bininfo[b_desc]
        max_len = max(len(arr) for arr in b_data)
        
        bb_list = []
        
        for j, arr in enumerate(b_data):
            desc = b_desc[j]
            # Создаем строки с padding из ''
            row_str = np.array(arr, dtype=str)
            padded_row = np.full(max_len + 1, '', dtype=object)
            padded_row[0] = desc
            padded_row[1:len(row_str)+1] = row_str
            bb_list.append(padded_row)
            
            if b_name == 'Ebin':
                # Добавляем строку с Жесткостью
                rig_row = np.array(bininfo['Rig'][j], dtype=str)
                padded_rig_row = np.full(max_len + 1, '', dtype=object)
                padded_rig_row[0] = 'Corresponding rigidities'
                padded_rig_row[1:len(rig_row)+1] = rig_row
                bb_list.append(padded_rig_row)
        
        bb[b_name] = np.array(bb_list)

    print("BinningInfo.mat загружен и обработан.")
    return bininfo, bb

# --- Динамические константы (загружаются при импорте) ---
print("Загрузка метаданных PAMELA (config.py)...")
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY = get_selection_coexistence()

# Загружаем биннинги
try:
    BIN_INFO, BB_INFO = load_binning_info()
except Exception as e:
    print(f"Критическая ошибка при загрузке биннингов: {e}")
    BIN_INFO, BB_INFO = None, None

print("Модуль config.py инициализирован.")
