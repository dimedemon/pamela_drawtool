"""
Модуль конфигурации (FIXED DICT VERSION)
Исправлена ошибка доступа к ключам .mat файла.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime
from . import kinematics

# === ПУТИ ===
# core/config.py -> core/../ -> root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
BINNING_INFO_FILE = os.path.join(DATA_DIR, 'BinningInfo.mat')
METADATA_FILE = os.path.join(DATA_DIR, 'file_metadata.mat')

print(f"[CONFIG] Путь к данным: {DATA_DIR}")

# --- Константы ---
PAMSTART = (datetime(2005, 12, 31) - datetime(1, 1, 1)).days + 1721425.5 
HTML_TEXT_COLOR = ('<HTML><FONT color="gray">', '</FONT></HTML>')

DATA_SOURCE_STR = ['PAMELA exp. data','Efficiency simulation','Anisotropic flux simulation',
                   'External exp. data','Empyrical models','Space weather data']
TBIN_STR = ['passage','day','month','3months','6months','year','bartels','Separate Periods']
PLOT_KINDS = ['Energy spectra','Rigidity spectra','pitch-angular distribution',
              'Radial distribution','Temporal variations','Variations along orbit',
              'Fluxes Histogram','L-pitch map','E-pitch map','E-L map','Auxiliary parameters']
GEO_STR = ['RB3']
SELECT_STR = ['ItalianH']

# --- ЗАГРУЗКА БИННИНГОВ ---
def load_binning_info_direct():
    """
    Загружает .mat файл напрямую в словарь, без сложных проверок атрибутов.
    """
    # Заготовка с пустыми списками, чтобы программа не падала, если ключа нет
    bininfo = {
        'Lbin': [], 'Lbindesc': [],
        'pitchbin': [], 'pitchbdesc': [],
        'Ebin': [], 'Ebindesc': [],
        'Rig': []
    }
    
    if not os.path.exists(BINNING_INFO_FILE):
        print(f"[CONFIG] ОШИБКА: Файл не найден: {BINNING_INFO_FILE}")
        return bininfo

    try:
        print(f"[CONFIG] Загрузка {BINNING_INFO_FILE}...")
        # Загружаем как словарь
        mat_dict = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
        
        # --- ПРЯМОЙ ПЕРЕНОС ДАННЫХ ---
        # Мы точно знаем ключи из вашего debug_test.py: 'Lbin', 'pitchbin', 'Ebin'
        
        # 1. Lbin
        if 'Lbin' in mat_dict:
            bininfo['Lbin'] = mat_dict['Lbin']
            print(f"[CONFIG] Lbin загружен. Размер: {len(bininfo['Lbin'])}")
        elif 'Lbins' in mat_dict:
             bininfo['Lbin'] = mat_dict['Lbins']
        
        # 2. pitchbin (важно: маленькая буква p, как выяснили)
        if 'pitchbin' in mat_dict:
            bininfo['pitchbin'] = mat_dict['pitchbin']
        elif 'PitchBin' in mat_dict:
            bininfo['pitchbin'] = mat_dict['PitchBin']
            
        # 3. Ebin
        if 'Ebin' in mat_dict:
            bininfo['Ebin'] = mat_dict['Ebin']

        # 4. Описания
        if 'Lbindesc' in mat_dict: bininfo['Lbindesc'] = mat_dict['Lbindesc']
        if 'pitchbdesc' in mat_dict: bininfo['pitchbdesc'] = mat_dict['pitchbdesc']
        if 'Ebindesc' in mat_dict: bininfo['Ebindesc'] = mat_dict['Ebindesc']

    except Exception as e:
        print(f"[CONFIG] Критическая ошибка чтения файла: {e}")

    # --- Расчет жесткости (Rigidity) ---
    try:
        ebins = bininfo['Ebin']
        # Если это не список, делаем списком
        if not isinstance(ebins, (list, np.ndarray)) or (isinstance(ebins, np.ndarray) and ebins.dtype != object):
             ebins = [ebins]
        
        rig_list = []
        for e in ebins:
            if np.ndim(e) == 0: continue # Пропуск пустых
            e = np.atleast_1d(e)
            # Упрощенная формула R = sqrt(E^2 + 2Em)
            m = 0.938
            R = np.sqrt(e**2 + 2*e*m)
            rig_list.append(R)
        bininfo['Rig'] = np.array(rig_list, dtype=object)
    except Exception as e:
        print(f"[CONFIG] Ошибка расчета Rigidity: {e}")

    return bininfo

# === ИНИЦИАЛИЗАЦИЯ ===
# Запускается при импорте
BIN_INFO = load_binning_info_direct()
