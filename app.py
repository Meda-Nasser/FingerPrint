from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import json
import os
import requests
import pandas as pd

app = Flask(__name__)
app.secret_key = "your_secret_key"

# كلمة المرور الخاصة بصفحة HR
HR_PASSWORD = "t"  # يجب تغييرها إلى كلمة مرور معقدة
@app.route("/search_records", methods=["GET", "POST"])
def search_records():
    if not validate_session():
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form.get("username")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        status_filter = request.form.get("status")

        # تحويل التاريخ إلى تنسيق datetime
        try:
            start_date = datetime.strptime(start_date_str, "%m/%d/%Y") if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%m/%d/%Y") if end_date_str else None
        except ValueError as e:
            print("Date format error:", e)
            return "<script>alert('تنسيق التاريخ غير صحيح. يجب أن يكون mm/dd/yyyy.'); window.history.back();</script>"

        # تحميل سجلات البصمات
        try:
            records = load_fingerprint_records()
        except Exception as e:
            print("Error loading fingerprint records:", e)
            return "<script>alert('حدث خطأ أثناء جلب السجلات.'); window.history.back();</script>"

        # فلترة السجلات بناءً على المدخلات
        filtered_records = []
        for record in records:
            try:
                # التحقق من اسم المستخدم
                if username and record["username"] != username:
                    continue
                # التحقق من التاريخ
                record_datetime = datetime.strptime(record["date_time"], "%Y-%m-%d %H:%M:%S")
                if start_date and record_datetime < start_date:
                    continue
                if end_date and record_datetime > end_date:
                    continue
                # التحقق من الحالة
                if status_filter != "الكل" and record["status"] != status_filter:
                    continue
                filtered_records.append(record)
            except Exception as e:
                print("Error processing record:", e)

        if not filtered_records:
            return "<script>alert('لا توجد سجلات تطابق معايير البحث.'); window.history.back();</script>"

        return render_template("search_results.html", records=filtered_records)

    return render_template("search.html")
# ملفات JSON المستخدمة
USER_DATA_FILE = "user_data.json"
FINGERPRINT_RECORDS_FILE = "fingerprint_records.json"

# تحميل بيانات المستخدمين
def load_user_data():
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print("Error loading user data:", e)
        return {}

# التحقق من الجلسة
def validate_session():
    users = load_user_data()
    if "username" in session and session["username"] not in users:
        session.pop("username", None)
        return False
    return True

