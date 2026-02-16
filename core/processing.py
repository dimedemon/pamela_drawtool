"""
Модуль Обработки (FINAL STABLE)
1. Исправлены ключи (x, y, y_err) для matplotlib_widget.
2. Добавлено масштабирование 1e7 (cm^-2 -> m^-2).
3. Усилена надежность при пустых выборках.
"""
import os
import numpy as np
import warnings
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    if values is None or len(values) == 0: return np.array([], dtype=int)
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    # 1. Загрузка параметров осей
    try:
        idx_L, idx_P, idx_E = app_state.lb - 1, app_state.pitchb - 1, app_state.eb - 1
        n_L_exp, n_P_exp = config.BIN_INFO['nL'][idx_L], config.BIN_INFO['nPitch'][idx_P]
        
        if app_state.ror_e == 1:
            X_full, X_err_half = config.BIN_INFO['Ecenters'][idx_E], config.BIN_INFO['dE'][idx_E] / 2.0
            x_label = "Kinetic Energy (GeV)"
        else:
            X_full, X_err_half = config.BIN_INFO['Rigcenters'][idx_E], config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
        n_E_exp = len(X_full)
    except: return []

    # 2. Поиск файлов
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra, accumulated_errors = [], []
    FUNITS = 1e7 # Масштаб

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Поиск данных J и ошибок dJ
        data_raw = getattr(mat, 'Jday', getattr(mat, 'J', None))
        error_raw = getattr(mat, 'dJday', getattr(mat, 'dJ', None))
        if data_raw is None or data_raw.ndim != 3: continue
        if error_raw is None: error_raw = np.zeros_like(data_raw)

        # Ориентация осей на основе ваших логов (L=3, E=6, P=16)
        shape = data_raw.shape
        ax_L, ax_E, ax_P = -1, -1, -1
        for i in range(3):
            if shape[i] == n_E_exp: ax_E = i; break
        for i in range(3):
            if i != ax_E and shape[i] == n_L_exp: ax_L = i; break
        for i in range(3):
            if i != ax_E and i != ax_L and shape[i] == n_P_exp: ax_P = i; break
        
        if ax_E == -1: ax_L, ax_E, ax_P = 0, 1, 2 # Fallback

        try:
            data_sorted = np.transpose(data_raw, (ax_E, ax_L, ax_P))
            error_sorted = np.transpose(error_raw, (ax_E, ax_L, ax_P))
            
            # Срез по выбранным L и Pitch
            L_indices = _find_bin_indices(config.BIN_INFO['Lbin'][idx_L], app_state.l)
            P_indices = _find_bin_indices(config.BIN_INFO['pitchbin'][idx_P], app_state.pitch)
            
            subset_d = data_sorted[:, L_indices, :][:, :, P_indices]
            subset_e = error_sorted[:, L_indices, :][:, :, P_indices]
            
            # Если срез пуст, пробуем взять весь файл (как Fallback)
            if np.nansum(subset_d) == 0:
                subset_d, subset_e = data_sorted, error_sorted

            subset_d[subset_d == 0] = np.nan
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                spec = np.nanmean(subset_d, axis=(1, 2))
                err = np.sqrt(np.nansum(subset_e**2, axis=(1, 2))) / np.maximum(np.sum(~np.isnan(subset_d), axis=(1, 2)), 1)
            
            if not np.all(np.isnan(spec)):
                accumulated_spectra.append(spec)
                accumulated_errors.append(err)
        except: continue

    if not accumulated_spectra: return []
    
    final_y = np.nanmean(accumulated_spectra, axis=0) * FUNITS
    final_err = (np.nanstd(accumulated_spectra, axis=0) if len(accumulated_spectra) > 1 else accumulated_errors[0]) * FUNITS

    mask = ~np.isnan(final_y) & (final_y > 0)
    
    # ВОЗВРАЩАЕМ КЛЮЧИ СОГЛАСНО matplotlib_widget.py
    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar", # Обязательно этот ключ
        "x": X_full[mask],
        "y": final_y[mask],
        "y_err": final_err[mask],
        "x_err": X_err_half[mask],
        "xlabel": x_label,
        "ylabel": "Flux (GeV m^2 sr s)^-1",
        "xscale": "log", "yscale": "log",
        "label": f"Spectrum (N={len(files)})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk < 2: return _generic_1d_plot(app_state, ax_index) # Индексы в интерфейсе 0, 1
    return []
