from flask import Flask, request, render_template, redirect, url_for, session
import pymysql
import difflib
import openai
import random

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '1234'
DB_NAME = 'hekate'

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    db=DB_NAME,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 회원가입 정보 저장 함수
def save_user_info(user_id, user_pw, user_name, user_birthday, user_gender, user_tel):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO tb_user (user_id, user_pw, user_name, user_birthday, user_gender, user_tel)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (user_id, user_pw, user_name, user_birthday, user_gender, user_tel))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("회원가입 정보 저장에 실패하였습니다:", str(e))
        return False
    finally:
        conn.close()

    return True

# 사용자 인증 함수 (아이디와 비밀번호를 DB와 비교하여 인증)
def verify_user_info(user_id, user_pw):
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cur:
            sql = """
            SELECT user_pw FROM tb_user WHERE user_id = %s
            """
            cur.execute(sql, (user_id,))
            result = cur.fetchone()
    finally:
        conn.close()

    if result is not None and result['user_pw'] == user_pw:
        return True
    else:
        return False

# 사용자 정보 조회 함수
def get_user_info():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cur:
            sql = """
            SELECT user_name, user_gender FROM tb_user
            """
            cur.execute(sql)
            result = cur.fetchone()
    finally:
        conn.close()

    return result if result is not None else None


def get_database_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        print("데이터베이스 연결에 실패하였습니다:", str(e))
        return None

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 세션 사용을 위한 시크릿 키 설정
openai.api_key = 'your_secret_key_here'

def generate_perfume(description):
    prompt = f"\n기분: {description['mood']}\n성별: {description['gender']}\n나이: {description['age']}\n선호하는 향의 종류: {description['preference']}\n지금까지 사용한 적 있는 향수 중에서 가장 마음에 드는 향수: {description['favorite']}\n선호하지않는 향기: {description['avoid']}\n향수 사용 목적: {description['purpose']}\n선호하는 향기의 강도: {description['intensity']}\n향수 사용 계절: {description['season']}\n향수의 향기:"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=500,
        n=5,  # 다양한 향기를 생성하기 위해 토큰 개수를 늘립니다.
        stop=None,
        temperature=0.5,
        top_p=1,
        frequency_penalty=0.1,
        presence_penalty=0.0
    )

    perfumes_with_reasons = []
    for choice in response.choices:
        # 향수와 이유를 튜플로 저장합니다.
        perfume_with_reason = (choice.text.strip(), "OpenAI에서 생성")
        perfumes_with_reasons.append(perfume_with_reason)

    return perfumes_with_reasons

