"""
Модуль конфигурации (CORE CONFIG STABLE)
Исправлено: возвращена полная длина массивов биннингов для исключения IndexError.
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

def _load_mat_file(path):
    if not path or not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

def get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key, None)
    return getattr(obj, key, None)

def calculate_bin_params(edges_array, mode='geometric'):
    """Расчет параметров бинов для всех строк массива."""
    if edges_array is None: return [], [], []
    if isinstance(edges_array, np.ndarray) and edges_array.dtype == 'O':
        centers, widths, counts = [], [], []
        for edges in edges_array:
            c, w, n = calculate_bin_params(edges, mode)
            centers.append(c); widths.append(w); counts.append(n)
        return np.array(centers, dtype='O'), np.array(widths, dtype='O'), np.array(counts, dtype='O')
    
    # Обработка одиночного массива
    edges = np.array(edges_array, dtype=float)
    if len(edges) < 2: return [], [], 0
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
        'dE': [], 'dR': [], 'dL': [], 'dPitch': []
    }
    mat = _load_mat_file(BINNING_INFO_FILE)
    if mat:
        bininfo['Lbin'] = get_val(mat, 'Lbin')
        bininfo['pitchbin'] = get_val(mat, 'pitchbin')
        
        # Загружаем ВСЕ 6 строк (не делим их здесь, чтобы не ломать индексы интерфейса)
        ebin_raw = get_val(mat, 'Ebin')
        bininfo['Ebin'] = ebin_raw
        bininfo['Rig'] = ebin_raw # В файле они в одном массиве Ebin

        # Считаем параметры для всех доступных строк
        bininfo['Ecenters'], bininfo['dE'], _ = calculate_bin_params(ebin_raw, 'geometric')
        bininfo['Rigcenters'], bininfo['dR'], _ = calculate_bin_params(ebin_raw, 'geometric')
        bininfo['Lcenters'], bininfo['dL'], _ = calculate_bin_params(bininfo['Lbin'], 'geometric')
        bininfo['pitchcenters'], bininfo['dPitch'], _ = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
    return bininfo

# === КОНСТАНТЫ GUI ===
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation','External exp. data','Empyrical models','Space weather data']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'L1sec','Lat1sec', 'Lon1sec']
TBIN_STR = ['passage','day','month','Separate Periods']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution','Radial distribution','Temporal variations','Variations along orbit','Fluxes Histogram']
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 

BIN_INFO = load_binning_info_direct()
GEO_STR = ['RB3', 'Polar8']; SELECT_STR = ['ItalianH', 'BasicCalo']
GS_ARRAY = np.ones((2, 2), dtype=bool); BINNING_STR = ['P3L4E4']
