"""
Модуль Обработки (Фаза 9 - FINAL DISTRIBUTION)
Реализует PlotKind 12: Гистограммы распределения потоков по виткам (из RBflux).
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime, timedelta
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e: return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- 1D PLOTS ---
def _generic_1d_plot(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; E_vals = app_state.e; val_name="E"; val_unit="GeV"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; E_vals = app_state.rig; val_name="R"; val_unit="GV"
    
    L_c = (L_edges[:-1]+L_edges[1:])/2; dL = (L_edges[1:]-L_edges[:-1])/2
    P_c = (P_edges[:-1]+P_edges[1:])/2; dP = (P_edges[1:]-P_edges[:-1])/2
    E_c = (E_edges[:-1]+E_edges[1:])/2; dE = (E_edges[1:]-E_edges[:-1])/2

    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, E_vals)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try: JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
            except: continue
            
            if mode == 'spectra': 
                iter1, iter2 = np.unique(L_idx), np.unique(P_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[i1, :, i2]; dy = dJJ[i1, :, i2]; n = NN[i1, :, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        l_lbl = f"[{L_edges[i1]:.2f}-{L_edges[i1+1]:.2f}]"
                        p_lbl = f"[{P_edges[i2]:.0f}-{P_edges[i2+1]:.0f}]"
                        lbl = f"L={l_lbl}, P={p_lbl}, D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar', 'x': E_c[mask], 'y': y[mask], 'x_err': dE[mask], 'y_err': dy[mask], 'label': lbl, 'xlabel': f"{val_name}, {val_unit}", 'ylabel': "Flux", 'xscale': 'log', 'yscale': 'log'})
            elif mode == 'radial':
                iter1, iter2 = np.unique(E_idx), np.unique(P_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[:, i1, i2]; dy = dJJ[:, i1, i2]; n = NN[:, i1, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        e_lbl = f"[{E_edges[i1]:.2f}-{E_edges[i1+1]:.2f}]"
                        p_lbl = f"[{P_edges[i2]:.0f}-{P_edges[i2+1]:.0f}]"
                        lbl = f"{val_name}={e_lbl}, P={p_lbl}, D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar', 'x': L_c[mask], 'y': y[mask], 'x_err': dL[mask], 'y_err': dy[mask], 'label': lbl, 'xlabel': "L-shell", 'ylabel': "Flux", 'xscale': 'linear', 'yscale': 'log'})
            elif mode == 'pitch':
                iter1, iter2 = np.unique(L_idx), np.unique(E_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[i1, i2, :]; dy = dJJ[i1, i2, :]; n = NN[i1, i2, :]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        l_lbl = f"[{L_edges[i1]:.2f}-{L_edges[i1+1]:.2f}]"
                        e_lbl = f"[{E_edges[i2]:.2f}-{E_edges[i2+1]:.2f}]"
                        lbl = f"L={l_lbl}, {val_name}={e_lbl}, D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar', 'x': P_c[mask], 'y': y[mask], 'x_err': dP[mask], 'y_err': dy[mask], 'label': lbl, 'xlabel': "Pitch (deg)", 'ylabel': "Flux", 'xscale': 'linear', 'yscale': 'log'})
    return plot_data_list

# --- 2D MAPS ---
def _generic_2d_map(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; val_name="E"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; val_name="R"
    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, app_state.e if app_state.ror_e==1 else app_state.rig)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        if app_state.fullday:
            try: JJ = data['Jday']
            except: continue
            if mode == 'l_pitch':
                for i_fix in np.unique(E_idx):
                    Z = JJ[:, i_fix, :].T 
                    e_lbl = f"[{E_edges[i_fix]:.2f}-{E_edges[i_fix+1]:.2f}]"
                    lbl = f"L-Pitch ({val_name}={e_lbl}), D={day_str}"
                    plot_data_list.append({'ax_index': ax_index, 'plot_type': 'pcolor', 'x': L_edges, 'y': P_edges, 'z': Z, 'label': lbl, 'xlabel': 'L', 'ylabel': 'Pitch', 'zlabel': 'Flux', 'zscale': 'log'})
            elif mode == 'e_pitch':
                for i_fix in np.unique(L_idx):
                    Z = JJ[i_fix, :, :].T 
                    l_lbl = f"[{L_edges[i_fix]:.2f}-{L_edges[i_fix+1]:.2f}]"
                    lbl = f"{val_name}-Pitch (L={l_lbl}), D={day_str}"
                    plot_data_list.append({'ax_index': ax_index, 'plot_type': 'pcolor', 'x': E_edges, 'y': P_edges, 'z': Z, 'label': lbl, 'xlabel': val_name, 'ylabel': 'Pitch', 'zlabel': 'Flux', 'xscale': 'log', 'zscale': 'log'})
            elif mode == 'e_l':
                for i_fix in np.unique(P_idx):
                    Z = JJ[:, :, i_fix] 
                    p_lbl = f"[{P_edges[i_fix]:.0f}-{P_edges[i_fix+1]:.0f}]"
                    lbl = f"{val_name}-L (P={p_lbl}), D={day_str}"
                    plot_data_list.append({'ax_index': ax_index, 'plot_type': 'pcolor', 'x': E_edges, 'y': L_edges, 'z': Z, 'label': lbl, 'xlabel': val_name, 'ylabel': 'L', 'zlabel': 'Flux', 'xscale': 'log', 'zscale': 'log'})
    return plot_data_list

# --- TEMPORAL & AUX ---
def _get_temporal_data(app_state, ax_index):
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; E_vals = app_state.e; val_name = "E"; val_unit = "GeV"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; E_vals = app_state.rig; val_name = "R"; val_unit = "GV"
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
        try: day_num = int(os.path.basename(infile).split('_')[1].split('.')[0]); current_date = base_date + timedelta(days=day_num)
        except: continue
        if app_state.fullday:
            try: JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
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
        l_lbl = f"[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}]"
        p_lbl = f"[{P_edges[p_idx]:.0f}-{P_edges[p_idx+1]:.0f}]"
        e_lbl = f"[{E_edges[e_idx]:.3f}-{E_edges[e_idx+1]:.3f}]"
        label = f"L={l_lbl}, P={p_lbl}, {val_name}={e_lbl} {val_unit}"
        combined = sorted(zip(trace_data['x'], trace_data['y'], trace_data['y_err']))
        x_s, y_s, err_s = zip(*combined)
        plot_data_list.append({"ax_index": ax_index, "plot_type": "errorbar", "x": x_s, "y": y_s, "y_err": err_s, "label": label, "xlabel": "Date", "ylabel": "Flux", "xscale": "linear", "yscale": "log"})
    return plot_data_list

def _get_auxiliary_data(app_state, ax_index):
    path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
    mat = _load_mat_file(path)
    if not mat: return []
    try:
        unixtime = np.array(mat['unixtime']).flatten()
        kp = np.array(mat['Kp']).flatten(); dst = np.array(mat['Dst']).flatten(); f10 = np.array(mat['f10p7']).flatten()
        if np.max(kp) > 9.0: kp = kp / 10.0
        if not app_state.pam_pers: return []
        start_day = app_state.pam_pers[0]; end_day = app_state.pam_pers[-1]
        base_unix = datetime(2005, 12, 31).timestamp()
        start_unix = base_unix + start_day * 86400; end_unix = base_unix + (end_day + 1) * 86400
        mask = (unixtime >= start_unix) & (unixtime <= end_unix)
        if not np.any(mask): return []
        t_data = [datetime.fromtimestamp(ts) for ts in unixtime[mask]]
        plots = []
        plots.append({"ax_index": ax_index, "plot_type": "errorbar", "x": t_data, "y": kp[mask], "label": "Kp Index", "xlabel": "Date", "ylabel": "Kp", "xscale": "linear", "yscale": "linear"})
        plots.append({"ax_index": ax_index, "plot_type": "errorbar", "x": t_data, "y": dst[mask], "label": "Dst (nT)", "xlabel": "Date", "ylabel": "Dst", "xscale": "linear", "yscale": "linear"})
        plots.append({"ax_index": ax_index, "plot_type": "errorbar", "x": t_data, "y": f10[mask], "label": "F10.7", "xlabel": "Date", "ylabel": "sfu", "xscale": "linear", "yscale": "linear"})
        return plots
    except Exception as e: print(f"Error Aux: {e}"); return []

# --- FLUX DISTRIBUTION (PlotKind 12) - FIXED ---

def _get_flux_distribution(app_state, ax_index):
    """
    Строит гистограмму распределения потоков по виткам.
    Использует стандартные файлы RBflux, извлекая данные из переменной J (массив витков).
    """
    # 1. Используем стандартные файлы RBflux
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    # 2. Индексы бинов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; E_vals = app_state.e; val_name="E"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; E_vals = app_state.rig; val_name="R"
    
    L_indices = np.unique(_find_bin_indices(L_edges, app_state.l))
    P_indices = np.unique(_find_bin_indices(P_edges, app_state.pitch))
    E_indices = np.unique(_find_bin_indices(E_edges, E_vals))
    
    # 3. Сбор статистики (key -> list of flux values)
    flux_collections = {} 
    
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        try:
            # В RBflux переменная J - это массив витков.
            # J[i] содержит матрицу потоков (3, 6, 16) для i-го витка.
            if not hasattr(mat, 'J'): continue
            
            J_passes = mat.J # Array of numpy arrays
            
            # Если J - это массив numpy, содержащий другие массивы (object array или просто многомерный)
            # В Python это обычно массив объектов
            
            for i_pass in range(len(J_passes)):
                pass_flux_matrix = J_passes[i_pass] 
                
                # Проверка: иногда бывают пустые витки или скаляры
                if np.isscalar(pass_flux_matrix) or pass_flux_matrix.size == 0: continue
                
                # Убедимся, что размерность совпадает с ожидаемой (L, E, P)
                # Например (3, 6, 16)
                if pass_flux_matrix.ndim != 3: continue
                
                for l_idx in L_indices:
                    for e_idx in E_indices:
                        for p_idx in P_indices:
                            if l_idx >= pass_flux_matrix.shape[0] or \
                               e_idx >= pass_flux_matrix.shape[1] or \
                               p_idx >= pass_flux_matrix.shape[2]: continue
                            
                            val = pass_flux_matrix[l_idx, e_idx, p_idx]
                            
                            # Фильтруем нули и NaN
                            if not np.isnan(val) and val > 0:
                                key = (l_idx, p_idx, e_idx)
                                if key not in flux_collections: flux_collections[key] = []
                                flux_collections[key].append(val)
                            
        except Exception as e:
            # print(f"Error extracting passages from {os.path.basename(fpath)}: {e}")
            pass

    # 4. Формируем гистограммы
    plot_data_list = []
    
    for key, fluxes in flux_collections.items():
        if len(fluxes) < 2: continue
        
        fluxes = np.array(fluxes)
        l_idx, p_idx, e_idx = key
        
        mean_val = np.mean(fluxes)
        std_val = np.std(fluxes)
        
        l_lbl = f"[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}]"
        p_lbl = f"[{P_edges[p_idx]:.0f}-{P_edges[p_idx+1]:.0f}]"
        e_lbl = f"[{E_edges[e_idx]:.2f}-{E_edges[e_idx+1]:.2f}]"
        
        label = (f"L={l_lbl}, P={p_lbl}, {val_name}={e_lbl}\n"
                 f"N={len(fluxes)}, Mean={mean_val:.2e}, Std={std_val:.2e}")
        
        plot_data_list.append({
            "ax_index": ax_index,
            "plot_type": "histogram",
            "x": fluxes,
            "label": label,
            "xlabel": "Flux (J)",
            "ylabel": "Counts (Passages)",
            "xscale": "linear", 
            "yscale": "linear",
            "bins": 50 
        })
        
    return plot_data_list

# --- MAIN DISPATCHER ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    pk = app_state.plot_kind 
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index, 'spectra')
    elif pk == 3: return _generic_1d_plot(app_state, ax_index, 'pitch')
    elif pk == 4: return _generic_1d_plot(app_state, ax_index, 'radial')
    elif pk == 5: return _get_temporal_data(app_state, ax_index)
    elif pk == 8: return _generic_2d_map(app_state, ax_index, 'l_pitch')
    elif pk == 9: return _generic_2d_map(app_state, ax_index, 'e_pitch')
    elif pk == 10: return _generic_2d_map(app_state, ax_index, 'e_l')
    elif pk == 11: return _get_auxiliary_data(app_state, ax_index)
    elif pk == 12: return _get_flux_distribution(app_state, ax_index) # <--- Fixed for RBflux
    return []
