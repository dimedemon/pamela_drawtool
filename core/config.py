"""
Модуль конфигурации (FINAL FIXED).
1. Исправлена ошибка 'dict object has no attribute __dict__'.
2. Метаданные загружаются корректно для раскраски дней.
3. Пути настроены на внешний диск.
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
    # Сначала ищем в структуре
    path_struct = os.path.join(DATA_DIR, 'dirflux_newStructure', filename)
    if os.path.exists(path_struct): return path_struct
    # Потом в корне
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

# Helper для извлечения данных из словаря или объекта
def get_val(obj, key):
    if isinstance(obj, dict):
        return obj.get(key, None)
    return getattr(obj, key, None)

# Загрузка Биннингов
def load_binning_info_direct():
    bininfo = { 'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [] }
    if not os.path.exists(BINNING_INFO_FILE): return bininfo
    try:
        mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        for k in ['Lbin', 'Lbindesc', 'pitchbin', 'pitchbdesc', 'Ebin', 'Ebindesc']:
            # Пробуем достать ключ любым способом
            val = get_val(mat, k)
            if val is None: # Пробуем разные регистры
                val = get_val(mat, k.lower()) or get_val(mat, k.capitalize()) or get_val(mat, k + 's')
            
            if val is not None:
                bininfo[k] = val
    except: pass
    
    # Rigidity
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
    
    vals = get_val(mat, 'stdbinnings')
    if vals is not None:
        try:
            if isinstance(vals, (str, np.str_)): return [str(vals)]
            valid = vals[vals != '']
            return sorted(list(np.unique(valid)))
        except: return default
    return default

# --- ЗАГРУЗКА МЕТАДАННЫХ (ИСПРАВЛЕННАЯ) ---
def load_metadata_full():
    """
    Загружает GeoSelections и информацию о днях.
    Работает корректно и со словарями, и с объектами.
    """
    geo_str = ['RB3']; sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)
    file_info = {}

    mat = _load_mat_file(METADATA_FILE)
    if mat is None: 
        return geo_str, sel_str, gs, file_info

    try:
        # А. Загрузка GeoSelections
        raw_geo = get_val(mat, 'GeoSelections')
        raw_sel = get_val(mat, 'Selections')

        if raw_geo is not None and raw_sel is not None:
            valid = (raw_geo != 'None') & (raw_sel != 'None')
            raw_geo = raw_geo[valid]
            raw_sel = raw_sel[valid]
            
            geo_str = sorted(list(np.unique(raw_geo)))
            sel_str = sorted(list(np.unique(raw_sel)))
            
            geo_map = {k:v for v,k in enumerate(geo_str)}
            sel_map = {k:v for v,k in enumerate(sel_str)}
            gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
            for g, s in zip(raw_geo, raw_sel):
                if g in geo_map and s in sel_map: gs[geo_map[g], sel_map[s]] = True
            if gs.ndim == 1: gs = gs.reshape(-1, 1)

        # Б. Загрузка информации о днях (ДЛЯ ОКНА ДНЕЙ!)
        keys_to_save = ['RunDays', 'Days', 'Date', 'Completeness', 'Duration', 'nEvents']
        for k in keys_to_save:
            val = get_val(mat, k)
            if val is not None:
                file_info[k] = val
        
        # Диагностика
        if 'Completeness' in file_info:
            print(f"[CONFIG] ✅ Данные о днях загружены. Completeness size: {len(file_info['Completeness'])}")
        else:
            print(f"[CONFIG] ⚠️ Данные о днях (Completeness) не найдены в файле.")

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
