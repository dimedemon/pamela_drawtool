"""
Модуль конфигурации (FULL PROTOCOL)
Восстановлены все константы для GUI и расчет точной геометрии бинов.
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

print(f"[CONFIG] UI файлы: {UI_DATA_PATH}")
print(f"[CONFIG] Данные:   {BASE_DATA_PATH}")

BINNING_INFO_FILE = os.path.join(UI_DATA_PATH, 'BinningInfo.mat')
METADATA_FILE = os.path.join(UI_DATA_PATH, 'file_metadata.mat')

# === ФУНКЦИИ ЗАГРУЗКИ И РАСЧЕТА ===
def _load_mat_file(path):
    if not path or not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

def get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key, None)
    return getattr(obj, key, None)

def calculate_bin_params(edges_array, mode='geometric'):
    """Вычисляет центры и ширину бинов для отрисовки."""
    if edges_array is None: return [], [], []
    if isinstance(edges_array, np.ndarray) and edges_array.dtype == 'O':
        centers, widths, counts = [], [], []
        for edges in edges_array:
            c, w, n = calculate_bin_params(edges, mode)
            centers.append(c); widths.append(w); counts.append(n)
        return np.array(centers, dtype='O'), np.array(widths, dtype='O'), np.array(counts, dtype='O')
    
    if isinstance(edges_array, (np.ndarray, list)) and len(edges_array) > 1:
        w = edges_array[1:] - edges_array[:-1]
        if mode == 'geometric':
            valid = np.array(edges_array, dtype=float)
            valid[valid <= 0] = 1e-9
            c = np.sqrt(valid[:-1] * valid[1:])
        else:
            c = (edges_array[:-1] + edges_array[1:]) / 2.0
        return c, w, len(c)
    return [], [], 0

def load_binning_info_direct():
    bininfo = { 
        'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [],
        'Ecenters': [], 'Rigcenters': [], 'Lcenters': [], 'pitchcenters': [],
        'dE': [], 'dR': [], 'dL': [], 'dPitch': [],
        'nE': [], 'nR': [], 'nL': [], 'nPitch': []
    }
    mat = _load_mat_file(BINNING_INFO_FILE)
    if mat:
        for k in ['Lbin', 'pitchbin', 'Ebin', 'Rig']:
            val = get_val(mat, k)
            if val is None: val = get_val(mat, k.lower())
            if val is not None: bininfo[k] = val
        bininfo['Ecenters'], bininfo['dE'], bininfo['nE'] = calculate_bin_params(bininfo['Ebin'], 'geometric')
        bininfo['Rigcenters'], bininfo['dR'], bininfo['nR'] = calculate_bin_params(bininfo['Rig'], 'geometric')
        bininfo['Lcenters'], bininfo['dL'], bininfo['nL'] = calculate_bin_params(bininfo['Lbin'], 'geometric')
        bininfo['pitchcenters'], bininfo['dPitch'], bininfo['nPitch'] = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
    return bininfo

def load_metadata_full():
    """Загружает Geo/Selection и матрицу совместимости."""
    geo_str = ['RB3']; sel_str = ['ItalianH']; gs = np.ones((1,1), dtype=bool)
    mat = _load_mat_file(METADATA_FILE)
    if mat:
        try:
            raw_geo = get_val(mat, 'GeoSelections')
            raw_sel = get_val(mat, 'Selections')
            if raw_geo is not None and raw_sel is not None:
                valid = (raw_geo != 'None') & (raw_sel != 'None')
                geo_str = sorted(list(np.unique(raw_geo[valid])))
                sel_str = sorted(list(np.unique(raw_sel[valid])))
                geo_map = {k:v for v,k in enumerate(geo_str)}
                sel_map = {k:v for v,k in enumerate(sel_str)}
                gs = np.zeros((len(geo_str), len(sel_str)), dtype=bool)
                for g, s in zip(raw_geo[valid], raw_sel[valid]):
                    if g in geo_map and s in sel_map: gs[geo_map[g], sel_map[s]] = True
        except: pass
    return geo_str, sel_str, gs

# === КОНСТАНТЫ ДЛЯ ИНТЕРФЕЙСА (Рис. 6 в Протоколе) ===
DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation','External exp. data','Empyrical models','Space weather data']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'Blaz', 'Blzen', 'L1sec','Lat1sec', 'Lon1sec', 'Roll1sec', 'SPitch1sec', 'Yaw1sec','aTime', 'eqpitchlim', 'LocPitch', 'maxgyro', 'mingyro','TimeGap1sec', 'TimeGap2sec', 'trkMaskI1sec', 'trkMaskS1sec', 'Trig1sec']
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
DISTR_VARS = ['Flux','Number of events','Gathering power','livetime','Countrate','Relative error of flux','Four entities at once']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution','Radial distribution','Temporal variations','Variations along orbit','Fluxes Histogram','L-pitch map','E-pitch map','E-L map','Auxiliary parameters']
UNIT_STR = ['km', 'G', '', 'G', 'G', 'Re', '°', '°', '°','°', '°', 's', '°', '°', '°','°', 's', 's', '', '', '' ]
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
GEO_STR, SELECT_STR, GS_ARRAY = load_metadata_full()
BINNING_STR = ['P3L4E4'] # Заглушка, если get_unique_stdbinnings не используется
