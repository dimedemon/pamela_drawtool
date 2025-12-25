"""
Модуль конфигурации (COMPLETE RESTORED VERSION)
Содержит все необходимые переменные: BIN_INFO, GS_ARRAY, BINNING_STR.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === ПУТИ ===
# Указываем путь к вашему внешнему диску
DATA_DIR = "/Volumes/T7 Touch"

# !!! ВАЖНО: Алиас для совместимости
BASE_DATA_PATH = DATA_DIR 

# BinningInfo скорее всего лежит внутри dirflux_newStructure или в корне. 
# Если он в корне T7 Touch, оставляем так:
BINNING_INFO_FILE = os.path.join(DATA_DIR, 'BinningInfo.mat')
# Если он внутри папки структуры, раскомментируйте эту строку:
# BINNING_INFO_FILE = os.path.join(DATA_DIR, 'dirflux_newStructure', 'BinningInfo.mat')

METADATA_FILE = os.path.join(DATA_DIR, 'file_metadata.mat')

print(f"[CONFIG] Путь к данным: {DATA_DIR}")

# --- Константы ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation',
                   'External exp. data','Empyrical models','Space weather data']
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution',
              'Radial distribution','Temporal variations','Variations along orbit',
              'Fluxes Histogram','L-pitch map','E-pitch map','E-L map','Auxiliary parameters']

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---
def _load_mat_file(path):
    if not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

# --- 1. ЗАГРУЗКА БИННИНГОВ (BIN_INFO) ---
def load_binning_info_direct():
    bininfo = {
        'Lbin': [], 'Lbindesc': [],
        'pitchbin': [], 'pitchbdesc': [],
        'Ebin': [], 'Ebindesc': [],
        'Rig': []
    }
    
    if not os.path.exists(BINNING_INFO_FILE):
        print(f"[CONFIG] ОШИБКА: Файл не найден: {BINNING_INFO_FILE}")
        return bininfo

    try:
        print(f"[CONFIG] Загрузка {BINNING_INFO_FILE}...")
        mat_dict = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        
        # 1. Lbin
        if 'Lbin' in mat_dict: bininfo['Lbin'] = mat_dict['Lbin']
        elif 'Lbins' in mat_dict: bininfo['Lbin'] = mat_dict['Lbins']
        
        # 2. pitchbin
        if 'pitchbin' in mat_dict: bininfo['pitchbin'] = mat_dict['pitchbin']
        elif 'PitchBin' in mat_dict: bininfo['pitchbin'] = mat_dict['PitchBin']
            
        # 3. Ebin
        if 'Ebin' in mat_dict: bininfo['Ebin'] = mat_dict['Ebin']

        # 4. Описания
        if 'Lbindesc' in mat_dict: bininfo['Lbindesc'] = mat_dict['Lbindesc']
        if 'pitchbdesc' in mat_dict: bininfo['pitchbdesc'] = mat_dict['pitchbdesc']
        if 'Ebindesc' in mat_dict: bininfo['Ebindesc'] = mat_dict['Ebindesc']
        
        print(f"[CONFIG] Lbin загружен. Размер: {len(bininfo['Lbin']) if hasattr(bininfo['Lbin'], '__len__') else 'Error'}")

    except Exception as e:
        print(f"[CONFIG] Ошибка чтения BinningInfo: {e}")

    # Расчет жесткости
    try:
        ebins = bininfo['Ebin']
        if not isinstance(ebins, (list, np.ndarray)) or (isinstance(ebins, np.ndarray) and ebins.dtype != object):
             ebins = [ebins]
        
        rig_list = []
        for e in ebins:
            if np.ndim(e) == 0: continue
            e = np.atleast_1d(e)
            m = 0.938
            R = np.sqrt(e**2 + 2*e*m)
            rig_list.append(R)
        bininfo['Rig'] = np.array(rig_list, dtype=object)
    except Exception as e:
        print(f"[CONFIG] Ошибка расчета Rigidity: {e}")

    return bininfo

# --- 2. ЗАГРУЗКА СПИСКА БИННИНГОВ (BINNING_STR) ---
def get_unique_stdbinnings():
    """Возвращает список доступных биннингов (например, ['P3L4E4'])."""
    default = ['P3L4E4']
    
    mat = _load_mat_file(METADATA_FILE)
    if mat is None:
        return default
        
    if hasattr(mat, 'stdbinnings'):
        try:
            vals = mat.stdbinnings
            # Если там всего одна строка
            if isinstance(vals, (str, np.str_)): 
                return [str(vals)]
            # Если массив строк
            valid = vals[vals != '']
            return sorted(list(np.unique(valid)))
        except:
            return default
            
    return default

# --- 3. ЗАГРУЗКА МЕТАДАННЫХ (GS_ARRAY, GEO_STR) ---
def load_metadata_safe():
    geo_str = ['RB3']
    sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)

    mat = _load_mat_file(METADATA_FILE)
    if mat is None:
        return geo_str, sel_str, gs

    try:
        if not hasattr(mat, 'GeoSelections') or not hasattr(mat, 'Selections'):
            return geo_str, sel_str, gs

        valid_mask = (mat.GeoSelections != 'None') & (mat.Selections != 'None')
        raw_geo = mat.GeoSelections[valid_mask]
        raw_sel = mat.Selections[valid_mask]
        
        geo_str = sorted(list(np.unique(raw_geo)))
        sel_str = sorted(list(np.unique(raw_sel)))
        
        geo_map = {k:v for v,k in enumerate(geo_str)}
        sel_map = {k:v for v,k in enumerate(sel_str)}
        
        gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
        for g, s in zip(raw_geo, raw_sel):
            if g in geo_map and s in sel_map:
                gs[geo_map[g], sel_map[s]] = True
        
        if gs.ndim == 1: gs = gs.reshape(-1, 1)
        
    except Exception as e:
        print(f"[CONFIG] Ошибка метаданных: {e}")
        
    return geo_str, sel_str, gs

# === ИНИЦИАЛИЗАЦИЯ (ВЫПОЛНЯЕТСЯ ПРИ ИМПОРТЕ) ===
# 1. Основные данные
BIN_INFO = load_binning_info_direct()

# 2. Список доступных биннингов (ВОССТАНОВЛЕНО)
BINNING_STR = get_unique_stdbinnings()

# 3. Метаданные селекции
GEO_STR, SELECT_STR, GS_ARRAY = load_metadata_safe()

# Заглушка, если метаданные не загрузились
if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
