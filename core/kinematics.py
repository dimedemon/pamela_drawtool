"""
Модуль Кинематики (Фаза 1)

Содержит функции для преобразования Энергии (T) в Жесткость (R) и обратно.
Портировано из ConvertT2R.m и ConvertR2T.m.
"""

import numpy as np

def convert_T_to_R(T, M, A, Z):
    """
    Конвертирует кинетическую энергию (T) в жесткость (R).
    Портировано из ConvertT2R.m.
    
    Args:
        T (float or np.ndarray): Кинетическая энергия в ГэВ (GeV)
        M (float or np.ndarray): Масса частицы в ГэВ/c^2 (GeV/c^2)
        A (float or np.ndarray): Массовое число (число нуклонов)
        Z (float or np.ndarray): Заряд
        
    Returns:
        float or np.ndarray: Жесткость в ГВ (GV)
    """
    A = np.where(A == 0, 1.0, A) # Защита от деления на ноль, как в оригинале
    R = (1.0 / Z) * (np.sqrt(np.power((A * T + M), 2) - np.power(M, 2)))
    return R

def convert_R_to_T(R, M, A, Z):
    """
    Конвертирует жесткость (R) в кинетическую энергию (T).
    Портировано из ConvertR2T.m.
    
    Args:
        R (float or np.ndarray): Жесткость в ГВ (GV)
        M (float or np.ndarray): Масса частицы в ГэВ/c^2 (GeV/c^2)
        A (float or np.ndarray): Массовое число (число нуклонов)
        Z (float or np.ndarray): Заряд
        
    Returns:
        float or np.ndarray: Кинетическая энергия в ГэВ (GeV)
    """
    A = np.where(A == 0, 1.0, A) # Защита от деления на ноль
    E = (1.0 / A) * (np.sqrt(np.power((Z * R), 2) + np.power(M, 2)) - M)
    return E
