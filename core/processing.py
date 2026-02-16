"""
Модуль Обработки (Processing Module) - FINAL ROBUST v2
Исправлено:
1. Ошибка 'numpy has no attribute warnings' (для NumPy 1.24+).
2. Ошибки размерностей массивов (Robust slicing).
3. Авто-определение осей (Adaptive Axes).
"""
import os
import numpy as np
import warnings  # <--- ДОБАВЛЕНО: Стандартный модуль вместо np.warnings
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: 
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    if values is None or len(values) == 0: return np.array([], dtype=int)
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

# --- ГЛАВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ ---
def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    print(f"\n[PROCESSING] -> Старт обработки (Robust Mode v2)")

    # 1. ИНИЦИАЛИЗАЦИЯ ОСЕЙ
    try:
        # Индексы 1-based -> 0-based
        L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
        P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
        
        if app_state.ror_e == 1: # Energy
            X_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
            x_label = "Rigidity (GV)"
            
        X_centers = np.sqrt(X_edges[:-1] * X_edges[1:])
        config_n_E = len(X_centers)
        print(f"[PROCESSING] Конфиг: Energy={config_n_E} bins.")
    except Exception as e:
        print(f"[ERROR] Ошибка биннинга: {e}")
        return []

    # 2. ИНДЕКСЫ ВЫБОРКИ
    target_l = app_state.l if (app_state.l and len(app_state.l) > 0) else [(L_edges[0] + L_edges[-1])/2]
    target_p = app_state.pitch if (app_state.pitch and len(app_state.pitch) > 0) else [45.0]

    L_indices = _find_bin_indices(L_edges, target_l)
    P_indices = _find_bin_indices(P_edges, target_p)

    # 3. ПОИСК ФАЙЛОВ
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra = []
    
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Поиск данных (поддержка Flux, flux, Jday, J)
        data_raw = None
        var_name = "Unknown"
        keys = mat.keys()
        
        for key in ['Flux', 'flux', 'Jday', 'J']:
            if key in keys:
                data_raw = mat[key]
                var_name = key
                break
        
        if data_raw is None:
            continue

        if data_raw.ndim != 3:
            continue

        # --- АДАПТИВНОЕ ОПРЕДЕЛЕНИЕ ОСЕЙ ---
        shape = data_raw.shape
        dims = [0, 1, 2]
        
        e_axis = -1
        if shape[0] == config_n_E: e_axis = 0
        elif shape[1] == config_n_E: e_axis = 1
        elif shape[2] == config_n_E: e_axis = 2
        
        if e_axis == -1:
            print(f"    [WARN] Пропуск {os.path.basename(fpath)}: нет оси длины {config_n_E}. Shape={shape}")
            continue
            
        # Распределяем L и Pitch
        rem_axes = [d for d in dims if d != e_axis]
        if shape[rem_axes[0]] < shape[rem_axes[1]]:
            p_axis, l_axis = rem_axes[0], rem_axes[1]
        else:
            p_axis, l_axis = rem_axes[1], rem_axes[0]

        # Транспонируем в стандарт (Energy, L, Pitch)
        if [e_axis, l_axis, p_axis] != [0, 1, 2]:
            data_sorted = np.transpose(data_raw, (e_axis, l_axis, p_axis))
        else:
            data_sorted = data_raw

        # --- СРЕЗ И УСРЕДНЕНИЕ ---
        try:
            n_L = data_sorted.shape[1]
            n_P = data_sorted.shape[2]
            
            valid_L = [i for i in L_indices if i < n_L]
            valid_P = [i for i in P_indices if i < n_P]
            
            if not valid_L or not valid_P: continue

            subset = data_sorted[:, valid_L, :][:, :, valid_P]
            subset[subset == 0] = np.nan
            
            # Используем стандартный warnings вместо np.warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                daily_spectrum = np.nanmean(subset, axis=(1, 2))
            
            accumulated_spectra.append(daily_spectrum)
            
        except Exception as e:
            print(f"    [ERROR] {e}")
            continue

    # 4. ФИНАЛЬНАЯ СБОРКА
    if not accumulated_spectra:
        print("[PROCESSING] Нет данных.")
        return []

    all_spectra = np.array(accumulated_spectra)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        final_flux = np.nanmean(all_spectra, axis=0)
        
        if len(accumulated_spectra) > 1:
            final_err = np.nanstd(all_spectra, axis=0) / np.sqrt(len(accumulated_spectra))
        else:
            final_err = np.zeros_like(final_flux)

    final_X = X_centers

    # --- SAFETY CUT (Гарантия равных длин) ---
    min_len = min(len(final_X), len(final_flux), len(final_err))
    
    final_X = final_X[:min_len]
    final_flux = final_flux[:min_len]
    final_err = final_err[:min_len]

    valid_mask = ~np.isnan(final_flux) & (final_flux > 0)
    
    x_out = final_X[valid_mask]
    y_out = final_flux[valid_mask]
    err_out = final_err[valid_mask]

    if len(x_out) == 0:
        print("[PROCESSING] Все данные пусты (NaN/Zero).")
        return []

    print(f"[PROCESSING] Успех! Точек: {len(x_out)}")

    return [{
        "ax_index": ax_index,
        "type": "spectra",
        "x_values": x_out,
        "y_values": y_out,
        "y_err": err_out,
        "x_label": x_label,
        "y_label": "Flux",
        "x_scale": "log", "y_scale": "log",
        "title": f"Spectrum (N={len(files)})",
        "label": "PAMELA Data"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    elif pk == 12: return [] 
    return []
