"""
Модуль Обработки (Фаза 1) - ИСПРАВЛЕННЫЙ

Содержит всю научную логику для загрузки данных,
обработки и подготовки к построению графиков.
(Портирует DrawSpectra.m, DrawRadial.m, и т.д.)
"""

import os
import numpy as np
from scipy.io import loadmat
from . import config  # Наш config с биннингами
from . import state   # Наш app_state

def _load_mat_file(file_path):
    """Общая функция-загрузчик .mat файлов."""
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл данных не найден: {file_path}")
        return None
    try:
        # struct_as_record=False важен для доступа к .mat как к объектам
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Ошибка при чтении .mat файла ({file_path}): {e}")
        return None

def _build_data_path(app_state: state.ApplicationState):
    """
    Воссоздает логику построения пути к файлам данных
    из Draw*.m скриптов.
    """
    
    # --- ИСПРАВЛЕНИЕ: Используем .ror_e, .eb, .pitchb, .lb ---
    
    # Определяем 'er' (E или R биннинг)
    if app_state.ror_e == 2: # 1=E, 2=R
        er = f"R{app_state.eb}"
    else:
        er = f"E{app_state.eb}"

    # v09 -> 9.0
    version_float = float(app_state.flux_version.replace('v', ''))

    if version_float < 5.0:
        # Старый формат stdbinning
        binningpath = f"stdbinning{app_state.pitchb}{app_state.lb}e{app_state.eb}" # Упрощено
    else:
        # Новый формат
        binningpath = f"stdbinning_P{app_state.pitchb}L{app_state.lb}{er}"

    # --- ИСПРАВЛЕНИЕ: Используем .tbin ---
    if app_state.tbin == 'Separate Periods':
        FCpath = 'RBfullfluxes'
    else:
        FCpath = f"RB{app_state.tbin}fluxes"

    inpath = os.path.join(config.GEN_PATH, 'Loc', app_state.flux_version,
                          app_state.selection, binningpath, FCpath)
    
    return inpath

def _find_bin_indices(edges, values):
    """
    Находит индексы бинов для заданных значений.
    """
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
        
    # searchsorted - быстрый бинарный поиск
    indices = np.searchsorted(edges, values, side='right') - 1
    
    # Обработка крайних случаев
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    
    return indices

def _get_spectra_data(app_state: state.ApplicationState, ax_index: int):
    """
    Портированная логика из DrawSpectra.m
    Возвращает список словарей с данными для построения.
    """
    
    plot_data_list = []
    base_path = _build_data_path(app_state)
    
    # --- ИСПРАВЛЕНИЕ: .lb, .pitchb, .ror_e, .eb ---
    
    # Получаем нужные бины из config
    # (индексы в Python начинаются с 0, в MATLAB с 1)
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

    # --- ИСПРАВЛЕНИЕ: .l, .pitch, .pam_pers, .tbin, .period ---
    
    # Находим индексы L и pitch
    L_indices = _find_bin_indices(L_edges, app_state.l)
    pitch_indices = _find_bin_indices(pitch_edges, app_state.pitch)
    
    # --- ИСПРАВЛЕНИЕ: Используем .pam_pers ---
    periods = app_state.pam_pers 
    
    if app_state.tbin == 'Separate Periods':
        periods = [app_state.period] # один файл
    else:
        # TODO: Логика для PamPers (списка дней)
        # ВРЕМЕННАЯ ЗАГЛУШКА:
        if not periods: # Если список пустой, используем хардкод
            print("ВНИМАНИЕ: app_state.pam_pers пуст. Используется [200] для теста.")
            periods = [200] # Хардкодим 200-й день для теста
        else:
            print(f"Используются дни/периоды: {periods}")
        

    # --- Цикл по периодам (дням) ---
    for period in periods:
        infile = os.path.join(base_path, f"RBflux_{period}.mat")
        data = _load_mat_file(infile)
        if data is None:
            print(f"Не удалось загрузить файл: {infile}")
            continue
            
        # Загрузка данных (Jday, J, numevday, numevu...)
        
        # --- ИСПРАВЛЕНИЕ: .fullday ---
        if app_state.fullday: 
            
            try:
                JJ = data['Jday']
                dJJ = data['dJday']
                NN = data['numevday']
            except KeyError as e:
                print(f"ОШИБКА: В файле .mat отсутствует ключ: {e}")
                # Возвращаем пустой список, если данные не найдены
                return []
            
            # --- Цикл по L-бинам ---
            for l_idx in np.unique(L_indices):
                # --- Цикл по Pitch-бинам ---
                for p_idx in np.unique(pitch_indices):
                    
                    # Извлечение данных (J(L, R, P))
                    y_data = JJ[l_idx, :, p_idx]
                    y_err = dJJ[l_idx, :, p_idx]
                    n_events = NN[l_idx, :, p_idx]
                    
                    # --- ИСПРАВЛЕНИЕ: .n_min ---
                    valid_indices = (n_events > app_state.n_min)
                    
                    if not np.any(valid_indices):
                        continue
                        
                    # Создание лейбла
                    label = (f"L=[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}], "
                             f"P=[{pitch_edges[p_idx]:.0f}-{pitch_edges[p_idx+1]:.0f}] deg, "
                             f"Day={period}")
                    
                    # --- ИСПРАВЛЕНИЕ: .units ---
                    # Упаковка данных для графика
                    plot_data_list.append({
                        "ax_index": ax_index,
                        "plot_type": "errorbar",
                        "x": x_data[valid_indices],
                        "y": y_data[valid_indices],
                        "x_err": dx_data[valid_indices],
                        "y_err": y_err[valid_indices],
                        "label": label,
                        "xlabel": x_label,
                        "ylabel": "J, (GeV m^2 Sr s)^-1" if app_state.units == 1 else "J, (MeV cm^2 Sr s)^-1",
                        "xscale": "log",
                        "yscale": "log"
                    })
        
        else:
            # --- ИСПРАВЛЕНИЕ: .fullday ---
            print("ВНИМАНИЕ: Логика для 'passes' (fullday=False) еще не реализована.")
            # ... (здесь должна быть логика для 'passes' (не fullday)) ...
            pass

    return plot_data_list


def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    """
    Главная функция-диспетчер.
    """
    
    # --- ИСПРАВЛЕНИЕ: .gen, .plot_kind ---
    gen = app_state.gen # 1 = PAMELA, 4 = External, 5 = Model...
    plot_kind = app_state.plot_kind # 1 = E spectra, 2 = R spectra...

    if gen == 1: # PAMELA exp. data
        if plot_kind == 1 or plot_kind == 2: # Energy/Rigidity spectra
            return _get_spectra_data(app_state, ax_index)
        
        elif plot_kind == 3: # pitch-angular
            pass
        elif plot_kind == 4: # Radial
            pass
        # ...
        
    elif gen == 4: # External exp. data
        pass
    
    elif gen == 5: # Empyrical models
        pass

    # Возвращаем пустой список, если тип графика не реализован
    return []