# حفظ بيانات المستخدمين
def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل سجلات البصمات
def load_fingerprint_records():
    try:
        if os.path.exists(FINGERPRINT_RECORDS_FILE):
            with open(FINGERPRINT_RECORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except json.JSONDecodeError as e:
        print("Error: Invalid JSON format in fingerprint records:", e)
        return []

# حفظ سجلات البصمات
def save_fingerprint_records(records):
    with open(FINGERPRINT_RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

# إعداد المستخدمين الافتراضيين
if not os.path.exists(USER_DATA_FILE):
    save_user_data({"admin": "1234"})

# صفحة تسجيل الدخول
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_user_data()
        username = request.form["username"]
        password = request.form["password"]

        if username not in users:
            return "<script>alert('اسم المستخدم غير موجود.'); window.location.href='/';</script>"
        
        if users[username] == password:
            session["username"] = username
            return redirect(url_for("main_page"))

        return "<script>alert('كلمة المرور غير صحيحة.'); window.location.href='/';</script>"
    
    return render_template("login.html")

# الصفحة الرئيسية
@app.route("/main")
def main_page():
    if not validate_session():
        return redirect(url_for("login"))
    return render_template("main.html", username=session["username"])

# صفحة تسجيل البصمات
@app.route("/fingerprint", methods=["GET", "POST"])
def fingerprint():
    if not validate_session():
        return redirect(url_for("login"))

    if request.method == "POST":
        username = session["username"]
        date_time = request.form["date_time"]
        location = request.form["location"]
        status = request.form["status"]

        if not location or location == "جاري تحديد الموقع...":
            return """
            <script>
                alert('يرجى تحديد الموقع قبل الإرسال.');
                window.history.back();
            </script>
            """
        
        record = {"username": username, "date_time": date_time, "location": location, "status": status}
        records = load_fingerprint_records()
        records.append(record)
        save_fingerprint_records(records)

        return """
        <script>
            alert('تم الإرسال بنجاح!');
            window.location.href = '/main';
        </script>
        """

    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # استخدام واجهة برمجة التطبيقات للحصول على الموقع
    location = get_location()  # دالة جديدة للحصول على الموقع
    return render_template("fingerprint.html", username=session["username"], date_time=date_time, location=location)

def get_location():
    try:
        # استبدل هذا بالرابط الخاص بواجهة برمجة التطبيقات التي تختارها
        response = requests.get("https://api.ipgeolocation.io/ipgeo?apiKey=YOUR_API_KEY")
        data = response.json()
        return f"{data['latitude']}, {data['longitude']}"  # أو أي معلومات أخرى تحتاجها
    except Exception as e:
        print("Error getting location:", e)
        return "جاري تحديد الموقع..."

# صفحة التقارير
@app.route("/reports")
def reports():
    if not validate_session():
        return redirect(url_for("login"))

    username = session["username"]
    records = load_fingerprint_records()
    user_records = [record for record in records if record["username"] == username]

    attendance_count = sum(1 for record in user_records if record["status"] == "حضور")
    departure_count = sum(1 for record in user_records if record["status"] == "انصراف")
    travel_count = sum(1 for record in user_records if record["status"] == "سفر")

    return render_template(
        "reports.html",
        records=user_records,
        attendance_count=attendance_count,
        departure_count=departure_count,
        travel_count=travel_count,
    )

# صفحة بيانات الموظف
@app.route("/employee_info")
def employee_info():
    if not validate_session():
        return redirect(url_for("login"))

    username = session["username"]
    ip_address = request.remote_addr  # الحصول على عنوان IP
    return render_template("employee_info.html", username=username, ip_address=ip_address)

# صفحة إدارة الموارد البشرية
@app.route("/hr", methods=["GET", "POST"])
def hr_management():
    if not session.get("hr_logged_in"):
        return redirect(url_for("hr_login"))

    if request.method == "POST":
        users = load_user_data()
        user_name = request.form["user_name"]
        user_password = request.form["user_password"]

        if user_name in users:
            return "<script>alert('اسم المستخدم موجود بالفعل!'); window.location.href='/hr';</script>"

        users[user_name] = user_password
        save_user_data(users)
        return redirect(url_for("hr_management"))

    return render_template("hr.html", users=load_user_data())

# تسجيل الخروج من HR
@app.route("/hr_logout")
def hr_logout():
    session.pop("hr_logged_in", None)
    return redirect(url_for("hr_login"))

# حذف مستخدم
@app.route("/hr/delete/<user_id>", methods=["POST"])
def delete_user(user_id):
    if not session.get("hr_logged_in"):
        return redirect(url_for("hr_login"))

    users = load_user_data()
    if user_id in users:
        del users[user_id]
        save_user_data(users)

        if session["username"] == user_id:
            session.pop("username", None)
            return """
            <script>
                alert("تم حذف الحساب وتسجيل الخروج بنجاح!");
                window.location.href = "/";
            </script>
            """

    return redirect(url_for("hr_management"))

import os
from flask import send_from_directory

@app.route("/export_data")
def export_data():
    if not session.get("hr_logged_in"):
        return redirect(url_for("hr_login"))

    records = load_fingerprint_records()

    # تحويل البيانات إلى DataFrame
    data_to_export = []
    for record in records:
        # استخدام قيمة افتراضية إذا كان المفتاح غير موجود
        location = record.get("location", "N/A")  # تعيين قيمة افتراضية
        data_to_export.append({
            "username": record["username"],
            "date_time": record["date_time"],
            "location": location,
            "status": record["status"]
        })

    df = pd.DataFrame(data_to_export)

    # تصدير البيانات إلى ملف Excel باستخدام openpyxl
    excel_file = "attendance_data.xlsx"
    excel_path = os.path.join("static", excel_file)
    df.to_excel(excel_path, index=False, engine='openpyxl')

    # إرجاع رابط لتحميل الملف
    return f"تم تصدير البيانات بنجاح! <a href='/static/{excel_file}'>تحميل الملف</a>"

# تحليل البيانات
@app.route("/data_analysis")
def data_analysis():
    if not session.get("hr_logged_in"):
        return redirect(url_for("hr_login"))

    records = load_fingerprint_records()
    attendance_count = sum(1 for record in records if record["status"] == "حضور")
    departure_count = sum(1 for record in records if record["status"] == "انصراف")

    return render_template("data_analysis.html", attendance_count=attendance_count, departure_count=departure_count)

# صفحة تسجيل الدخول HR
@app.route("/hr_login", methods=["GET", "POST"])
def hr_login():
    if request.method == "POST":
        hr_password = request.form["hr_password"]

        if hr_password == HR_PASSWORD:
            session["hr_logged_in"] = True
            return redirect(url_for("hr_management"))
        
        return "<script>alert('كلمة مرور HR غير صحيحة!'); window.location.href='/hr_login';</script>"

    return render_template("hr_login.html")

if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
