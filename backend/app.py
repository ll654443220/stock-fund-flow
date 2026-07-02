from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from spider import StockFundFlowSpider, MockFundFlowData
import os
import time
import threading
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

spider = StockFundFlowSpider()

cache_data = None
cache_time = 0
cache_lock = threading.Lock()
CACHE_DURATION = 30


def get_cached_data():
    global cache_data, cache_time
    now = time.time()

    with cache_lock:
        if cache_data and (now - cache_time) < CACHE_DURATION:
            return cache_data

    try:
        data = fetch_real_data()
        with cache_lock:
            cache_data = data
            cache_time = time.time()
        return data
    except Exception as e:
        print(f"获取真实数据失败，使用模拟数据: {e}")
        data = MockFundFlowData.generate_mock_data()
        with cache_lock:
            cache_data = data
            cache_time = time.time()
        return data


def fetch_real_data():
    sectors = spider.get_sector_fund_flow()
    if not sectors:
        raise Exception("无数据")

    top_sectors = sectors[:15]
    bottom_sectors = sectors[-15:]
    selected_sectors = top_sectors + bottom_sectors

    sectors_data = []
    times = []

    for sector in selected_sectors:
        code = sector['code']
        secid = f'90.{code}'
        intraday = spider.get_intraday_fund_flow(secid)

        if intraday and intraday.get('times'):
            times = intraday['times']
            flow_data = [round(x / 100000000, 2) for x in intraday['main_net_inflow']]
        else:
            flow_data = [round(sector['main_net_inflow'] / 100000000, 2)]

        sectors_data.append({
            'name': sector['name'],
            'final_flow': round(sector['main_net_inflow'] / 100000000, 2),
            'flow_data': flow_data,
            'change_percent': sector.get('change_percent', 0),
        })

    sectors_data.sort(key=lambda x: x['final_flow'], reverse=True)

    now = datetime.now()
    return {
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M'),
        'is_trading': _is_trading_time(),
        'times': times,
        'sectors': sectors_data,
    }


def _is_trading_time():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    total_min = hour * 60 + minute

    morning_start = 9 * 60 + 30
    morning_end = 11 * 60 + 30
    afternoon_start = 13 * 60
    afternoon_end = 15 * 60

    return (morning_start <= total_min <= morning_end) or \
           (afternoon_start <= total_min <= afternoon_end)


@app.route('/api/fund-flow')
def fund_flow():
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    if use_mock:
        data = MockFundFlowData.generate_mock_data()
        return jsonify(data)

    data = get_cached_data()
    return jsonify(data)


@app.route('/api/sector-list')
def sector_list():
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    if use_mock:
        data = MockFundFlowData.generate_mock_data()
        sectors = [{'name': s['name'], 'final_flow': s['final_flow']} for s in data['sectors']]
        return jsonify({'sectors': sectors})

    sectors = spider.get_sector_fund_flow()
    result = [
        {
            'name': s['name'],
            'code': s['code'],
            'final_flow': round(s['main_net_inflow'] / 100000000, 2),
            'change_percent': s.get('change_percent', 0),
        }
        for s in sectors
    ]
    return jsonify({'sectors': result})


@app.route('/api/sector/<sector_code>')
def sector_detail(sector_code):
    history = spider.get_sector_fund_flow_history(sector_code)
    return jsonify({'history': history})


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
