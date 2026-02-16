"""
Модуль Обработки (VALIDATION MATCH)
Исправлено:
1. Удалена лишняя (последняя) точка - overflow bin.
2. Синхронизированы X-координаты с центрами бинов.
3. Убрано масштабирование 10^7 согласно требованию пользователя.
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
    if values is None or (isinstance(values, (list, np.ndarray)) and len(values) == 0):
        return np.array([0])
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _get_spectra_data(app_state, ax_index):
    print(f"\n[PROCESSING] -> Построение спектра (Day {app_state.pam_pers})...")

    # 1. Параметры биннинга
    try:
        idx_L, idx_P, idx_E = app_state.lb - 1, app_state.pitchb - 1, app_state.eb - 1
        L_edges = config.BIN_INFO['Lbin'][idx_L]
        P_edges = config.BIN_INFO['pitchbin'][idx_P]
        
        if app_state.ror_e == 1: # Energy
            x_centers_all = config.BIN_INFO['Ecenters'][idx_E]
            x_err_half_all = config.BIN_INFO['dE'][idx_E] / 2.0
            x_label = "E (GeV)"
        else: # Rigidity
            x_centers_all = config.BIN_INFO['Rigcenters'][idx_E]
            x_err_half_all = config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
            
        # УДАЛЯЕМ ПОСЛЕДНИЙ БИН (Overflow) для соответствия валидации
        x_centers = x_centers_all[:-1]
        x_err_half = x_err_half_all[:-1]
        n_E_valid = len(x_centers)
        
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

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        j_data = mat.get('Jday', mat.get('J'))
        dj_data = mat.get('dJday', mat.get('dJ'))
        
        if j_data is None: continue

        try:
            # MATLAB: Jday(L, E, P). Срезаем по осям.
            # Нам нужны только первые n_E_valid бинов по энергии (ось 1)
            subset_j = j_data[l_indices, :n_E_valid, :] # <--- Срез до n_E_valid!
            subset_j = subset_j[:, :, p_indices]
            
            subset_dj = dj_data[l_indices, :n_E_valid, :] if dj_data is not None else np.zeros_like(subset_j)
            subset_dj = subset_dj[:, :, p_indices]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Усреднение по L и Pitch
                y_day = np.nanmean(subset_j, axis=(0, 2))
                y_err_day = np.sqrt(np.nansum(subset_dj**2, axis=(0, 2))) / np.sum(~np.isnan(subset_j), axis=(0, 2))

            accumulated_y.append(y_day)
            accumulated_y_err.append(y_err_day)
        except Exception as e:
            print(f"    [ERROR] Ошибка среза в {os.path.basename(fpath)}: {e}")
            continue

    if not accumulated_y: return []

    # 4. Финальный расчет (без множителя 10^7)
    final_y = np.nanmean(accumulated_y, axis=0)
    if len(accumulated_y) > 1:
        final_y_err = np.nanstd(accumulated_y, axis=0) / np.sqrt(len(accumulated_y))
    else:
        final_y_err = accumulated_y_err[0]

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
        "label": f"PAMELA Spectrum (Day {app_state.pam_pers})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk == 0 or pk == 1:
        return _get_spectra_data(app_state, ax_index)
    return []
