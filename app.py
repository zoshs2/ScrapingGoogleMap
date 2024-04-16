import os
import time
import argparse
from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# NOTE: 기본적으로 구글맵을 동작시키는 JS 스크립트(map.html)가 templates 폴더 안에 있어야 한다.
app = Flask(__name__, template_folder='templates')

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', type=str)
parser.add_argument('--lat', type=str)
parser.add_argument('--lon', type=str)
parser.add_argument('-z', '--zoom', type=str)
parser.add_argument('-b', '--basepath', type=str, help='Basepath for saving')
parser.add_argument('-d', '--dirpath', type=str, help='Sub-directory name for saving')
parser.add_argument('--ts', type=str, help='Time stamp(String) for a given city')
parser.add_argument('-v', '--visible', type=str)
args = parser.parse_args()
port_num = args.port

# NOTE: ~/.bashrc_profile에 환경변수 미리 설정해둘 것
my_api_key = os.environ.get('GOOGLE_API_KEY') 

SavingDir = os.path.join(f'{args.basepath}', f'{args.dirpath}')
if os.path.exists(SavingDir) == False:
    os.mkdir(f"{SavingDir}")

visible_button = 'on' if args.visible == '0' else 'off'

# NOTE: Raw file Name
filename = f'Gmap_TrafficLayer_Raw_{args.dirpath}_{args.ts}.png'
savepath = os.path.join(SavingDir, filename)

@app.route('/')
def index():
    return render_template('map.html', lat=args.lat, lon=args.lon, zoom=args.zoom, api_key=my_api_key, visible=visible_button)

@app.route('/get_screenshot')
def get_screenshot():
    url = f'http://localhost:{port_num}'

    # Open another headless browser with height extracted above
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,816")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.binary_location = os.path.join(os.getcwd(), 'chrome-linux64/chrome')
    chrome_service = Service(os.path.join(os.getcwd(), 'chromedriver-linux64/chromedriver'))
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    driver.get(url)
    # pause 3 second to let page loads
    time.sleep(10)
    
    # save screenshot
    driver.save_screenshot(savepath)
    driver.close()
    return "<p>Successfully Saved.</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port_num, debug=True)