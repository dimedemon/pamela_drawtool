"""
Модуль конфигурации (FIXED PATHS & METADATA).
Ищет metadata и binninginfo и в корне, и в dirflux_newStructure.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === 1. ПУТЬ К ДАННЫМ ===
# Указываем корень вашего диска
DATA_DIR = "/Volumes/T7 Touch"

# Алиас для file_manager
BASE_DATA_PATH = DATA_DIR 

print(f"[CONFIG] Корень данных: {DATA_DIR}")

# === 2. УМНЫЙ ПОИСК ФАЙЛОВ ===
def find_file(filename):
    """Ищет файл в корне DATA_DIR или в подпапке dirflux_newStructure"""
    # Вариант 1: Внутри структуры (наиболее вероятно для metadata)
    path_struct = os.path.join(DATA_DIR, 'dirflux_newStructure', filename)
    if os.path.exists(path_struct):
        return path_struct
    
    # Вариант 2: В корне (наиболее вероятно для BinningInfo, судя по логам)
    path_root = os.path.join(DATA_DIR, filename)
    if os.path.exists(path_root):
        return path_root
        
    return path_root # Возвращаем дефолт, даже если нет

# Определяем пути автоматически
BINNING_INFO_FILE = find_file('BinningInfo.mat')
METADATA_FILE = find_file('file_metadata.mat')

print(f"[CONFIG] BinningInfo: {BINNING_INFO_FILE}")
print(f"[CONFIG] Metadata:    {METADATA_FILE}")

# --- Константы ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation',
                   'External exp. data','Empyrical models','Space weather data']
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution',
              'Radial distribution','Temporal variations','Variations along orbit',
              'Fluxes Histogram','L-pitch map','E-pitch map','E-L map','Auxiliary parameters']

# --- Helper ---
def _load_mat_file(path):
    if not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

# --- ЗАГРУЗКА БИННИНГОВ ---
def load_binning_info_direct():
    bininfo = { 'Lbin': [], 'Lbindesc': [], 'pitchbin': [], 'pitchbdesc': [], 
                'Ebin': [], 'Ebindesc': [], 'Rig': [] }
    
    if not os.path.exists(BINNING_INFO_FILE):
        print(f"[CONFIG] ❌ BinningInfo не найден!")
        return bininfo

    try:
        mat_dict = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        
        # Перенос данных
        if 'Lbin' in mat_dict: bininfo['Lbin'] = mat_dict['Lbin']
        elif 'Lbins' in mat_dict: bininfo['Lbin'] = mat_dict['Lbins']
        
        if 'pitchbin' in mat_dict: bininfo['pitchbin'] = mat_dict['pitchbin']
        elif 'PitchBin' in mat_dict: bininfo['pitchbin'] = mat_dict['PitchBin']
            
        if 'Ebin' in mat_dict: bininfo['Ebin'] = mat_dict['Ebin']

        if 'Lbindesc' in mat_dict: bininfo['Lbindesc'] = mat_dict['Lbindesc']
        if 'pitchbdesc' in mat_dict: bininfo['pitchbdesc'] = mat_dict['pitchbdesc']
        if 'Ebindesc' in mat_dict: bininfo['Ebindesc'] = mat_dict['Ebindesc']
        
    except Exception as e:
        print(f"[CONFIG] Ошибка чтения BinningInfo: {e}")

    # Rigidity
    try:
        ebins = bininfo['Ebin']
        if not isinstance(ebins, (list, np.ndarray)) or (isinstance(ebins, np.ndarray) and ebins.dtype != object):
             ebins = [ebins]
        rig_list = []
        for e in ebins:
            if np.ndim(e) == 0: continue
            e = np.atleast_1d(e)
            rig_list.append(np.sqrt(e**2 + 2*e*0.938))
        bininfo['Rig'] = np.array(rig_list, dtype=object)
    except Exception as e: pass

    return bininfo

# --- СПИСОК БИННИНГОВ ---
def get_unique_stdbinnings():
    default = ['P3L4E4']
    mat = _load_mat_file(METADATA_FILE) # Теперь ищет по правильному пути
    if mat is None: return default
    if hasattr(mat, 'stdbinnings'):
        try:
            vals = mat.stdbinnings
            if isinstance(vals, (str, np.str_)): return [str(vals)]
            valid = vals[vals != '']
            return sorted(list(np.unique(valid)))
        except: return default
    return default

# --- МЕТАДАННЫЕ (GEO/SELECTION) ---
def load_metadata_safe():
    geo_str = ['RB3']; sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)

    mat = _load_mat_file(METADATA_FILE) # Теперь ищет по правильному пути
    
    if mat is None:
        print(f"[CONFIG] ❌ Metadata не найден по пути: {METADATA_FILE}")
        return geo_str, sel_str, gs

    try:
        print("[CONFIG] ✅ Metadata успешно загружен.")
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

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY = load_metadata_safe()

if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
