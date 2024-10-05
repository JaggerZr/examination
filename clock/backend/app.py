from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import datetime
import threading
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

MONTHS = [44, 42, 48, 40, 48, 44, 40, 44, 42, 40, 40, 42, 44, 48, 42, 40, 44, 38]
SECONDS_PER_MINUTE = 90
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 90
SECONDS_PER_DAY = SECONDS_PER_HOUR * 36
SECONDS_PER_MONTH = [days * SECONDS_PER_DAY for days in MONTHS]
SECONDS_PER_YEAR = sum(SECONDS_PER_MONTH)

# 全局变量来存储时间偏移
time_offset = 0

class AlienTime:
    def __init__(self, year, month, day, hour, minute, second):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.hour = int(hour)
        self.minute = int(minute)
        self.second = int(second)

    @staticmethod
    def current_alien_time():
        global time_offset
        earth_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=time_offset)
        return AlienTime.from_earth_time(earth_time)

    @classmethod
    def from_earth_time(cls, earth_time):
        earth_seconds = (earth_time - datetime.datetime(1970, 1, 1)).total_seconds()
        alien_seconds = earth_seconds * 2
        alien_start = cls(2804, 18, 31, 2, 2, 88)
        return alien_start.add_seconds(alien_seconds)

    @classmethod
    def from_string(cls, time_str):
        date_part, time_part = time_str.rsplit(' ', 1)
        year, month, day = map(int, date_part.split('-'))
        hour, minute, second = map(int, time_part.split(':'))
        return cls(year, month, day, hour, minute, second)

    def to_earth_time(self):
        alien_start = AlienTime(2804, 18, 31, 2, 2, 88)
        alien_seconds = self.total_seconds() - alien_start.total_seconds()
        earth_seconds = alien_seconds // 2
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=earth_seconds)

    def add_seconds(self, seconds):
        self.second += int(seconds)

        self.minute += self.second // SECONDS_PER_MINUTE
        self.second %= SECONDS_PER_MINUTE

        self.hour += self.minute // 90
        self.minute %= 90

        self.day += self.hour // 36
        self.hour %= 36

        while self.day > MONTHS[int(self.month) - 1]:
            self.day -= MONTHS[int(self.month) - 1]
            self.month += 1
            if self.month > 18:
                self.month = 1
                self.year += 1

        self.year = int(self.year)
        self.month = int(self.month)
        self.day = int(self.day)
        self.hour = int(self.hour)
        self.minute = int(self.minute)
        self.second = int(self.second)

        return self

    def total_seconds(self):
        seconds = self.second
        seconds += self.minute * SECONDS_PER_MINUTE
        seconds += self.hour * SECONDS_PER_HOUR
        seconds += (self.day - 1) * SECONDS_PER_DAY
        seconds += sum(SECONDS_PER_MONTH[:self.month - 1])
        seconds += (self.year - 2804) * SECONDS_PER_YEAR
        return seconds

    def __str__(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d} {self.hour:02d}:{self.minute:02d}:{self.second:02d}"

# 存储闹钟的字典
alarms = {}

@app.route('/api/current-alien-time')
def get_current_alien_time():
    alien_time = AlienTime.current_alien_time()
    return jsonify({'alien_time': str(alien_time)})

@app.route('/api/convert-to-earth-time', methods=['POST'])
def convert_to_earth_time():
    alien_time_str = request.json['alien_time']
    try:
        alien_time = AlienTime.from_string(alien_time_str)
        earth_time = alien_time.to_earth_time()
        return jsonify({'earth_time': earth_time.strftime('%Y-%m-%d %H:%M:%S')})
    except ValueError:
        return jsonify({'error': 'Invalid alien time format'}), 400

@app.route('/api/set-alien-time', methods=['POST'])
def set_alien_time():
    global time_offset
    alien_time_str = request.json['alien_time']
    try:
        new_alien_time = AlienTime.from_string(alien_time_str)
        current_alien_time = AlienTime.current_alien_time()
        
        # 计算新的时间偏移
        new_earth_time = new_alien_time.to_earth_time()
        current_earth_time = datetime.datetime.utcnow()
        time_offset = int((new_earth_time - current_earth_time).total_seconds())
        
        return jsonify({'success': True, 'message': 'Time set successfully'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/set-alarm', methods=['POST'])
def set_alarm():
    alarm_time = request.json['alarm_time']
    try:
        alien_time = AlienTime.from_string(alarm_time)
        alarm_id = str(len(alarms) + 1)
        alarms[alarm_id] = alien_time
        return jsonify({'success': True, 'alarm_id': alarm_id})
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid time format'}), 400

@app.route('/api/get-alarms', methods=['GET'])
def get_alarms():
    return jsonify({id: str(time) for id, time in alarms.items()})

def check_alarms():
    while True:
        current_time = AlienTime.current_alien_time()
        for alarm_id, alarm_time in list(alarms.items()):
            time_diff = abs(current_time.total_seconds() - alarm_time.total_seconds())
            if time_diff < 1 or (time_diff > SECONDS_PER_YEAR - 1):  # 允许1秒的误差
                socketio.emit('alarm_triggered', {'alarm_id': alarm_id, 'time': str(alarm_time)})
                del alarms[alarm_id]
        time.sleep(0.5)  # 每0.5秒检查一次

# 启动闹钟检查线程
alarm_thread = threading.Thread(target=check_alarms)
alarm_thread.daemon = True
alarm_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True)