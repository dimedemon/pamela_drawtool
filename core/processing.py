"""
Модуль Обработки (HISTOGRAM & VARIANCE ANALYSIS)
Добавлено:
- Функция _get_flux_histogram_data для анализа разброса в одной ячейке.
- Сбор данных N (частота) vs Flux (интенсивность) за выбранный период.
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
    """Находит индекс бина для заданного значения согласно протоколу."""
    if values is None or (isinstance(values, (list, np.ndarray)) and len(values) == 0):
        return np.array([0])
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _get_spectra_data(app_state, ax_index):
    """Отрисовка стандартных энергетических/жесткостных спектров."""
    print(f"\n[PROCESSING] -> Построение спектра (Day {app_state.pam_pers})...")
    try:
        idx_L, idx_P, idx_E = app_state.lb - 1, app_state.pitchb - 1, app_state.eb - 1
        L_edges = config.BIN_INFO['Lbin'][idx_L]
        P_edges = config.BIN_INFO['pitchbin'][idx_P]
        
        if app_state.ror_e == 1:
            x_centers_all = config.BIN_INFO['Ecenters'][idx_E]
            x_err_half_all = config.BIN_INFO['dE'][idx_E] / 2.0
            x_label = "E (GeV)"
        else:
            x_centers_all = config.BIN_INFO['Rigcenters'][idx_E]
            x_err_half_all = config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
            
        x_centers = x_centers_all[:-1]
        x_err_half = x_err_half_all[:-1]
        n_E_valid = len(x_centers)
    except Exception as e:
        print(f"[ERROR] Ошибка биннинга: {e}")
        return []

    l_indices = _find_bin_indices(L_edges, app_state.l)
    p_indices = _find_bin_indices(P_edges, app_state.pitch)
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_y, accumulated_y_err = [], []
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        j_data = mat.get('Jday', mat.get('J'))
        dj_data = mat.get('dJday', mat.get('dJ'))
        if j_data is None: continue

        try:
            subset_j = j_data[l_indices, :n_E_valid, :]
            subset_j = subset_j[:, :, p_indices]
            subset_dj = dj_data[l_indices, :n_E_valid, :] if dj_data is not None else np.zeros_like(subset_j)
            subset_dj = subset_dj[:, :, p_indices]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y_day = np.nanmean(subset_j, axis=(0, 2))
                y_err_day = np.sqrt(np.nansum(subset_dj**2, axis=(0, 2))) / np.sum(~np.isnan(subset_j), axis=(0, 2))
            accumulated_y.append(y_day)
            accumulated_y_err.append(y_err_day)
        except: continue

    if not accumulated_y: return []
    final_y = np.nanmean(accumulated_y, axis=0)
    final_y_err = np.nanstd(accumulated_y, axis=0) / np.sqrt(len(accumulated_y)) if len(accumulated_y) > 1 else accumulated_y_err[0]
    mask = ~np.isnan(final_y) & (final_y > 0)
    if not np.any(mask): return []

    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x_centers[mask], "y": final_y[mask], "y_err": final_y_err[mask], "x_err": x_err_half[mask],
        "xlabel": x_label, "ylabel": "Flux (MeV cm^2 sr s)^-1",
        "xscale": "log", "yscale": "log",
        "label": f"PAMELA Spectrum (Day {app_state.pam_pers})"
    }]

def _get_flux_histogram_data(app_state, ax_index):
    """Сбор распределения потоков в ОДНОЙ ячейке за период времени."""
    print(f"\n[PROCESSING] -> Анализ разброса потоков (Histogram)...")

    # 1. Определение точной ячейки (L, E, P)
    try:
        idx_L_set, idx_P_set, idx_E_set = app_state.lb-1, app_state.pitchb-1, app_state.eb-1
        
        # Индексы ячеек из BinningInfo
        l_idx = _find_bin_indices(config.BIN_INFO['Lbin'][idx_L_set], app_state.l)[0]
        p_idx = _find_bin_indices(config.BIN_INFO['pitchbin'][idx_P_set], app_state.pitch)[0]
        
        # Индекс энергии
        edges_e = config.BIN_INFO['Ebin'][idx_E_set] if app_state.ror_e == 1 else config.BIN_INFO['Rig'][idx_E_set]
        e_idx = _find_bin_indices(edges_e, app_state.e)[0]
    except Exception as e:
        print(f"[ERROR] Ошибка определения ячейки: {e}")
        return []

    # 2. Сбор данных из файлов (например, за 10 дней)
    files = file_manager.get_input_filenames(app_state, 'flux')
    flux_samples = []

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Чтение Jday(L, E, P)
        j_data = mat.get('Jday', mat.get('J'))
        if j_data is not None:
            try:
                # Берем ровно одну точку из каждого файла
                val = j_data[l_idx, e_idx, p_idx]
                if val > 0 and not np.isnan(val):
                    flux_samples.append(val)
            except: continue

    if not flux_samples:
        print("[PROCESSING] Нет данных в выбранной ячейке за указанный период.")
        return []

    # 3. Подготовка структуры гистограммы N vs Flux
    return [{
        "ax_index": ax_index,
        "plot_type": "histogram",
        "x": np.array(flux_samples),
        "bins": 20,
        "xlabel": "Flux Intensity (MeV cm^2 sr s)^-1",
        "ylabel": "N (Frequency)",
        "xscale": "linear", "yscale": "log", # Лог-шкала Y для изучения хвостов
        "title": f"Flux Distribution (L={app_state.l}, P={app_state.pitch}, E={app_state.e})",
        "label": f"Samples: {len(flux_samples)}"
    }]

def get_plot_data(app_state, ax_index=0):
    """Диспетчер задач на основе выбора в интерфейсе."""
    pk = app_state.plot_kind
    if pk == 0 or pk == 1:
        return _get_spectra_data(app_state, ax_index)
    elif pk == 6: # Fluxes Histogram (7-й пункт в PLOT_KINDS)
        return _get_flux_histogram_data(app_state, ax_index)
    return []
