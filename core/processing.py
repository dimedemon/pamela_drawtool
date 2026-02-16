"""
Модуль Обработки (SPREAD & TAILS ANALYSIS)
Задача: Восстановить разброс потоков в одной ячейке L-P-E за период.
"""
import os
import numpy as np
import warnings
from . import config
from . import file_manager

# ... (вспомогательные функции остаются прежними)

def _get_flux_histogram_data(app_state, ax_index):
    """Сбор N vs Flux для анализа хвостов и разброса."""
    print(f"\n[PROCESSING] -> Анализ стабильности потока в ячейке...")

    try:
        # Безопасное получение индексов (защита от IndexError)
        idx_L = min(app_state.lb - 1, len(config.BIN_INFO['Lbin']) - 1)
        idx_P = min(app_state.pitchb - 1, len(config.BIN_INFO['pitchbin']) - 1)
        
        # Выбираем набор бинов E или R
        if app_state.ror_e == 1:
            bin_set = config.BIN_INFO['Ebin']
            idx_E_config = min(app_state.eb - 1, len(bin_set) - 1)
        else:
            bin_set = config.BIN_INFO['Rig']
            idx_E_config = min(app_state.eb - 1, len(bin_set) - 1)

        # Находим конкретную ячейку (индексы внутри выбранного биннинга)
        l_idx = _find_bin_indices(config.BIN_INFO['Lbin'][idx_L], app_state.l)[0]
        p_idx = _find_bin_indices(config.BIN_INFO['pitchbin'][idx_P], app_state.pitch)[0]
        e_idx = _find_bin_indices(bin_set[idx_E_config], app_state.e)[0]
    except Exception as e:
        print(f"[ERROR] Ошибка доступа к бинам: {e}")
        return []

    files = file_manager.get_input_filenames(app_state, 'flux')
    flux_samples = []
    error_samples = []

    for fpath in files:
        mat = _load_mat_file(fpath)
        if not mat: continue
        
        # Jday(L, E, P)
        j_data = mat.get('Jday', mat.get('J'))
        dj_data = mat.get('dJday', mat.get('dJ'))
        
        if j_data is not None:
            try:
                val = j_data[l_idx, e_idx, p_idx]
                if val > 0 and not np.isnan(val):
                    flux_samples.append(val)
                    if dj_data is not None: error_samples.append(dj_data[l_idx, e_idx, p_idx])
            except: continue

    if not flux_samples: return []

    # Статистика для сравнения разброса
    real_std = np.std(flux_samples)
    stat_err_mean = np.mean(error_samples) if error_samples else 0

    return [{
        "ax_index": ax_index,
        "plot_type": "histogram",
        "x": np.array(flux_samples),
        "bins": 15, # Для 10 дней 15 бинов оптимально
        "xlabel": "Flux Intensity (Raw Units)",
        "ylabel": "N (Frequency)",
        "yscale": "log", # Для изучения "хвостов"
        "title": f"Spread: Real Sigma={real_std:.2e} | Stat Error={stat_err_mean:.2e}",
        "label": f"Cell (L={app_state.l}, P={app_state.pitch}, E={app_state.e})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [0, 1]: return _get_spectra_data(app_state, ax_index)
    if pk == 6: return _get_flux_histogram_data(app_state, ax_index) # Режим гистограммы
    return []
