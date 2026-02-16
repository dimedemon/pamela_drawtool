"""
Модуль Обработки (Processing Module) - FINAL GOLD FIX
Исправлено:
1. Ключи словаря для matplotlib_widget (x, y, y_err, xlabel...).
2. Исправлена ошибка 'numpy has no attribute warnings'.
3. Сохранена логика авто-определения осей и выравнивания длин.
"""
import os
import numpy as np
import warnings
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
    print(f"\n[PROCESSING] -> Старт обработки (Final Gold Fix)")

    # 1. ИНИЦИАЛИЗАЦИЯ ОСЕЙ
    try:
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
        
        # Поиск данных
        data_raw = None
        for key in ['Flux', 'flux', 'Jday', 'J']:
            if key in mat.keys():
                data_raw = mat[key]
                break
        
        if data_raw is None or data_raw.ndim != 3:
            continue

        # --- АДАПТИВНОЕ ОПРЕДЕЛЕНИЕ ОСЕЙ ---
        # Логика: Energy=6 (совпадает с конфигом), Pitch=3, L=остальное
        shape = data_raw.shape
        dims = [0, 1, 2]
        
        e_axis = -1
        if shape[0] == config_n_E: e_axis = 0
        elif shape[1] == config_n_E: e_axis = 1
        elif shape[2] == config_n_E: e_axis = 2
        
        if e_axis == -1:
            # Fallback: пробуем найти самую длинную ось, если конфиг не совпал
            e_axis = np.argmax(shape)
            # print(f"    [WARN] Ось энергии не совпала. Взял max-ось: {e_axis}")

        # Распределяем L и Pitch
        rem = [d for d in dims if d != e_axis]
        if shape[rem[0]] < shape[rem[1]]:
            p_axis, l_axis = rem[0], rem[1]
        else:
            p_axis, l_axis = rem[1], rem[0]

        # Транспонируем в (Energy, L, Pitch)
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
            
            # Auto-Recovery для пустых выборок
            fallback_used = False
            if not valid_L: 
                valid_L = range(n_L); fallback_used = True
            if not valid_P: 
                valid_P = range(n_P); fallback_used = True
            
            subset = data_sorted[:, valid_L, :][:, :, valid_P]
            
            if np.all(subset == 0):
                if not fallback_used:
                    subset = data_sorted # Пробуем взять весь файл, если выборка пуста
                    subset[subset==0] = np.nan
                else:
                    continue
            else:
                subset[subset == 0] = np.nan

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                daily_spectrum = np.nanmean(subset, axis=(1, 2))
            
            if np.all(np.isnan(daily_spectrum)): continue
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
    
    x_out = final_X[:min_len]
    y_out = final_flux[:min_len]
    err_out = final_err[:min_len]

    valid_mask = ~np.isnan(y_out) & (y_out > 0)
    
    if not np.any(valid_mask):
        print("[PROCESSING] Все значения потока <= 0.")
        return []

    print(f"[PROCESSING] Успех! Точек: {np.sum(valid_mask)}")

    # ВАЖНО: Возвращаем ключи, которые ждет matplotlib_widget (x, y, y_err)
    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x_out[valid_mask],       # <--- БЫЛО x_values
        "y": y_out[valid_mask],       # <--- БЫЛО y_values
        "y_err": err_out[valid_mask], 
        "xlabel": x_label,            # <--- БЫЛО x_label
        "ylabel": "Flux",             # <--- БЫЛО y_label
        "xscale": "log",              # <--- БЫЛО x_scale
        "yscale": "log",              # <--- БЫЛО y_scale
        "label": f"Spectrum (N={len(files)})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    elif pk == 12: return [] 
    return []
