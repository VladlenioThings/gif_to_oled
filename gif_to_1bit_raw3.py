#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageStat
import argparse

# === Аргументы ===
parser = argparse.ArgumentParser(description="Конвертация GIF в 1-битный RAW для Arduino (без PNG, с авто-порогом)")
parser.add_argument("--input", required=True, help="Входной GIF")
parser.add_argument("--output", required=True, help="Выходной RAW файл")
parser.add_argument("--mode", required=True, choices=["fit","stretch"], help="fit = сохранять пропорции, stretch = растянуть")
parser.add_argument("--invert", action="store_true", help="Инвертировать цвета")
parser.add_argument("--threshold", type=int, help="Порог для ч/б (0..255). Если не указан, определяется автоматически")
args = parser.parse_args()

INPUT_GIF = args.input
OUTPUT_RAW = args.output
MODE = args.mode
INVERT = args.invert
THRESHOLD = args.threshold

FRAME_WIDTH = 128
FRAME_HEIGHT = 64

# === Разворот бит ===
def reverse_bits(byte):
    byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    return byte

# === 1. Чтение кадров GIF ===
print("[1/4] Чтение кадров GIF...")
img = Image.open(INPUT_GIF)
frames = []
delays = []

i = 0
while True:
    try:
        img.seek(i)
        frame = img.convert("L")  # grayscale
        frames.append(frame.copy())
        delays.append(img.info.get("duration", 0))
        i += 1
    except EOFError:
        break

frame_count = len(frames)
if frame_count == 0:
    raise RuntimeError("Не удалось прочитать кадры из GIF")

# === 2. Авто-порог, если не указан ===
if THRESHOLD is None:
    all_pixels = []
    for frame in frames:
        stat = ImageStat.Stat(frame)
        all_pixels.append(stat.mean[0])
    THRESHOLD = int(sum(all_pixels)/len(all_pixels))
    print(f"Авто-порог определён как {THRESHOLD}")

# === 3. Конвертация в 1-битный RAW ===
print(f"[2/4] Конвертация {frame_count} кадров в {OUTPUT_RAW}...")
with open(OUTPUT_RAW, "wb") as fout:
    for frame in frames:
        
        
        if MODE == "fit":
            # создаём пустой кадр нужного размера
            out_frame = Image.new("L", (FRAME_WIDTH, FRAME_HEIGHT), 0)
            src_w, src_h = frame.size

            # вычисляем коэффициент масштабирования, не увеличиваем
            scale = min(FRAME_WIDTH / src_w, FRAME_HEIGHT / src_h, 1.0)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)

            # масштабируем исходный кадр
            tmp = frame.resize((new_w, new_h), Image.Resampling.NEAREST)

            # центрируем в out_frame
            ox = (FRAME_WIDTH - new_w) // 2
            oy = (FRAME_HEIGHT - new_h) // 2
            out_frame.paste(tmp, (ox, oy))

        else:
            # stretch: растягиваем на весь экран
            out_frame = frame.resize((FRAME_WIDTH, FRAME_HEIGHT), Image.Resampling.NEAREST)

        # конвертация в 1-битный RAW
        for y in range(FRAME_HEIGHT):
            for x_byte in range(FRAME_WIDTH // 8):
                byte = 0
                for bit in range(8):
                    px = out_frame.getpixel((x_byte*8 + bit, y))
                    bit_val = px > THRESHOLD
                    if INVERT:
                        bit_val = not bit_val
                    if bit_val:
                        byte |= (1 << (7 - bit))
                byte = reverse_bits(byte)
                fout.write(byte.to_bytes(1, "little"))

# === 4. Создание delays.txt ===
print("[3/4] Создание delays.txt...")
delays_file = os.path.splitext(OUTPUT_RAW)[0] + "_delays.txt"

unique_delays = sorted(set(delays))
average_delay = sum(delays) / len(delays)

if len(unique_delays) == 1:
    content = f"{unique_delays[0]}\n"
else:
    content_lines = [
        f"# Среднее время кадра: {average_delay:.2f} мс",
        f"# Встречаются тайминги: {', '.join(str(d) for d in unique_delays)}",
        "\n".join(str(d) for d in delays)
    ]
    content = "\n".join(content_lines) + "\n"

with open(delays_file, "w") as f:
    f.write(content)

# === Итог ===
print("[4/4] Готово!")
print(f"Файл RAW: {OUTPUT_RAW} ({frame_count} кадров)")
print(f"Файл задержек: {delays_file}")
print(f"Режим: {MODE}, инверсия: {'да' if INVERT else 'нет'}, порог: {THRESHOLD}")
