"""
Модуль конфигурации (MODERNIZED SCIENTIFIC)
Автоматически вычисляет центры бинов и ошибки ширины,
чтобы соответствовать логике MATLAB (DrawSpectra.m).
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === ПУТИ ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
UI_DATA_PATH = os.path.join(PROJECT_ROOT, 'data')

# Внешний диск
ext_root = "/Volumes/T7 Touch"
ext_clean = os.path.join(ext_root, "PAMELA_DATA")
if os.path.exists(ext_clean):
    BASE_DATA_PATH = ext_clean
else:
    BASE_DATA_PATH = ext_root

print(f"[CONFIG] UI файлы (Metadata): {UI_DATA_PATH}")
print(f"[CONFIG] Данные (Flux):       {BASE_DATA_PATH}")

# === КЛЮЧЕВЫЕ ФАЙЛЫ ===
BINNING_INFO_FILE = os.path.join(UI_DATA_PATH, 'BinningInfo.mat')
METADATA_FILE = os.path.join(UI_DATA_PATH, 'file_metadata.mat')

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def _load_mat_file(path):
    if not path or not os.path.exists(path): return None
    try: return loadmat(path, squeeze_me=True, struct_as_record=False)
    except: return None

def get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key, None)
    return getattr(obj, key, None)

def calculate_bin_params(edges_array, mode='geometric'):
    """
    Вычисляет центры (centers) и ширину (d) бинов из границ.
    """
    if edges_array is None: return [], []
    
    # Если это массив массивов (cell array)
    if isinstance(edges_array, np.ndarray) and edges_array.dtype == 'O':
        centers = []
        widths = []
        for edges in edges_array:
            if isinstance(edges, (np.ndarray, list)) and len(edges) > 1:
                w = edges[1:] - edges[:-1] # Ширина
                
                # Центр
                if mode == 'geometric':
                    # Защита от отрицательных значений
                    valid_edges = edges.copy()
                    valid_edges[valid_edges <= 0] = 1e-9 
                    c = np.sqrt(valid_edges[:-1] * valid_edges[1:])
                else: 
                    c = (edges[:-1] + edges[1:]) / 2.0
                
                centers.append(c)
                widths.append(w)
            else:
                centers.append([])
                widths.append([])
        return np.array(centers, dtype='O'), np.array(widths, dtype='O')
        
    # Если это одиночный массив
    elif isinstance(edges_array, (np.ndarray, list)) and len(edges_array) > 1:
        w = edges_array[1:] - edges_array[:-1]
        if mode == 'geometric':
            valid_edges = edges_array.copy()
            valid_edges[valid_edges <= 0] = 1e-9
            c = np.sqrt(valid_edges[:-1] * valid_edges[1:])
        else:
            c = (edges_array[:-1] + edges_array[1:]) / 2.0
        return c, w
        
    return [], []

def load_binning_info_direct():
    """Загружает BinningInfo и вычисляет недостающую геометрию."""
    bininfo = { 
        'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [],
        'Ecenters': [], 'Rigcenters': [], 'Lcenters': [], 'pitchcenters': [],
        'dE': [], 'dR': [], 'dL': [], 'dPitch': []
    }
    
    if not os.path.exists(BINNING_INFO_FILE): return bininfo

    try:
        mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        
        # 1. Загружаем исходные границы (они там точно есть)
        for k in ['Lbin', 'pitchbin', 'Ebin', 'Rig']:
            val = get_val(mat, k)
            if val is None: val = get_val(mat, k.lower())
            if val is not None: bininfo[k] = val

        # 2. ВЫЧИСЛЯЕМ то, чего нет (для полного соответствия валидации)
        # Энергия и L - логарифмические (геометрическое среднее)
        bininfo['Ecenters'], bininfo['dE'] = calculate_bin_params(bininfo['Ebin'], 'geometric')
        bininfo['Rigcenters'], bininfo['dR'] = calculate_bin_params(bininfo['Rig'], 'geometric')
        bininfo['Lcenters'], bininfo['dL'] = calculate_bin_params(bininfo['Lbin'], 'geometric')
        
        # Питч-углы - линейные (арифметическое среднее)
        bininfo['pitchcenters'], bininfo['dPitch'] = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
        
        print("[CONFIG] Бины и ошибки (dE, dR) успешно вычислены.")

    except Exception as e: 
        print(f"[CONFIG] Ошибка обработки BinningInfo: {e}")
        pass
        
    return bininfo

def get_unique_stdbinnings():
    default = ['P3L4E4']
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
    mat = _load_mat_file(METADATA_FILE)
    if mat:
        try:
            raw_geo = get_val(mat, 'GeoSelections')
            raw_sel = get_val(mat, 'Selections')
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
    return geo_str, sel_str, gs, file_info

# === КОНСТАНТЫ ===
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')
DATA_SOURCE_STR = ['PAMELA exp. data','External exp. data','Empyrical models']
GEN_STR = ['Alt1sec', 'Babs1sec', 'BB01sec', 'L1sec','Lat1sec', 'Lon1sec']
UNIT_STR = ['km', 'G', '', 'G', 'G', 'Re']
TBIN_STR = ['passage','day','Separate Periods']

# === ИНИЦИАЛИЗАЦИЯ ===
BIN_INFO = load_binning_info_direct()
BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY, FILE_INFO = load_metadata_full()

if GS_ARRAY.ndim != 2: 
    GS_ARRAY = np.ones((len(GEO_STR), len(SELECT_STR)), dtype=bool)
