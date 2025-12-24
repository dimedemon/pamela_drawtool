import os
import scipy.io

# 1. Вычисляем путь так же, как в конфиге
current_dir = os.path.dirname(os.path.abspath(__file__))
# Если запускаем из корня, data должна быть тут
path_v1 = os.path.join(current_dir, 'data', 'BinningInfo.mat')
# Если запускаем из core, надо подняться
path_v2 = os.path.join(current_dir, '..', 'data', 'BinningInfo.mat')

print(f"Текущая папка запуска: {os.getcwd()}")
print(f"Проверяем путь 1: {path_v1} -> {os.path.exists(path_v1)}")
print(f"Проверяем путь 2: {path_v2} -> {os.path.exists(path_v2)}")

real_path = path_v1 if os.path.exists(path_v1) else (path_v2 if os.path.exists(path_v2) else None)

if real_path:
    print(f"\nФайл найден: {real_path}")
    try:
        mat = scipy.io.loadmat(real_path, squeeze_me=True, struct_as_record=False)
        print("Файл загружен успешно!")
        print("Ключи внутри:", [k for k in mat.keys() if not k.startswith('_')])
        
        # Проверяем Lbin
        if hasattr(mat, 'Lbin'):
            print("✅ Lbin найден как атрибут!")
        elif 'Lbin' in mat:
            print("✅ Lbin найден как ключ словаря!")
        else:
            print("❌ Lbin ОТСУТСТВУЕТ в файле!")
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
else:
    print("\n❌ ФАЙЛ BINNINGINFO.MAT НЕ НАЙДЕН НИ ПО ОДНОМУ ПУТИ!")
    print("Положите файл в папку 'data' в корне проекта.")
