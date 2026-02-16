"""
Модуль конфигурации (PROTOCOL COMPLIANT)
Реализует логику работы с биннингами согласно CheckProtocol (рис. 4, 8).
Автоматически рассчитывает центры (geometric mean для E/L) и ширину (dE/dL).
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime

# === ПУТИ ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
UI_DATA_PATH = os.path.join(PROJECT_ROOT, 'data')

# Логика внешнего диска
ext_root = "/Volumes/T7 Touch"
ext_clean = os.path.join(ext_root, "PAMELA_DATA")
BASE_DATA_PATH = ext_clean if os.path.exists(ext_clean) else ext_root

print(f"[CONFIG] UI файлы: {UI_DATA_PATH}")
print(f"[CONFIG] Данные:   {BASE_DATA_PATH}")

# === КЛЮЧЕВЫЕ ФАЙЛЫ ===
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
    """
    Вычисляет параметры бинов (центр и ширина) на основе границ.
    Geometric: для логарифмических шкал (Energy, Rigidity, L).
    Arithmetic: для линейных шкал (Pitch).
    """
    if edges_array is None: return [], [], []
    
    # Обработка вложенных массивов (Cell Arrays в MATLAB)
    if isinstance(edges_array, np.ndarray) and edges_array.dtype == 'O':
        centers, widths, counts = [], [], []
        for edges in edges_array:
            c, w, n = calculate_bin_params(edges, mode)
            centers.append(c); widths.append(w); counts.append(n)
        return np.array(centers, dtype='O'), np.array(widths, dtype='O'), np.array(counts, dtype='O')
    
    # Обработка массива чисел
    if isinstance(edges_array, (np.ndarray, list)) and len(edges_array) > 1:
        w = edges_array[1:] - edges_array[:-1] # Ширина (dE, dL...)
        
        if mode == 'geometric':
            # Защита от <=0
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
    
    if not os.path.exists(BINNING_INFO_FILE): return bininfo

    try:
        mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        
        # 1. Загрузка границ (как на рис. 4 протокола)
        for k in ['Lbin', 'pitchbin', 'Ebin', 'Rig']:
            val = get_val(mat, k)
            if val is None: val = get_val(mat, k.lower())
            if val is not None: bininfo[k] = val

        # 2. Расчет параметров (для построения графиков)
        bininfo['Ecenters'], bininfo['dE'], bininfo['nE'] = calculate_bin_params(bininfo['Ebin'], 'geometric')
        bininfo['Rigcenters'], bininfo['dR'], bininfo['nR'] = calculate_bin_params(bininfo['Rig'], 'geometric')
        bininfo['Lcenters'], bininfo['dL'], bininfo['nL'] = calculate_bin_params(bininfo['Lbin'], 'geometric')
        bininfo['pitchcenters'], bininfo['dPitch'], bininfo['nPitch'] = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
        
        print("[CONFIG] Геометрия бинов рассчитана.")

    except Exception as e: 
        print(f"[CONFIG] Ошибка BinningInfo: {e}")
        
    return bininfo

# === CONSTANTS & INIT ===
BIN_INFO = load_binning_info_direct()

# Заглушки для UI списков (если нужны)
def get_unique_stdbinnings(): return ['P3L4E4']
def load_metadata_full(): return ['RB3'], ['ItalianH'], np.ones((1,1)), {}

BINNING_STR = get_unique_stdbinnings()
GEO_STR, SELECT_STR, GS_ARRAY, FILE_INFO = load_metadata_full()
