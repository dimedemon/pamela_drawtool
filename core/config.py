"""
Модуль конфигурации (FULL PROTOCOL STABLE)
Исправлено: восстановлены все константы GUI и метод _load_mat_file.
Реализовано: разделение Ebin на Energy и Rigidity согласно протоколу.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime

# === ПУТИ ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
UI_DATA_PATH = os.path.join(PROJECT_ROOT, 'data')

ext_root = "/Volumes/T7 Touch"
ext_clean = os.path.join(ext_root, "PAMELA_DATA")
BASE_DATA_PATH = ext_clean if os.path.exists(ext_clean) else ext_root

BINNING_INFO_FILE = os.path.join(UI_DATA_PATH, 'BinningInfo.mat')
METADATA_FILE = os.path.join(UI_DATA_PATH, 'file_metadata.mat')

# === СЛУЖЕБНЫЕ ФУНКЦИИ ===
def _load_mat_file(path):
    """Необходим для Binnings.py и других виджетов."""
    if not path or not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

def get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key, None)
    return getattr(obj, key, None)

def calculate_bin_params(edges_array, mode='geometric'):
    if edges_array is None or len(edges_array) == 0: return [], [], 0
    if isinstance(edges_array, np.ndarray) and edges_array.dtype == 'O':
        centers, widths, counts = [], [], []
        for edges in edges_array:
            c, w, n = calculate_bin_params(edges, mode)
            centers.append(c); widths.append(w); counts.append(n)
        return np.array(centers, dtype='O'), np.array(widths, dtype='O'), np.array(counts, dtype='O')
    
    edges = np.array(edges_array, dtype=float)
    w = edges[1:] - edges[:-1]
    if mode == 'geometric':
        valid = edges.copy(); valid[valid <= 0] = 1e-9
        c = np.sqrt(valid[:-1] * valid[1:])
    else:
        c = (edges[:-1] + edges[1:]) / 2.0
    return c, w, len(c)

def load_binning_info_direct():
    bininfo = { 
        'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [],
        'Ecenters': [], 'Rigcenters': [], 'Lcenters': [], 'pitchcenters': [],
        'dE': [], 'dR': [], 'dL': [], 'dPitch': [],
        'nE': [], 'nR': [], 'nL': [], 'nPitch': []
    }
    mat = _load_mat_file(BINNING_INFO_FILE)
    if mat:
        bininfo['Lbin'] = get_val(mat, 'Lbin')
        bininfo['pitchbin'] = get_val(mat, 'pitchbin')
        
        # Разделение E и R (нечётные - E, чётные - R)
        ebin_raw = get_val(mat, 'Ebin')
        if ebin_raw is not None and isinstance(ebin_raw, np.ndarray) and ebin_raw.dtype == 'O':
            bininfo['Ebin'] = ebin_raw[0::2] # 0, 2, 4... (Energy)
            bininfo['Rig'] = ebin_raw[1::2]  # 1, 3, 5... (Rigidity)
        else:
            bininfo['Ebin'] = bininfo['Rig'] = ebin_raw

        bininfo['Ecenters'], bininfo['dE'], bininfo['nE'] = calculate_bin_params(bininfo['Ebin'], 'geometric')
        bininfo['Rigcenters'], bininfo['dR'], bininfo['nR'] = calculate_bin_params(bininfo['Rig'], 'geometric')
        bininfo['Lcenters'], bininfo['dL'], bininfo['nL'] = calculate_bin_params(bininfo['Lbin'], 'geometric')
        bininfo['pitchcenters'], bininfo['dPitch'], bininfo['nPitch'] = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
    return bininfo

# === КОНСТАНТЫ ИНТЕРФЕЙСА ===
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation','External exp. data','Empyrical models','Space weather data']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'L1sec','Lat1sec', 'Lon1sec']
TBIN_STR = ['passage','day','month','Separate Periods']
DISTR_VARS = ['Flux','Number of events','Gathering power','livetime','Countrate','Relative error of flux']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution','Radial distribution','Temporal variations','Variations along orbit','Fluxes Histogram']
UNIT_STR = ['km', 'G', '', 'G', 'G', 'Re', '°', '°', '°','°', '°', 's']
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
GEO_STR = ['RB3', 'Polar8']
SELECT_STR = ['ItalianH', 'BasicCalo']
GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
BINNING_STR = ['P3L4E4']
