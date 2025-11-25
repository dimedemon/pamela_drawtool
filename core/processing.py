"""
Модуль Обработки (Фаза 3 - С использованием File Manager)
"""

import os
import numpy as np
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager # <--- НОВЫЙ ИМПОРТ

def _load_mat_file(file_path):
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл данных не найден: {file_path}")
        return None
    try:
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

def _get_spectra_data(app_state: state.ApplicationState, ax_index: int):
    plot_data_list = []
    
    # --- ИСПОЛЬЗУЕМ НОВЫЙ МЕНЕДЖЕР ФАЙЛОВ ---
    filenames, base_path = file_manager.get_input_filenames(app_state, 'flux')
    
    # Границы бинов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    pitch_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: # E
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_centers = (E_edges[:-1] + E_edges[1:]) / 2
        dE = (E_edges[1:] - E_edges[:-1]) / 2
        x_data, dx_data = E_centers, dE
        x_label = "E, GeV"
    else: # R
        R_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        R_centers = (R_edges[:-1] + R_edges[1:]) / 2
        dR = (R_edges[1:] - R_edges[:-1]) / 2
        x_data, dx_data = R_centers, dR
        x_label = "R, GV"

    # Фиксированные параметры
    L_indices = _find_bin_indices(L_edges, app_state.l)
    pitch_indices = _find_bin_indices(pitch_edges, app_state.pitch)
    
    # --- ЦИКЛ ПО ФАЙЛАМ (полученным из file_manager) ---
    for fname in filenames:
        infile = os.path.join(base_path, fname)
        data = _load_mat_file(infile)
        if data is None: continue
            
        # Извлекаем "день" из имени файла для лейбла (RBflux_200.mat -> 200)
        # (Это упрощенно, можно сделать красивее через regex)
        try:
            day_str = fname.split('_')[1].split('.')[0]
        except:
            day_str = "Unknown"

        if app_state.fullday:
            try:
                JJ = data['Jday']
                dJJ = data['dJday']
                NN = data['numevday']
            except KeyError: return []
            
            for l_idx in np.unique(L_indices):
                for p_idx in np.unique(pitch_indices):
                    y_data = JJ[l_idx, :, p_idx]
                    y_err = dJJ[l_idx, :, p_idx]
                    n_events = NN[l_idx, :, p_idx]
                    
                    valid_indices = (n_events > app_state.n_min)
                    if not np.any(valid_indices): continue
                        
                    label = (f"L=[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}], "
                             f"P=[{pitch_edges[p_idx]:.0f}-{pitch_edges[p_idx+1]:.0f}] deg, "
                             f"Day={day_str}")
                    
                    plot_data_list.append({
                        "ax_index": ax_index,
                        "plot_type": "errorbar",
                        "x": x_data[valid_indices],
                        "y": y_data[valid_indices],
                        "x_err": dx_data[valid_indices],
                        "y_err": y_err[valid_indices],
                        "label": label,
                        "xlabel": x_label,
                        "ylabel": "J",
                        "xscale": "log",
                        "yscale": "log"
                    })
    return plot_data_list

def _get_radial_data(app_state: state.ApplicationState, ax_index: int):
    plot_data_list = []
    
    # --- ИСПОЛЬЗУЕМ НОВЫЙ МЕНЕДЖЕР ФАЙЛОВ ---
    filenames, base_path = file_manager.get_input_filenames(app_state, 'flux')
    
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    pitch_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    L_centers = (L_edges[:-1] + L_edges[1:]) / 2
    dL = (L_edges[1:] - L_edges[:-1]) / 2
    
    pitch_indices = _find_bin_indices(pitch_edges, app_state.pitch)
    
    if app_state.ror_e == 1: # E
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_values = app_state.e
    else: # R
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_values = app_state.rig
        
    E_indices = _find_bin_indices(E_edges, E_values)

    for fname in filenames:
        infile = os.path.join(base_path, fname)
        data = _load_mat_file(infile)
        if data is None: continue
        
        try:
            day_str = fname.split('_')[1].split('.')[0]
        except:
            day_str = "Unknown"
            
        if app_state.fullday:
            try:
                JJ = data['Jday']
                dJJ = data['dJday']
                NN = data['numevday']
            except KeyError: return []
            
            for e_idx in np.unique(E_indices):
                for p_idx in np.unique(pitch_indices):
                    y_data = JJ[:, e_idx, p_idx]
                    y_err = dJJ[:, e_idx, p_idx]
                    n_events = NN[:, e_idx, p_idx]
                    
                    valid_indices = (n_events > app_state.n_min)
                    if not np.any(valid_indices): continue
                        
                    val_name = "E" if app_state.ror_e == 1 else "R"
                    val_unit = "GeV" if app_state.ror_e == 1 else "GV"
                    val_center = (E_edges[e_idx] + E_edges[e_idx+1])/2
                    
                    label = (f"{val_name}={val_center:.3f} {val_unit}, "
                             f"P=[{pitch_edges[p_idx]:.0f}-{pitch_edges[p_idx+1]:.0f}], "
                             f"Day={day_str}")
                    
                    plot_data_list.append({
                        "ax_index": ax_index,
                        "plot_type": "errorbar",
                        "x": L_centers[valid_indices],
                        "y": y_data[valid_indices],
                        "x_err": dL[valid_indices],
                        "y_err": y_err[valid_indices],
                        "label": label,
                        "xlabel": "L-shell",
                        "ylabel": "J",
                        "xscale": "linear",
                        "yscale": "log"
                    })
    return plot_data_list

# --- (Добавьте сюда _get_pitch_data, обновив его аналогично) ---

def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    gen = app_state.gen 
    plot_kind = app_state.plot_kind 

    if gen == 1: 
        if plot_kind == 1 or plot_kind == 2: 
            return _get_spectra_data(app_state, ax_index)
        elif plot_kind == 3: 
            # return _get_pitch_data(app_state, ax_index)
            pass
        elif plot_kind == 4: 
            return _get_radial_data(app_state, ax_index)
            
    return []
