"""
Модуль конфигурации (FINAL MERGED VERSION)
1. Lbin/Pitchbin загружаются через словарь (исправлено).
2. GS_ARRAY и метаданные восстановлены (исправлено).
3. Вернут helper _load_mat_file для совместимости с Binnings.py.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === ПУТИ ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

BINNING_INFO_FILE = os.path.join(DATA_DIR, 'BinningInfo.mat')
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

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ (Нужна для Binnings.py) ---
def _load_mat_file(path):
    if not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

# --- ЗАГРУЗКА БИННИНГОВ (Код, который сработал) ---
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

# --- ЗАГРУЗКА МЕТАДАННЫХ (Восстановлено для GS_ARRAY) ---
def load_metadata_safe():
    # Дефолтные значения
    geo_str = ['RB3']
    sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)

    if not os.path.exists(METADATA_FILE):
        return geo_str, sel_str, gs

    try:
        mat = loadmat(METADATA_FILE, squeeze_me=True, struct_as_record=False)
        
        # Проверяем наличие полей
        if not hasattr(mat, 'GeoSelections') or not hasattr(mat, 'Selections'):
            return geo_str, sel_str, gs

        # Фильтруем 'None' значения
        valid_mask = (mat.GeoSelections != 'None') & (mat.Selections != 'None')
        
        raw_geo = mat.GeoSelections[valid_mask]
        raw_sel = mat.Selections[valid_mask]
        
        geo_str = sorted(list(np.unique(raw_geo)))
        sel_str = sorted(list(np.unique(raw_sel)))
        
        # Строим матрицу связей
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

# === ИНИЦИАЛИЗАЦИЯ (Выполняется при импорте) ===
BIN_INFO = load_binning_info_direct()
GEO_STR, SELECT_STR, GS_ARRAY = load_metadata_safe()

# Если матрица пустая или 0-мерная, делаем заглушку
if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
