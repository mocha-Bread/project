from flask import Flask, request, jsonify
import pymysql
import time

app = Flask(__name__)

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '1234'
DB_NAME = 'hekate'

db_config = {
    "host": 'localhost',
    "user": 'root',
    "password": '1234',
    "database": 'hekate'
}

# 초기 입력 가능 간격 설정
keypad_interval = 10  # 10 seconds
last_keypad_time = 0

@app.route('/api/get_perf_loc', methods=['GET', 'POST'])
def abc():
    global last_keypad_time

    current_time = time.time()
    elapsed_time = current_time - last_keypad_time

    if elapsed_time < keypad_interval:
        return jsonify(error="Too soon to send another keypad input"), 429

    keypad_value = request.form.get('keypadValue')

    if keypad_value is None:
        return jsonify(error="Invalid request, keypadValue not provided"), 400

    print(f"Received keypad_value: {keypad_value}")

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # First, get the perf_idx1 from tb_reco_perfume for the given user_id
            sql1 = "SELECT perf_idx1 FROM tb_reco_perfume WHERE user_code = %s"
            cursor.execute(sql1, (keypad_value,))
            result1 = cursor.fetchone()

            if not result1:
                return jsonify(error="No data found for user_id"), 404

            perf_idx1 = result1['perf_idx1']

            # Now, get perf_loc from tb_perfume_state for the given perf_idx1
            sql2 = "SELECT perf_loc FROM tb_perfume_state WHERE perf_idx = %s"
            cursor.execute(sql2, (perf_idx1,))
            result2 = cursor.fetchone()

            if result2:
                perf_loc = result2['perf_loc']
                print(f"Found perf_loc: {perf_loc}")
                response = {'perf_loc': perf_loc}
                return jsonify(response)
            else:
                return jsonify(error="No location data found for perf_idx1"), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify(error=str(e)), 500

    finally:
        conn.close()

    last_keypad_time = current_time

if __name__ == "__main__":
    app.run(host='192.168.90.214', port=5020, debug=True)
