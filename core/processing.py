"""
Модуль Обработки (Processing Module) - FINAL GOLD
Исправлено:
1. Ошибка 'numpy has no attribute warnings'.
2. Авто-определение осей (Energy=6, Pitch=3, L=16).
3. Fallback: если выборка пуста, берет среднее по всем L.
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
    print(f"\n[PROCESSING] -> Старт обработки (Final Gold)")

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
        # Логика: Energy=6 (совпадает с конфигом), Pitch=3 (обычно мало), L=остальное (16)
        shape = data_raw.shape
        dims = [0, 1, 2]
        
        e_axis = -1
        # Ищем ось длины 6
        if shape[0] == config_n_E: e_axis = 0
        elif shape[1] == config_n_E: e_axis = 1
        elif shape[2] == config_n_E: e_axis = 2
        
        if e_axis == -1:
            print(f"    [WARN] {os.path.basename(fpath)} пропускается (нет оси E={config_n_E})")
            continue
            
        # Оставшиеся оси распределяем: меньшая -> Pitch, большая -> L
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
            
            # Пробуем взять выборку пользователя
            valid_L = [i for i in L_indices if i < n_L]
            valid_P = [i for i in P_indices if i < n_P]
            
            # --- AUTO-RECOVERY ---
            # Если выборка пуста (например, L-бины пользователя 0..2, а данные в 3..15),
            # берем ВСЕ доступные L
            fallback_used = False
            if not valid_L: 
                valid_L = range(n_L)
                fallback_used = True
            if not valid_P: 
                valid_P = range(n_P)
                fallback_used = True
            
            subset = data_sorted[:, valid_L, :][:, :, valid_P]
            
            # Проверка на пустоту данных (нули)
            if np.all(subset == 0):
                if not fallback_used:
                    print(f"    [WARN] Выбранная область пуста. Пробую взять среднее по всему файлу...")
                    subset = data_sorted
                    subset[subset==0] = np.nan
                else:
                    print(f"    [WARN] Файл пуст.")
                    continue
            else:
                subset[subset == 0] = np.nan

            # Усредняем
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                daily_spectrum = np.nanmean(subset, axis=(1, 2))
            
            # Проверка, что спектр не NaN
            if np.all(np.isnan(daily_spectrum)):
                continue

            accumulated_spectra.append(daily_spectrum)
            
        except Exception as e:
            print(f"    [ERROR] {e}")
            continue

    # 4. ФИНАЛЬНАЯ СБОРКА
    if not accumulated_spectra:
        print("[PROCESSING] Нет данных (все файлы пусты или не подходят).")
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

    # Фильтруем NaN и нули для лог-шкалы
    valid_mask = ~np.isnan(y_out) & (y_out > 0)
    
    if not np.any(valid_mask):
        print("[PROCESSING] Все значения потока <= 0.")
        return []

    print(f"[PROCESSING] График готов! Точек: {np.sum(valid_mask)}")

    return [{
        "ax_index": ax_index,
        "type": "spectra",
        "x_values": x_out[valid_mask],
        "y_values": y_out[valid_mask],
        "y_err": err_out[valid_mask],
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
