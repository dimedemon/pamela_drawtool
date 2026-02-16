"""
Модуль Обработки (Processing Module)
Убрано принудительное домножение на 10^7 согласно валидационному графику.
Сохранена логика точного определения осей и безопасного доступа к данным.
"""
import os
import numpy as np
import warnings
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    """Загружает .mat файл как словарь."""
    if not os.path.exists(file_path): return None
    try:
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    """Поиск индекса бина."""
    if values is None or (isinstance(values, (list, np.ndarray)) and len(values) == 0):
        return np.array([0])
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
    
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _get_spectra_data(app_state, ax_index):
    """Реализация логики из DrawSpectra.m без масштабирования."""
    print(f"\n[PROCESSING] -> Построение спектра (Raw Units)...")

    # 1. Параметры биннинга 
    try:
        idx_L, idx_P, idx_E = app_state.lb - 1, app_state.pitchb - 1, app_state.eb - 1
        L_edges = config.BIN_INFO['Lbin'][idx_L]
        P_edges = config.BIN_INFO['pitchbin'][idx_P]
        
        if app_state.ror_e == 1: # Energy
            x_centers = config.BIN_INFO['Ecenters'][idx_E]
            x_err_half = config.BIN_INFO['dE'][idx_E] / 2.0
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            x_centers = config.BIN_INFO['Rigcenters'][idx_E]
            x_err_half = config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
    except Exception as e:
        print(f"[ERROR] Ошибка биннинга: {e}")
        return []

    # 2. Индексы L и Pitch 
    l_indices = _find_bin_indices(L_edges, app_state.l)
    p_indices = _find_bin_indices(P_edges, app_state.pitch)

    # 3. Загрузка данных
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_y = []
    accumulated_y_err = []
    FUNITS = 1.0 # Множитель убран для соответствия валидации

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        j_data = None
        if 'Jday' in mat: j_data = mat['Jday']
        elif 'J' in mat: j_data = mat['J']
        
        dj_data = None
        if 'dJday' in mat: dj_data = mat['dJday']
        elif 'dJ' in mat: dj_data = mat['dJ']
        
        if j_data is None: continue

        try:
            # MATLAB: Jday(L, E, P). В файле (3, 6, 16) 
            subset_j = j_data[l_indices, :, :]
            subset_j = subset_j[:, :, p_indices]
            
            subset_dj = dj_data[l_indices, :, :] if dj_data is not None else np.zeros_like(subset_j)
            subset_dj = subset_dj[:, :, p_indices]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y_day = np.nanmean(subset_j, axis=(0, 2))
                y_err_day = np.sqrt(np.nansum(subset_dj**2, axis=(0, 2))) / np.sum(~np.isnan(subset_j), axis=(0, 2))

            accumulated_y.append(y_day)
            accumulated_y_err.append(y_err_day)
        except Exception as e:
            print(f"    [ERROR] Ошибка среза: {e}")
            continue

    if not accumulated_y: return []

    # 4. Финальный расчет
    final_y = np.nanmean(accumulated_y, axis=0) * FUNITS
    if len(accumulated_y) > 1:
        final_y_err = (np.nanstd(accumulated_y, axis=0) / np.sqrt(len(accumulated_y))) * FUNITS
    else:
        final_y_err = accumulated_y_err[0] * FUNITS

    mask = ~np.isnan(final_y) & (final_y > 0)
    if not np.any(mask): return []

    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x_centers[mask],
        "y": final_y[mask],
        "y_err": final_y_err[mask],
        "x_err": x_err_half[mask],
        "xlabel": x_label,
        "ylabel": "Flux (MeV cm^2 sr s)^-1",
        "xscale": "log", "yscale": "log",
        "label": f"PAMELA Spectrum (N={len(accumulated_y)})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk == 0 or pk == 1:
        return _get_spectra_data(app_state, ax_index)
    return []
