"""
Модуль Обработки (Фаза 3 - Radial Distribution)
"""

import os
import numpy as np
from scipy.io import loadmat
from . import config
from . import state

def _load_mat_file(file_path):
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл данных не найден: {file_path}")
        return None
    try:
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def _build_data_path(app_state: state.ApplicationState):
    if app_state.ror_e == 2:
        er = f"R{app_state.eb}"
    else:
        er = f"E{app_state.eb}"

    version_float = float(app_state.flux_version.replace('v', ''))
    if version_float < 5.0:
        binningpath = f"stdbinning{app_state.pitchb}{app_state.lb}e{app_state.eb}"
    else:
        binningpath = f"stdbinning_P{app_state.pitchb}L{app_state.lb}{er}"

    if app_state.tbin == 'Separate Periods':
        FCpath = 'RBfullfluxes'
    else:
        FCpath = f"RB{app_state.tbin}fluxes"

    inpath = os.path.join(config.GEN_PATH, 'Loc', app_state.flux_version,
                          app_state.selection, binningpath, FCpath)
    return inpath

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- СУЩЕСТВУЮЩАЯ ФУНКЦИЯ (SPECTRA) ---
def _get_spectra_data(app_state: state.ApplicationState, ax_index: int):
    # ... (Код _get_spectra_data остается без изменений, как в прошлом шаге) ...
    # (Для краткости я не дублирую его здесь, оставьте старый код этой функции)
    # ...
    # Если нужно, я могу продублировать его, но лучше просто добавить новую функцию ниже.
    pass 

# --- НОВАЯ ФУНКЦИЯ (RADIAL) ---
def _get_radial_data(app_state: state.ApplicationState, ax_index: int):
    """
    Порт DrawRadial.m
    Строит зависимость потока от L-оболочки.
    """
    plot_data_list = []
    base_path = _build_data_path(app_state)
    
    # Границы бинов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    pitch_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    # Вычисляем центры L-бинов (Ось X для этого графика)
    L_centers = (L_edges[:-1] + L_edges[1:]) / 2
    dL = (L_edges[1:] - L_edges[:-1]) / 2
    
    # Находим индексы для ФИКСИРОВАННЫХ параметров (Pitch и E/R)
    pitch_indices = _find_bin_indices(pitch_edges, app_state.pitch)
    
    if app_state.ror_e == 1: # E
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_values = app_state.e
    else: # R
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_values = app_state.rig
        
    E_indices = _find_bin_indices(E_edges, E_values)

    periods = app_state.pam_pers 
    if app_state.tbin == 'Separate Periods':
        periods = [app_state.period]
    elif not periods:
        periods = [200] # Хардкод для теста

    for period in periods:
        infile = os.path.join(base_path, f"RBflux_{period}.mat")
        data = _load_mat_file(infile)
        if data is None: continue
            
        if app_state.fullday:
            try:
                JJ = data['Jday']
                dJJ = data['dJday']
                NN = data['numevday']
            except KeyError: return []
            
            # --- Цикл по E-бинам (фиксированным) ---
            for e_idx in np.unique(E_indices):
                # --- Цикл по Pitch-бинам (фиксированным) ---
                for p_idx in np.unique(pitch_indices):
                    
                    # Извлечение данных: J(L, E, P)
                    # Нам нужны ВСЕ L (slice :), конкретный E, конкретный P
                    y_data = JJ[:, e_idx, p_idx]
                    y_err = dJJ[:, e_idx, p_idx]
                    n_events = NN[:, e_idx, p_idx]
                    
                    valid_indices = (n_events > app_state.n_min)
                    if not np.any(valid_indices): continue
                        
                    # Лейбл
                    val_name = "E" if app_state.ror_e == 1 else "R"
                    val_unit = "GeV" if app_state.ror_e == 1 else "GV"
                    val_center = (E_edges[e_idx] + E_edges[e_idx+1])/2
                    
                    label = (f"{val_name}={val_center:.3f} {val_unit}, "
                             f"P=[{pitch_edges[p_idx]:.0f}-{pitch_edges[p_idx+1]:.0f}], "
                             f"Day={period}")
                    
                    plot_data_list.append({
                        "ax_index": ax_index,
                        "plot_type": "errorbar",
                        "x": L_centers[valid_indices], # L по оси X
                        "y": y_data[valid_indices],
                        "x_err": dL[valid_indices],
                        "y_err": y_err[valid_indices],
                        "label": label,
                        "xlabel": "L-shell",
                        "ylabel": "J",
                        "xscale": "linear", # L обычно в линейном масштабе
                        "yscale": "log"
                    })
    return plot_data_list

# --- ГЛАВНЫЙ ДИСПЕТЧЕР ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    gen = app_state.gen 
    plot_kind = app_state.plot_kind 

    if gen == 1: # PAMELA exp. data
        if plot_kind == 1 or plot_kind == 2: # Spectra
            # Вызываем старую функцию (убедитесь, что она есть в файле!)
            return _get_spectra_data(app_state, ax_index) 
        
        elif plot_kind == 3: # pitch-angular
            pass
        elif plot_kind == 4: # Radial distribution
            return _get_radial_data(app_state, ax_index) # <--- НОВЫЙ ВЫЗОВ
            
    return []
