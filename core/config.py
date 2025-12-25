"""
Модуль конфигурации (CLEAN FOLDER EDITION).
Работает строго внутри выделенной папки на внешнем диске.
Игнорирует мусор в корне диска.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === 1. НАСТРОЙКА ПУТЕЙ ===

# Корень диска
DRIVE_ROOT = "/Volumes/T7 Touch"

# Имя твоей новой чистой папки (ИЗМЕНИ, ЕСЛИ НАЗВАЛ ПО-ДРУГОМУ)
DATA_FOLDER_NAME = "PAMELA_DATA"

# Полный путь, где теперь лежат данные
DATA_DIR = os.path.join(DRIVE_ROOT, DATA_FOLDER_NAME)
BASE_DATA_PATH = DATA_DIR 

print(f"[CONFIG] Рабочая папка: {DATA_DIR}")

# === 2. ФУНКЦИИ ПОИСКА ===
def find_in_data(filename, subfolder=None):
    """
    Ищет файл строго внутри DATA_DIR.
    Проверяет корень папки и dirflux_newStructure.
    """
    if not os.path.exists(DATA_DIR):
        print(f"[CONFIG] ❌ ОШИБКА: Папка {DATA_DIR} не существует!")
        return None

    candidates = []
    
    # Формируем список мест для проверки
    if subfolder:
        # 1. В подпапке внутри структуры (самый частый вариант для матлаба)
        candidates.append(os.path.join(DATA_DIR, 'dirflux_newStructure', subfolder, filename))
        # 2. В подпапке просто в корне
        candidates.append(os.path.join(DATA_DIR, subfolder, filename))
    else:
        # 3. Просто в корне чистой папки
        candidates.append(os.path.join(DATA_DIR, filename))
        # 4. Внутри dirflux (в корне структуры)
        candidates.append(os.path.join(DATA_DIR, 'dirflux_newStructure', filename))
        # 5. Специфично для MagParam/Metadata - часто лежат в SolarHelioParams
        candidates.append(os.path.join(DATA_DIR, 'dirflux_newStructure', 'SolarHelioParams', filename))

    for path in candidates:
        if os.path.exists(path):
            return path
            
    # Если не нашли, возвращаем путь по умолчанию (первый кандидат), чтобы видеть ошибку
    return candidates[0]

# Находим ключевые файлы
BINNING_INFO_FILE = find_in_data('BinningInfo.mat')
METADATA_FILE = find_in_data('file_metadata.mat')
# Ищем MagParam (он может быть в корне или в SolarHelioParams)
MAGPARAM_FILE = find_in_data('MagParam2.mat')
if not MAGPARAM_FILE or not os.path.exists(MAGPARAM_FILE):
     MAGPARAM_FILE = find_in_data('MagParam2.mat', subfolder='SolarHelioParams')

print(f"[CONFIG] MagParam2: {MAGPARAM_FILE}")
print(f"[CONFIG] Metadata:  {METADATA_FILE}")

# === 3. ЗАГРУЗКА ДАННЫХ ===
def _load_mat_file(path):
    if not path or not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

def get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key, None)
    return getattr(obj, key, None)

def load_binning_info_direct():
    bininfo = { 'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [] }
    if not BINNING_INFO_FILE or not os.path.exists(BINNING_INFO_FILE): return bininfo
    try:
        mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        for k in ['Lbin', 'Lbindesc', 'pitchbin', 'pitchbdesc', 'Ebin', 'Ebindesc']:
            val = get_val(mat, k)
            if val is None: val = get_val(mat, k.lower()) or get_val(mat, k.capitalize()) or get_val(mat, k + 's')
            if val is not None: bininfo[k] = val
    except: pass
    try:
        ebins = bininfo.get('Ebin', [])
        if isinstance(ebins, np.ndarray) and ebins.size > 0:
            e = np.atleast_1d(ebins[0] if ebins.ndim > 1 else ebins)
            bininfo['Rig'] = np.sqrt(e**2 + 2*e*0.938)
    except: pass
    return bininfo

def get_unique_stdbinnings():
    default = ['P3L4E4']
    if not METADATA_FILE or not os.path.exists(METADATA_FILE): return default
    mat = _load_mat_file(METADATA_FILE)
    if mat is None: return default
    vals = get_val(mat, 'stdbinnings')
    if vals is not None:
        try:
            if isinstance(vals, (str, np.str_)): return [str(vals)]
            vals_flat = np.array(vals).flatten()
            valid = [str(v) for v in vals_flat if str(v).strip() != '']
            if valid: return sorted(list(set(valid)))
        except: pass
    return default

def load_metadata_full():
    geo_str = ['RB3']; sel_str = ['ItalianH']
    gs = np.ones((1,1), dtype=bool)
    file_info = {}

    # 1. Загрузка меню из metadata
    mat_meta = _load_mat_file(METADATA_FILE)
    if mat_meta:
        try:
            raw_geo = get_val(mat_meta, 'GeoSelections')
            raw_sel = get_val(mat_meta, 'Selections')
            if raw_geo is not None and raw_sel is not None:
                valid = (raw_geo != 'None') & (raw_sel != 'None')
                raw_geo = raw_geo[valid]; raw_sel = raw_sel[valid]
                geo_str = sorted(list(np.unique(raw_geo)))
                sel_str = sorted(list(np.unique(raw_sel)))
                geo_map = {k:v for v,k in enumerate(geo_str)}
                sel_map = {k:v for v,k in enumerate(sel_str)}
                gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
                for g, s in zip(raw_geo, raw_sel):
                    if g in geo_map and s in sel_map: gs[geo_map[g], sel_map[s]] = True
                if gs.ndim == 1: gs = gs.reshape(-1, 1)
        except: pass

    # 2. Загрузка ДНЕЙ из MagParam2 (Главный источник правды)
    if MAGPARAM_FILE and os.path.exists(MAGPARAM_FILE):
        mat_mag = _load_mat_file(MAGPARAM_FILE)
        if mat_mag:
            try:
                pamdays = get_val(mat_mag, 'pamdays')
                if pamdays is not None:
                    unique_days = np.unique(pamdays)
                    print(f"[CONFIG] ✅ Дни загружены из MagParam2: {len(unique_days)} шт.")
                    file_info['RunDays'] = unique_days
                    file_info['Days'] = unique_days
                    file_info['Completeness'] = np.ones(len(unique_days))
                    file_info['Date'] = np.zeros(len(unique_days))
            except: pass
    else:
        print("[CONFIG] ❌ MagParam2.mat не найден! Окно дней будет пустым.")

    return geo_str, sel_str, gs, file_info

# === 4. КОНСТАНТЫ ===
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation','External exp. data','Empyrical models','Space weather data']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'Blaz', 'Blzen', 'L1sec','Lat1sec', 'Lon1sec', 'Roll1sec', 'SPitch1sec', 'Yaw1sec','aTime', 'eqpitchlim', 'LocPitch', 'maxgyro', 'mingyro','TimeGap1sec', 'TimeGap2sec', 'trkMaskI1sec', 'trkMaskS1sec', 'Trig1sec']
GEN_X_STR = ['aTime', 'aTime', 'L1sec', 'BB01sec', 'Alt1sec', 'Lat1sec', 'Lon1sec']
WHAT_X_VARS = ['Date & time', 'time from entrance', 'L', 'B/B0', 'Altitude','latitude', 'longitude']
WHAT_Y_VARS = ['Altitude', 'Babs', 'B/B_0', 'Baz loc', 'Bzen loc', 'L', 'latitude','longitude', 'Roll', 'SPitch', 'Yaw', 'absolute time','maximum eqpitch', 'Local Pitch', 'maximum gyroangle','minimum gyroangle', 'TimeGap1', 'TimeGap2', 'TrkMaskI', 'TrkMaskS', 'Trigger']
UNIT_X_STR = ['m', 's', 'Re', '', 'km', '^{\circ}', '^{\circ}']
UNIT_STR = ['km', 'G', '', 'G', 'G', 'Re', '^{\circ}', '^{\circ}', '^{\circ}','^{\circ}', '^{\circ}', 's', '^{\circ}', '^{\circ}', '^{\circ}','^{\circ}', 's', 's', '', '', '' ]
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
DISTR_VARS = ['Flux','Number of events','Gathering power','livetime','Countrate','Relative error of flux','Four entities at once']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution','Radial distribution','Temporal variations','Variations along orbit','Fluxes Histogram','L-pitch map','E-pitch map','E-L map','Auxiliary parameters']
SP_WEATHER_STR = ['f10p7','SSN','Dst','Kp','Ap']

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY, FILE_INFO = load_metadata_full()

if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