def generate_perfume_effect(perfume):
    prompt = f"{perfume} 향을 맡아서 얻을수 있는 정신적으로 긍정적인 효과를 1가지만 알려주세요\n"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.4,
        top_p=0.7,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    if response.choices:
        # 정신적으로 긍정적인 효과를 잘 나타내는 문장을 선택하기 위해 비교 대상 문장 리스트를 정의합니다.
        positive_effects = ['정신이 맑아지고 상쾌한 기분이 들어요', '긴장이 완화되고 편안함을 느껴요', '에너지가 넘치고 기분이 상쾌해져요', '긍정적인 감정이 느껴져요', '스트레스가 풀리고 기분이 좋아져요','편안해지고 정신이 맑아져요']

        # API 응답에서 가장 비슷한 효과 문장을 선택합니다.
        best_effect = None
        best_similarity = 0
        for choice in response.choices:
            for positive_effect in positive_effects:
                similarity = difflib.SequenceMatcher(None, choice.text.strip(), positive_effect).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_effect = choice.text.strip()

        return best_effect

    return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'login' in request.form:
            return redirect(url_for('login'))  # 로그인 페이지로 리디렉션
        elif 'signup' in request.form:
            return redirect(url_for('signup'))  # 회원가입 페이지로 리디렉션

    return render_template('good.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 로그인 처리
        id = request.form['id']
        pass_word = request.form['pass_word']

        # 입력한 아이디와 비밀번호를 DB와 비교하여 인증
        if verify_user_info(id, pass_word):
            session['user_id'] = id  # 세션에 사용자 ID 저장
            return redirect(url_for('welcome'))
        else:
            error_message = "잘못된 아이디 혹은 비밀번호입니다."
            return render_template('good.html', error_message=error_message)
    else:
        return render_template('good.html')

# 회원가입 페이지
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # 회원가입 처리
        user_id = request.form['user_id']
        user_pw = request.form['user_pw']
        confirm_pass_word = request.form['confirm_pass_word']
        user_gender = request.form['user_gender']
        user_birthday = request.form['user_birthday']
        user_name = request.form['user_name']
        user_tel = request.form['user_tel']
        # 비밀번호 확인
        if user_pw != confirm_pass_word:
            return "비밀번호와 비밀번호 확인이 일치하지 않습니다."

        # 비밀번호를 안전하게 해시화
        #hashed_pw = generate_password_hash(user_pw)

        # 회원 정보를 데이터베이스에 저장
        save_user_info(user_id, user_pw, user_name, user_birthday, user_gender, user_tel)

        # 회원가입 완료 페이지로 리디렉션
        return redirect(url_for('signup_complete'))

    # GET 요청을 받았을 때 회원가입 화면 출력
    return render_template('login_signup.html')

# 회원가입 완료 페이지
@app.route('/signup_complete', methods=['GET'])
def signup_complete():
    # GET 요청을 받았을 때 회원가입 완료 화면 출력
    return render_template('signup_complete.html')

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    # 이전과 동일한 내용
    if request.method == 'POST':
        # POST 요청을 받았을 때 사용자 입력 처리
        description = {
            'mood': request.form['mood'],
            'gender': request.form['gender'],
            'age': request.form['age'],
            'preference': request.form['preference'],
            'favorite': request.form['favorite'],
            'avoid': request.form['avoid'],
            'purpose': request.form['purpose'],
            'intensity': request.form['intensity'],
            'season': request.form['season'],
        }

        # 향수 생성 및 이유 가져오기
        perfumes_with_reasons = generate_perfume(description)

        representative_perfumes = ['우디','플로럴','프루티','로즈','알데하이드','시트러스','비누','구르망','허브','그린','머스크','아쿠아','스위트','타바코','레더','애니멀릭','푸제르','오리엔탈','','','','','','','','','','','','','','','','','','','']

        # 추천 향기 리스트
        recommended_perfumes = []
        for perfume, reason in perfumes_with_reasons:
            if perfume in representative_perfumes:
                # 향수와 이유를 튜플로 저장합니다.
                effect = generate_perfume_effect(perfume)
                recommended_perfumes.append((perfume, reason, effect))

        # 대표적인 향기 종류로의 대답이 없는 경우, 첫 번째 향기와 비슷한 향기 추천
        if len(recommended_perfumes) == 0 and len(perfumes_with_reasons) > 0:
            first_perfume = perfumes_with_reasons[0][0]
            similarity_ratios = []

            for perfume in representative_perfumes:
                similarity_ratio = difflib.SequenceMatcher(None, first_perfume, perfume).ratio()
                similarity_ratios.append(similarity_ratio)

            max_similarity_ratio = max(similarity_ratios)
            similar_perfume_index = similarity_ratios.index(max_similarity_ratio)
            similar_perfume = representative_perfumes[similar_perfume_index]

            # 향수와 이유를 튜플로 저장합니다.
            effect = generate_perfume_effect(similar_perfume)
            recommended_perfumes.append((similar_perfume, "유사한 향기를 추천 했습니다", effect))
        return render_template('perfume_recommendation2.html', perfumes=recommended_perfumes)
        
    else:
        # GET 요청을 받았을 때 기본 화면 출력
        user_info = get_user_info()
        gender, age = user_info if user_info else ('', '')  # 만약 데이터가 없으면 빈 문자열로 초기화

        # 템플릿 렌더링하여 HTML 코드 반환
        return render_template('welcome.html')
    
@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    perfume = request.args.get('perfume')

    # hekate DB에서 해당 perfume 값에 해당하는 데이터 가져오기
    if perfume:
        try:
            with conn.cursor() as cursor:
                # %는 와일드카드로서 임의의 문자열을 의미합니다.
                sql = "SELECT perf_idx, perf_name, perf_img, perf_info FROM tb_perfume WHERE perf_affiliation LIKE %s"
                cursor.execute(sql, ('%' + perfume + '%',))
                result = cursor.fetchall()
        except Exception as e:
            # 에러 처리
            print(f"Error: {e}")
            result = []
    else:
        result = []

    # 템플릿에 데이터 전달 후 HTML 렌더링
    return render_template('recommendations.html', perfume=perfume, result=result)

@app.route('/submit', methods=['GET','POST'])
def submit_form():
    selected_perfumes = request.form.getlist('selected_perfumes')
    selected_perfumes = [int(perfume) for perfume in ','.join(selected_perfumes).split(',')]
    
    # 세션에서 사용자 ID 가져오기
    user_id = session.get('user_id')

    # 랜덤한 4자리 숫자로 구성된 user_code 생성
    user_code = str(random.randint(1000, 9999))

    # 데이터베이스에 INSERT 문 실행
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)
    cursor = conn.cursor()

    if len(selected_perfumes) == 1:
        cursor.execute("INSERT INTO tb_reco_perfume (user_code, user_id, perf_idx1,perf_idx2) VALUES (%s, %s, %s, %s)",
                       (user_code, user_id, selected_perfumes[0],None))
    elif len(selected_perfumes) >= 2:
        cursor.execute("INSERT INTO tb_reco_perfume (user_code, user_id, perf_idx1, perf_idx2) VALUES (%s, %s, %s, %s)",
                       (user_code, user_id, selected_perfumes[0], selected_perfumes[1]))

    conn.commit()
    conn.close()

    return render_template('/nice.html',user_code=user_code)

from flask import render_template, request

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        perf_idx = request.args.get('perf_idx')
        return render_template("feedback.html", perf_idx=perf_idx)
    elif request.method == 'POST':
        # 폼 제출 후의 처리 로직
        # ...
        return render_template('feedback.html')
   
@app.route('/good')
def good():
    return render_template('good.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5020)
