"""
Модуль конфигурации (PROTOCOL INTERLEAVED)
Исправлено: Разделение Ebin на Energy (нечетные) и Rigidity (четные).
"""
import os
import numpy as np
from scipy.io import loadmat

# ... (пути остаются прежними)

def load_binning_info_direct():
    bininfo = { 
        'Lbin': [], 'pitchbin': [], 'Ebin': [], 'Rig': [],
        'Ecenters': [], 'Rigcenters': [], 'Lcenters': [], 'pitchcenters': [],
        'dE': [], 'dR': [], 'dL': [], 'dPitch': []
    }
    mat = loadmat(BINNING_INFO_FILE, squeeze_me=True, struct_as_record=False)
    if mat:
        # Границы L и Pitch - простые списки
        bininfo['Lbin'] = get_val(mat, 'Lbin')
        bininfo['pitchbin'] = get_val(mat, 'pitchbin')
        
        # Энергия и Жесткость - ЧЕРЕДУЮТСЯ
        ebin_raw = get_val(mat, 'Ebin')
        if ebin_raw is not None and ebin_raw.dtype == 'O':
            # Нечетные (1,3,5...) -> Энергия. В Python (0,2,4...)
            bininfo['Ebin'] = ebin_raw[0::2]
            # Четные (2,4,6...) -> Жесткость. В Python (1,3,5...)
            bininfo['Rig'] = ebin_raw[1::2]
        else:
            bininfo['Ebin'] = ebin_raw
            bininfo['Rig'] = ebin_raw # Fallback

        # Расчет параметров
        bininfo['Ecenters'], bininfo['dE'], _ = calculate_bin_params(bininfo['Ebin'], 'geometric')
        bininfo['Rigcenters'], bininfo['dR'], _ = calculate_bin_params(bininfo['Rig'], 'geometric')
        bininfo['Lcenters'], bininfo['dL'], _ = calculate_bin_params(bininfo['Lbin'], 'geometric')
        bininfo['pitchcenters'], bininfo['dPitch'], _ = calculate_bin_params(bininfo['pitchbin'], 'arithmetic')
    return bininfo
