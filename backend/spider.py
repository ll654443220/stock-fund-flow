import requests
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional


class StockFundFlowSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://data.eastmoney.com/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_sector_fund_flow(self) -> List[Dict]:
        url = 'https://push2.eastmoney.com/api/qt/clist/get'
        params = {
            'pn': '1',
            'pz': '50',
            'po': '1',
            'np': '1',
            'ut': 'b2884a393a59ad64002292a3e90d46a5',
            'fltt': '2',
            'invt': '2',
            'fid': 'f62',
            'fs': 'm:90+t:2',
            'fields': 'f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124',
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('data') and data['data'].get('diff'):
                return self._parse_sector_data(data['data']['diff'])
        except Exception as e:
            print(f"获取板块资金流向失败: {e}")

        return []

    def _parse_sector_data(self, diff_list: List[Dict]) -> List[Dict]:
        sectors = []
        for item in diff_list:
            sector = {
                'code': item.get('f12', ''),
                'name': item.get('f14', ''),
                'price': item.get('f2', 0),
                'change_percent': item.get('f3', 0),
                'main_net_inflow': item.get('f62', 0),
                'main_net_inflow_ratio': item.get('f184', 0),
                'super_large_net_inflow': item.get('f66', 0),
                'super_large_net_inflow_ratio': item.get('f69', 0),
                'large_net_inflow': item.get('f72', 0),
                'large_net_inflow_ratio': item.get('f75', 0),
                'medium_net_inflow': item.get('f78', 0),
                'medium_net_inflow_ratio': item.get('f81', 0),
                'small_net_inflow': item.get('f84', 0),
                'small_net_inflow_ratio': item.get('f87', 0),
                'total_market_cap': item.get('f124', 0),
            }
            sectors.append(sector)
        return sectors

    def get_sector_fund_flow_history(self, sector_code: str) -> List[Dict]:
        url = 'https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get'
        params = {
            'lmt': '0',
            'klt': '101',
            'secid': f'90.{sector_code}',
            'fields1': 'f1,f2,f3,f7',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65',
            'ut': 'b2884a393a59ad64002292a3e90d46a5',
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('data') and data['data'].get('klines'):
                return self._parse_history_data(data['data']['klines'])
        except Exception as e:
            print(f"获取板块历史资金流向失败: {e}")

        return []

    def _parse_history_data(self, klines: List[str]) -> List[Dict]:
        history = []
        for line in klines:
            parts = line.split(',')
            if len(parts) >= 13:
                history.append({
                    'date': parts[0],
                    'main_net_inflow': float(parts[1]),
                    'super_large_net_inflow': float(parts[2]),
                    'large_net_inflow': float(parts[3]),
                    'medium_net_inflow': float(parts[4]),
                    'small_net_inflow': float(parts[5]),
                    'main_net_inflow_ratio': float(parts[6]),
                    'super_large_ratio': float(parts[7]),
                    'large_ratio': float(parts[8]),
                    'medium_ratio': float(parts[9]),
                    'small_ratio': float(parts[10]),
                    'close_price': float(parts[11]),
                    'change_percent': float(parts[12]),
                })
        return history

    def get_intraday_fund_flow(self, secid: str) -> Dict:
        url = 'https://push2.eastmoney.com/api/qt/stock/fflow/kline/get'
        params = {
            'lmt': '0',
            'klt': '1',
            'secid': secid,
            'fields1': 'f1,f2,f3,f7',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
            'ut': 'b2884a393a59ad64002292a3e90d46a5',
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('data') and data['data'].get('klines'):
                return self._parse_intraday_data(data['data']['klines'], data['data'])
        except Exception as e:
            print(f"获取日内资金流向失败: {e}")

        return {}

    def _parse_intraday_data(self, klines: List[str], meta: Dict) -> Dict:
        times = []
        main_net = []
        super_large = []
        large = []
        medium = []
        small = []

        for line in klines:
            parts = line.split(',')
            if len(parts) >= 6:
                times.append(parts[0])
                main_net.append(float(parts[1]))
                super_large.append(float(parts[2]))
                large.append(float(parts[3]))
                medium.append(float(parts[4]))
                small.append(float(parts[5]))

        return {
            'name': meta.get('name', ''),
            'times': times,
            'main_net_inflow': main_net,
            'super_large_net_inflow': super_large,
            'large_net_inflow': large,
            'medium_net_inflow': medium,
            'small_net_inflow': small,
        }


class MockFundFlowData:
    SECTORS = [
        '有色金属', '人形机器人', '电力', '锂矿', '网络游戏', '煤炭',
        '创新药', '银行Ⅱ', '电网设备', '白酒', 'AI应用', '化工',
        '光学光电子', '电力设备', '锂电池', '证券', '半导体设备', 'MLCC',
        '商业航天', '储能', '消费电子', '玻璃基板', '液冷服务器', '光纤',
        'PCB', '算力租赁', '人工智能', 'CPO', '半导体', '存储芯片', '通信技术'
    ]

    @classmethod
    def generate_mock_data(cls) -> Dict:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        is_trading = False
        if (current_hour == 9 and current_minute >= 30) or (current_hour == 10) or \
           (current_hour == 11 and current_minute <= 30) or \
           (current_hour >= 13 and current_hour < 15) or \
           (current_hour == 11 and current_minute > 30 and current_minute < 60):
            is_trading = True

        times = cls._generate_time_points()
        sectors_data = []

        base_flows = [
            47.15, 32.80, 24.06, 18.25, 13.89, 4.17,
            2.90, 0.17, -0.83, -0.91, -11.76, -12.40,
            -12.83, -14.64, -18.96, -25.90, -27.32, -35.31,
            -46.35, -53.36, -54.40, -57.44, -62.50, -76.59,
            -110.64, -119.65, -140.58, -156.68, -228.33, -259.25, -280.88
        ]

        for i, sector in enumerate(cls.SECTORS):
            base_flow = base_flows[i] if i < len(base_flows) else 0
            flow_data = cls._generate_flow_series(times, base_flow)
            sectors_data.append({
                'name': sector,
                'final_flow': round(base_flow + random.uniform(-5, 5), 2),
                'flow_data': flow_data,
            })

        sectors_data.sort(key=lambda x: x['final_flow'], reverse=True)

        return {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M'),
            'is_trading': is_trading,
            'times': times,
            'sectors': sectors_data,
        }

    @classmethod
    def _generate_time_points(cls) -> List[str]:
        times = []
        for hour in [9, 10, 11]:
            start_min = 30 if hour == 9 else 0
            end_min = 30 if hour == 11 else 60
            for minute in range(start_min, end_min, 5):
                times.append(f'{hour:02d}:{minute:02d}')
        for hour in [13, 14]:
            for minute in range(0, 60, 5):
                times.append(f'{hour:02d}:{minute:02d}')
        times.append('15:00')
        return times

    @classmethod
    def _generate_flow_series(cls, times: List[str], final_value: float) -> List[float]:
        n = len(times)
        flows = []
        for i in range(n):
            t = i / max(n - 1, 1)
            base = final_value * (t ** 0.7)
            noise = random.uniform(-abs(final_value) * 0.08, abs(final_value) * 0.08)
            wave = abs(final_value) * 0.05 * (2 * random.random() - 1)
            flows.append(round(base + noise + wave, 2))
        if flows:
            flows[-1] = final_value
        return flows
