"""
Модуль Обработки (Фаза 5 - FINAL LABELS)
Обеспечивает корректные подписи диапазонов [min-max] для L, Pitch, E, R
во всех типах графиков.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime, timedelta
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл не найден: {file_path}")
        return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e: print(f"Ошибка чтения .mat: {e}"); return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- ГЕНЕРАТОР 1D ГРАФИКОВ (Спектры, Радиальное, Питч) ---

def _generic_1d_plot(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    # 1. Загружаем границы бинов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: # Energy
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_vals = app_state.e
        val_name = "E"; val_unit = "GeV"
    else: # Rigidity
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_vals = app_state.rig
        val_name = "R"; val_unit = "GV"
    
    # Центры и ошибки (для осей)
    L_c = (L_edges[:-1]+L_edges[1:])/2; dL = (L_edges[1:]-L_edges[:-1])/2
    P_c = (P_edges[:-1]+P_edges[1:])/2; dP = (P_edges[1:]-P_edges[:-1])/2
    E_c = (E_edges[:-1]+E_edges[1:])/2; dE = (E_edges[1:]-E_edges[:-1])/2

    # Индексы выбранных пользователем бинов
    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, E_vals)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try:
                JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
            except: continue
            
            # === ТИП 1: СПЕКТРЫ (Ось X = E или R) ===
            if mode == 'spectra': 
                iter1, iter2 = np.unique(L_idx), np.unique(P_idx)
                for i1 in iter1: # Фиксируем L
                    for i2 in iter2: # Фиксируем Pitch
                        y = JJ[i1, :, i2]; dy = dJJ[i1, :, i2]; n = NN[i1, :, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        
                        # --- ИСПРАВЛЕНИЕ ПОДПИСЕЙ ---
                        l_lbl = f"[{L_edges[i1]:.2f}-{L_edges[i1+1]:.2f}]"
                        p_lbl = f"[{P_edges[i2]:.0f}-{P_edges[i2+1]:.0f}]"
                        
                        lbl = f"L={l_lbl}, P={p_lbl}, D={day_str}"
                        
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': E_c[mask], 'y': y[mask], 'x_err': dE[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': f"{val_name}, {val_unit}",
                            'ylabel': "Flux", 'xscale': 'log', 'yscale': 'log'})
                            
            # === ТИП 4: РАДИАЛЬНОЕ (Ось X = L) ===
            elif mode == 'radial':
                iter1, iter2 = np.unique(E_idx), np.unique(P_idx)
                for i1 in iter1: # Фиксируем E
                    for i2 in iter2: # Фиксируем Pitch
                        y = JJ[:, i1, i2]; dy = dJJ[:, i1, i2]; n = NN[:, i1, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        
                        # --- ИСПРАВЛЕНИЕ ПОДПИСЕЙ ---
                        e_lbl = f"[{E_edges[i1]:.2f}-{E_edges[i1+1]:.2f}]"
                        p_lbl = f"[{P_edges[i2]:.0f}-{P_edges[i2+1]:.0f}]"
                        
                        lbl = f"{val_name}={e_lbl}, P={p_lbl}, D={day_str}"
                        
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': L_c[mask], 'y': y[mask], 'x_err': dL[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': "L-shell", 'ylabel': "Flux",
                            'xscale': 'linear', 'yscale': 'log'})

            # === ТИП 3: ПИТЧ-УГЛОВОЕ (Ось X = Pitch) ===
            elif mode == 'pitch':
                iter1, iter2 = np.unique(L_idx), np.unique(E_idx)
                for i1 in iter1: # Фиксируем L
                    for i2 in iter2: # Фиксируем E
                        y = JJ[i1, i2, :]; dy = dJJ[i1, i2, :]; n = NN[i1, i2, :]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        
                        # --- ИСПРАВЛЕНИЕ ПОДПИСЕЙ ---
                        l_lbl = f"[{L_edges[i1]:.2f}-{L_edges[i1+1]:.2f}]"
                        e_lbl = f"[{E_edges[i2]:.2f}-{E_edges[i2+1]:.2f}]"
                        
                        lbl = f"L={l_lbl}, {val_name}={e_lbl}, D={day_str}"
                        
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': P_c[mask], 'y': y[mask], 'x_err': dP[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': "Pitch (deg)", 'ylabel': "Flux",
                            'xscale': 'linear', 'yscale': 'log'})

    return plot_data_list

# --- ГЕНЕРАТОР 2D КАРТ (PlotKind 8, 9, 10) ---

def _generic_2d_map(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: 
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_vals = app_state.e; val_name = "E"
    else: 
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_vals = app_state.rig; val_name = "R"
    
    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, E_vals)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try: JJ = data['Jday']
            except: continue
            
            # --- L vs Pitch (Fix E) ---
            if mode == 'l_pitch': 
                for i_fix in np.unique(E_idx):
                    Z = JJ[:, i_fix, :].T 
                    e_lbl = f"[{E_edges[i_fix]:.2f}-{E_edges[i_fix+1]:.2f}]"
                    lbl = f"L-Pitch Map ({val_name}={e_lbl}), D={day_str}"
                    
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': L_edges, 'y': P_edges, 'z': Z,
                        'label': lbl, 'xlabel': 'L', 'ylabel': 'Pitch', 'zlabel': 'Flux',
                        'xscale': 'linear', 'yscale': 'linear', 'zscale': 'log'
                    })

            # --- E vs Pitch (Fix L) ---
            elif mode == 'e_pitch': 
                for i_fix in np.unique(L_idx):
                    Z = JJ[i_fix, :, :].T 
                    l_lbl = f"[{L_edges[i_fix]:.2f}-{L_edges[i_fix+1]:.2f}]"
                    lbl = f"{val_name}-Pitch Map (L={l_lbl}), D={day_str}"
                    
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': E_edges, 'y': P_edges, 'z': Z,
                        'label': lbl, 'xlabel': val_name, 'ylabel': 'Pitch', 'zlabel': 'Flux',
                        'xscale': 'log', 'yscale': 'linear', 'zscale': 'log'
                    })
            
            # --- E vs L (Fix Pitch) ---
            elif mode == 'e_l': 
                for i_fix in np.unique(P_idx):
                    Z = JJ[:, :, i_fix] 
                    p_lbl = f"[{P_edges[i_fix]:.0f}-{P_edges[i_fix+1]:.0f}]"
                    lbl = f"{val_name}-L Map (P={p_lbl}), D={day_str}"
                    
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': E_edges, 'y': L_edges, 'z': Z,
                        'label': lbl, 'xlabel': val_name, 'ylabel': 'L', 'zlabel': 'Flux',
                        'xscale': 'log', 'yscale': 'linear', 'zscale': 'log'
                    })
    return plot_data_list

# --- ГЕНЕРАТОР ВРЕМЕННЫХ РЯДОВ (PlotKind 5) ---

def _get_temporal_data(app_state, ax_index):
    """
    Temporal variations (X=Date).
    """
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: 
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_vals = app_state.e; val_name = "E"; val_unit = "GeV"
    else: 
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_vals = app_state.rig; val_name = "R"; val_unit = "GV"
        
    L_indices = np.unique(_find_bin_indices(L_edges, app_state.l))
    P_indices = np.unique(_find_bin_indices(P_edges, app_state.pitch))
    E_indices = np.unique(_find_bin_indices(E_edges, E_vals))
    
    traces = {}
    for l in L_indices:
        for p in P_indices:
            for e in E_indices:
                traces[(l,p,e)] = {'x': [], 'y': [], 'y_err': []}

    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []
    
    base_date = datetime(2005, 12, 31)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try:
            day_num = int(os.path.basename(infile).split('_')[1].split('.')[0])
            current_date = base_date + timedelta(days=day_num)
        except: continue

        if app_state.fullday:
            try:
                JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
            except: continue
            
            for l_idx in L_indices:
                for e_idx in E_indices:
                    for p_idx in P_indices:
                        if l_idx >= JJ.shape[0] or e_idx >= JJ.shape[1] or p_idx >= JJ.shape[2]: continue
                        if NN[l_idx, e_idx, p_idx] > app_state.n_min:
                            key = (l_idx, p_idx, e_idx)
                            traces[key]['x'].append(current_date)
                            traces[key]['y'].append(JJ[l_idx, e_idx, p_idx])
                            traces[key]['y_err'].append(dJJ[l_idx, e_idx, p_idx])
    
    plot_data_list = []
    for key, trace_data in traces.items():
        if not trace_data['x']: continue
        l_idx, p_idx, e_idx = key
        
        # --- ИСПРАВЛЕНИЕ ПОДПИСЕЙ ---
        l_lbl = f"[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}]"
        p_lbl = f"[{P_edges[p_idx]:.0f}-{P_edges[p_idx+1]:.0f}]"
        e_lbl = f"[{E_edges[e_idx]:.3f}-{E_edges[e_idx+1]:.3f}]"
        
        label = f"L={l_lbl}, P={p_lbl}, {val_name}={e_lbl} {val_unit}"
        
        combined = sorted(zip(trace_data['x'], trace_data['y'], trace_data['y_err']))
        x_s, y_s, err_s = zip(*combined)
        
        plot_data_list.append({
            "ax_index": ax_index, "plot_type": "errorbar",
            "x": x_s, "y": y_s, "y_err": err_s,
            "label": label, "xlabel": "Date", "ylabel": "Flux",
            "xscale": "linear", "yscale": "log"
        })

    return plot_data_list

# --- MAIN DISPATCHER ---

def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    pk = app_state.plot_kind 
    
    # 1D Plots
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index, 'spectra')
    elif pk == 3: return _generic_1d_plot(app_state, ax_index, 'pitch')
    elif pk == 4: return _generic_1d_plot(app_state, ax_index, 'radial')
    
    # Temporal
    elif pk == 5: return _get_temporal_data(app_state, ax_index)
    
    # 2D Maps
    elif pk == 8: return _generic_2d_map(app_state, ax_index, 'l_pitch')
    elif pk == 9: return _generic_2d_map(app_state, ax_index, 'e_pitch')
    elif pk == 10: return _generic_2d_map(app_state, ax_index, 'e_l')
    
    return []
