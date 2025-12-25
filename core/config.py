"""
Модуль конфигурации (DAYS & COLORS RESTORED).
1. Пути настроены на T7 Touch.
2. Восстановлена загрузка информации о ДНЯХ (Completeness, RunDays) для раскраски окна.
3. Восстановлены все текстовые константы.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === 1. ПУТИ (Ваш внешний диск) ===
DATA_DIR = "/Volumes/T7 Touch"
BASE_DATA_PATH = DATA_DIR 

print(f"[CONFIG] Корень данных: {DATA_DIR}")

# Умный поиск файлов
def find_file(filename):
    path_struct = os.path.join(DATA_DIR, 'dirflux_newStructure', filename)
    if os.path.exists(path_struct): return path_struct
    path_root = os.path.join(DATA_DIR, filename)
    return path_root

BINNING_INFO_FILE = find_file('BinningInfo.mat')
METADATA_FILE = find_file('file_metadata.mat')

print(f"[CONFIG] Metadata: {METADATA_FILE}")

# === 2. КОНСТАНТЫ ИНТЕРФЕЙСА ===
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation',
                   'External exp. data','Empyrical models','Space weather data']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'Blaz', 'Blzen', 'L1sec',
    'Lat1sec', 'Lon1sec', 'Roll1sec', 'SPitch1sec', 'Yaw1sec',
    'aTime', 'eqpitchlim', 'LocPitch', 'maxgyro', 'mingyro',
    'TimeGap1sec', 'TimeGap2sec', 'trkMaskI1sec', 'trkMaskS1sec', 'Trig1sec']
GEN_X_STR = ['aTime', 'aTime', 'L1sec', 'BB01sec', 'Alt1sec', 'Lat1sec', 'Lon1sec']
WHAT_X_VARS = ['Date & time', 'time from entrance', 'L', 'B/B0', 'Altitude',
    'latitude', 'longitude']
WHAT_Y_VARS = ['Altitude', 'Babs', 'B/B_0', 'Baz loc', 'Bzen loc', 'L', 'latitude',
    'longitude', 'Roll', 'SPitch', 'Yaw', 'absolute time',
    'maximum eqpitch', 'Local Pitch', 'maximum gyroangle',
    'minimum gyroangle', 'TimeGap1', 'TimeGap2', 'TrkMaskI', 'TrkMaskS', 'Trigger']
UNIT_X_STR = ['m', 's', 'Re', '', 'km', '^{\circ}', '^{\circ}']
UNIT_STR = ['km', 'G', '', 'G', 'G', 'Re', '^{\circ}', '^{\circ}', '^{\circ}',
    '^{\circ}', '^{\circ}', 's', '^{\circ}', '^{\circ}', '^{\circ}',
    '^{\circ}', 's', 's', '', '', '' ]
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
DISTR_VARS = ['Flux','Number of events','Gathering power','livetime',
              'Countrate','Relative error of flux','Four entities at once']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution',
              'Radial distribution','Temporal variations','Variations along orbit',
              'Fluxes Histogram','L-pitch map','E-pitch map','E-L map',
              'Auxiliary parameters']
SP_WEATHER_STR = ['f10p7','SSN','Dst','Kp','Ap']

# === 3. ЗАГРУЗКА ДАННЫХ ===
def _load_mat_file(path):
    if not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

# Загрузка Биннингов
def load_binning_info_direct():
    bininfo = { 'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [] }
    if not os.path.exists(BINNING_INFO_FILE): return bininfo
    try:
        mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        for k in ['Lbin', 'Lbindesc', 'pitchbin', 'pitchbdesc', 'Ebin', 'Ebindesc']:
            keys = [k, k.lower(), k.capitalize(), k + 's'] 
            for key in keys:
                if key in mat:
                    bininfo[k] = mat[key]
                    break
    except: pass
    try:
        ebins = bininfo.get('Ebin', [])
        if isinstance(ebins, np.ndarray) and ebins.size > 0:
            e = np.atleast_1d(ebins[0] if ebins.ndim > 1 else ebins)
            bininfo['Rig'] = np.sqrt(e**2 + 2*e*0.938)
    except: pass
    return bininfo

# Загрузка списка биннингов
def get_unique_stdbinnings():
    default = ['P3L4E4']
    mat = _load_mat_file(METADATA_FILE)
    if mat is None: return default
    if hasattr(mat, 'stdbinnings'):
        try:
            vals = mat.stdbinnings
            if isinstance(vals, (str, np.str_)): return [str(vals)]
            valid = vals[vals != '']
            return sorted(list(np.unique(valid)))
        except: return default
    return default

# --- ГЛАВНАЯ ФУНКЦИЯ ДЛЯ МЕТАДАННЫХ (ИСПРАВЛЕНА) ---
def load_metadata_full():
    """
    Загружает не только GeoSelections, но и информацию о Днях (Completeness),
    чтобы окно дней могло их раскрасить.
    """
    # 1. Значения по умолчанию
    geo_str = ['RB3']; sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)
    
    # Словарь для хранения информации о днях (Completeness, Dates и т.д.)
    file_info = {}

    mat = _load_mat_file(METADATA_FILE)
    if mat is None: 
        return geo_str, sel_str, gs, file_info

    try:
        # А. Загрузка GeoSelections (для меню)
        if hasattr(mat, 'GeoSelections') and hasattr(mat, 'Selections'):
            valid = (mat.GeoSelections != 'None') & (mat.Selections != 'None')
            raw_geo = mat.GeoSelections[valid]
            raw_sel = mat.Selections[valid]
            geo_str = sorted(list(np.unique(raw_geo)))
            sel_str = sorted(list(np.unique(raw_sel)))
            
            geo_map = {k:v for v,k in enumerate(geo_str)}
            sel_map = {k:v for v,k in enumerate(sel_str)}
            gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
            for g, s in zip(raw_geo, raw_sel):
                if g in geo_map and s in sel_map: gs[geo_map[g], sel_map[s]] = True
            if gs.ndim == 1: gs = gs.reshape(-1, 1)

        # Б. Загрузка информации о днях (ДЛЯ ОКНА ДНЕЙ!)
        # Проверяем наличие ключевых полей и сохраняем их
        keys_to_save = ['RunDays', 'Days', 'Date', 'Completeness', 'Duration', 'nEvents']
        for k in keys_to_save:
            if hasattr(mat, k):
                file_info[k] = getattr(mat, k)
            elif k in mat.__dict__: # Если это словарь
                file_info[k] = mat.__dict__[k]

        print(f"[CONFIG] Загружена информация о днях. Ключи: {list(file_info.keys())}")

    except Exception as e:
        print(f"[CONFIG] Ошибка загрузки метаданных: {e}")
        
    return geo_str, sel_str, gs, file_info

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
BINNING_STR = get_unique_stdbinnings()

# Теперь мы получаем 4 значения
GEO_STR, SELECT_STR, GS_ARRAY, FILE_INFO = load_metadata_full()

if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
