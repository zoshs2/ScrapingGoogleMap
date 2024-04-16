import subprocess
import time
from datetime import datetime
import requests
import pytz
from pytz import country_timezones, timezone
import os
import cv2
import imutils
import numpy as np
import argparse
import sys
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--city', required=True, type=str, help='City name to refer the current time in city')
parser.add_argument('-p', '--port', default='1993', type=str, help='Port number for request')
parser.add_argument('--lat', required=True, type=float, help='Latitude')
parser.add_argument('--lon', required=True, type=float, help='Longitude')
parser.add_argument('-z', '--zoom', required=True, type=float, help='Zoom level')
args = parser.parse_args()

city_name = args.city.lower()
temp = []
for c in city_name.split('_'):
    temp.append(c[0].upper() + c[1:])
city_name = '_'.join(temp)
port_num = args.port

# =============================================================================================================
# ========================================= INPUT ARGUMENTS INSPECTION ========================================
try:
    port_num_int = int(port_num)
    if len(port_num) != 4:
        raise ValueError

except:
    print(f"WRONG PORT!!! 4-digits number needed for port, but given '{port_num}'.")
    sys.exit()

def find_city(query):
    for country, cities in country_timezones.items():
        for city in cities:
            if query in city:
                yield timezone(city)

for tz in find_city(city_name):
    pass

try:
    print(f"Given a '{city_name}', timezone(pytz tz) found: {tz}.")
except:
    print("Check again your city name of interest. Failed.")
    print("Available timezones in pytz:: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568")
    sys.exit()

sys.stdout.flush()
# ===========================================================================================================

# Setting the interested timezone
city_dir_name = tz.zone.split('/')[1]

# NOTE!! BasePath 위치 재확인할 것 (현재는 우리 서버 내 데이터 스토리지에 저장되도록 설정)
BasePath = '/home/data/GMAP_TRAFFIC'
RawSavingDir = os.path.join(BasePath, f'{city_dir_name}')
if os.path.exists(RawSavingDir) == False:
    os.mkdir(f"{RawSavingDir}")

# Initialize the number of snapshots.
snap_cnt = 0

def trim_whitespace(filepath):
    image_array = cv2.imread(filepath)
    # RGB(BGR) 상관없이 whitespace 는 (255, 255, 255)임.
    # (255, 255, 255) - 흰색이 아닌 영역의 인덱스들을 서칭.
    non_white_indices = np.where(np.any(image_array != [255, 255, 255], axis=-1))

    # 해당 영역의 상하 및 좌우로 최소최대 인덱스를 bounding box (bbox)로 함.
    bbox = (np.min(non_white_indices[0]), np.min(non_white_indices[1]),
            np.max(non_white_indices[0]), np.max(non_white_indices[1]))

    # Crop the image using the bounding box (bbox).
    cropped_image_array = image_array[bbox[0]:bbox[2]+1, bbox[1]:bbox[3]+1]

    return cropped_image_array

def ScreenShot(cmd, port):
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(10)
    res = requests.get(f'http://localhost:{port}/get_screenshot')
    time.sleep(10)
    process.terminate()
    process.wait()
    return

# Define the command to run
base_command = f"python app.py -p {port_num} --lat {args.lat} --lon {args.lon} -z {args.zoom} -b {BasePath} -d {city_dir_name}"

while True:
    if snap_cnt >= 6050:
        # 최소 브레이크 포인트 장치
        # 5분 단위 > 하루 288장 > 3주(21일) 동작 예정 > 총 6048장
        break

    current_time = datetime.now(tz)
    if int(current_time.strftime("%M")) % 5 == 0:
        time_prefix = current_time.strftime("%Y%m%d_%H%M")
        if snap_cnt == 0:
            original_command = base_command + f" --ts origin -v {snap_cnt}"
            ScreenShot(original_command, port_num)

        timely_command = base_command + f" --ts {time_prefix} -v 1"
        ScreenShot(timely_command, port_num)

        snap_cnt += 1
        print(f"{city_name.upper():=^50}")
        print(f">>>>> SUCCESSFULLY CAPTURE THE GOOGLE MAP.")
        sys.stdout.flush()

        origin_err_flag = False
        visual_on_path = os.path.join(RawSavingDir, f'Gmap_TrafficLayer_Raw_{city_dir_name}_origin.png')
        rawfile_path = os.path.join(RawSavingDir, f'Gmap_TrafficLayer_Raw_{city_dir_name}_{time_prefix}.png')
        bgr_clean_cropped = trim_whitespace(rawfile_path)
        rgb_clean_cropped = cv2.cvtColor(bgr_clean_cropped, cv2.COLOR_BGR2RGB)
        origin_clean_cropped = cv2.cvtColor(trim_whitespace(visual_on_path), cv2.COLOR_BGR2RGB)

        if rgb_clean_cropped.shape != (800, 800, 3):
            print(">>>>> FATAL ERROR:: INCONSISTENT RESOLUTION. SKIPPED THE PROCESSING OF THE FILE BELOW.")
            print(f"{rawfile_path}")
            print(f"SKIPPED RESOLUTION: {rgb_clean_cropped.shape}")
            sys.stdout.flush()
            time.sleep(60)
            continue

        if origin_clean_cropped.shape != (800, 800, 3):
            print(">>>>> ANNOYING ERROR:: ALL-FEATURED GOOGLE MAP HAS INCONSISTENT RESOLUTION.")
            print(f"{visual_on_path}")
            print(f"TRIMMED ORIGIN RESOLUTION: {origin_clean_cropped.shape}")
            origin_err_flag = True
            sys.stdout.flush()
        
        print(">>>>> SUCCESSFULLY PASS THE RESOLUTION (800px X 800px). ")
        print("DELETE THE ORIGINAL RAW FILE...", end='\n\n')
        try:
            os.remove(rawfile_path)
            if not origin_err_flag:
                os.remove(visual_on_path)
            time.sleep(5)
        except OSError as e:
            print(">>>>> BRUTAL EXCEPTION:: YOU TRIED TO DELETE THE NOT-EXISTED FILE.")
            sys.stdout.flush()
        
        rgb_img = Image.fromarray(rgb_clean_cropped, mode='RGB')
        rgb_img.save(rawfile_path)
        if not origin_err_flag:
            rgb_origin = Image.fromarray(origin_clean_cropped, mode='RGB')
            rgb_origin.save(visual_on_path)

        print(">>>>> SUCCESSFULLY SAVE WITH THE CLEAN RGB IMAGE !!!")
        print(f"NUMBER OF RESULTS ON THIS JOB:: {snap_cnt:,}", end='\n\n\n')
        sys.stdout.flush()
        time.sleep(60) # 적어도 1분이 지나고 나서, 다시 loop 를 돌도록 하자. 