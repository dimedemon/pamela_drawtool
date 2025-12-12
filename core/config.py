"""
Модуль конфигурации (Фаза 5 - FINAL RESTORED)
Исправлено:
1. Вернуты потерянные константы (DATA_SOURCE_STR и др).
2. METADATA_FILE теперь ищется и в корне data, и в data/dirflux_newStructure.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === ПУТИ ===
# Абсолютный путь к папке data внутри проекта
BASE_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# Путь к BinningInfo.mat (всегда в корне data)
BINNING_INFO_FILE = os.path.join(BASE_DATA_PATH, 'BinningInfo.mat')

# Путь к метаданным (умный поиск)
_meta_root = os.path.join(BASE_DATA_PATH, 'file_metadata.mat')
_meta_sub = os.path.join(BASE_DATA_PATH, 'dirflux_newStructure', 'file_metadata.mat')

if os.path.exists(_meta_root):
    METADATA_FILE = _meta_root
elif os.path.exists(_meta_sub):
    METADATA_FILE = _meta_sub
else:
    METADATA_FILE = _meta_root # Дефолт, даже если нет

# --- Константы ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

# --- СПИСКИ ДЛЯ ИНТЕРФЕЙСА (Вернул на место!) ---
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation',
                   'Anisotropic flux simulation','External exp. data',
                   'Empyrical models','Space weather data']

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


# --- Загрузчик ---
def _load_mat_file(path):
    if not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

# --- Метаданные (Selection/Geo) ---
def get_selection_coexistence(file_path=METADATA_FILE):
    # Дефолтные значения
    def_geo = ['RB3']; def_sel = ['ItalianH']; def_gs = np.ones((1,1), dtype=bool)
    
    mat = _load_mat_file(file_path)
    if mat is None or not hasattr(mat, 'GeoSelections'):
        return def_geo, def_sel, def_gs

    try:
        valid = (mat.GeoSelections != 'None') & (mat.Selections != 'None')
        geo_str = sorted(list(np.unique(mat.GeoSelections[valid])))
        sel_str = sorted(list(np.unique(mat.Selections[valid])))
        
        geo_map = {k:v for v,k in enumerate(geo_str)}
        sel_map = {k:v for v,k in enumerate(sel_str)}
        
        gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
        for g, s in zip(mat.GeoSelections[valid], mat.Selections[valid]):
            if g in geo_map and s in sel_map: gs[geo_map[g], sel_map[s]] = True
            
        if gs.ndim == 1: gs = gs.reshape(-1, 1)
        return geo_str, sel_str, gs
    except: return def_geo, def_sel, def_gs

def get_unique_stdbinnings(file_path=METADATA_FILE):
    mat = _load_mat_file(file_path)
    if mat and hasattr(mat, 'stdbinnings'):
        return sorted(list(np.unique(mat.stdbinnings[mat.stdbinnings != ''])))
    return ['P3L4E4']

# --- Биннинги ---
def load_binning_info(file_path=BINNING_INFO_FILE):
    print(f"Loading BinningInfo from {file_path}...")
    mat = _load_mat_file(file_path)
    
    if mat is None:
        print("Warning: BinningInfo.mat not found. Using dummy data.")
        keys = ['pitchbin', 'Lbin', 'Ebin']
        bininfo = {'pitchbin': [np.array([0, 90])], 'Lbin': [np.array([1.0, 1.2])], 'Ebin': [np.array([0.1, 1.0])], 'Rig': [np.array([0.1, 1.0])]}
        bb = {k: np.array([['Desc', 'Val']]) for k in keys}
        return bininfo, bb

    src = mat
    if not hasattr(mat, 'pitchbin'):
        for key in dir(mat):
            if key.startswith('_'): continue
            attr = getattr(mat, key)
            if hasattr(attr, 'pitchbin'):
                src = attr
                break
    
    bininfo = {}; bb = {}
    keys = ['pitchbin', 'Lbin', 'Ebin']
    descs = ['pitchbdesc', 'Lbindesc', 'Ebindesc']
    
    for k, d in zip(keys, descs):
        if not hasattr(src, k): continue 
        bininfo[k] = getattr(src, k)
        bininfo[d] = getattr(src, d)

    bininfo['Rig'] = []
    ebins = bininfo['Ebin'] if isinstance(bininfo['Ebin'], np.ndarray) and bininfo['Ebin'].dtype==object else [bininfo['Ebin']]
    for e in ebins:
        e = np.atleast_1d(e)
        bininfo['Rig'].append(kinematics.convert_T_to_R(e, 0.938*np.ones_like(e), np.ones_like(e), np.ones_like(e)))
    bininfo['Rig'] = np.array(bininfo['Rig'], dtype=object)

    for i, name in enumerate(keys):
        data = bininfo[name]
        desc = bininfo[descs[i]]
        if not (isinstance(data, np.ndarray) and data.dtype==object): data = [data]; desc = [desc]
        
        bb_list = []
        max_len = max(len(np.atleast_1d(arr)) for arr in data)
        for j, arr in enumerate(data):
            row = np.full(max_len+1, '', dtype=object)
            row[0] = desc[j] if j < len(desc) else "?"
            vals = np.atleast_1d(arr).astype(str)
            row[1:len(vals)+1] = vals
            bb_list.append(row)
        bb[name] = np.array(bb_list, dtype=object)

    return bininfo, bb

# --- INIT ---
print("Config: Initializing...")
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY = get_selection_coexistence()
if GS_ARRAY.ndim != 2: GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)

try: BIN_INFO, BB_INFO = load_binning_info()
except: BIN_INFO, BB_INFO = {}, {}

print("Config: Initialized.")
