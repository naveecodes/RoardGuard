import os, sqlite3, uuid, csv, io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'roadguard.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app = Flask(__name__, template_folder='.')
app.secret_key = os.environ.get('ROADGUARD_SECRET', 'change-this-secret-before-deployment')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS potholes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            size TEXT NOT NULL,
            depth_cm REAL,
            status TEXT NOT NULL DEFAULT 'Reported',
            road_name TEXT,
            image_filename TEXT,
            reporter_name TEXT,
            created_at TEXT NOT NULL,
            complaint_status TEXT NOT NULL DEFAULT 'Not submitted',
            complaint_reference TEXT
        )''')
        count = con.execute('SELECT COUNT(*) FROM potholes').fetchone()[0]
        if count == 0:
            demo = [
                ('RG-DEMO01','Large pothole near junction','Demo entry — replace with a verified report.',30.3782,76.7767,'Large',12,'Reported','Ambala Cantt (demo)',None,'Demo User','2026-10-26 09:30','Not submitted',None),
                ('RG-DEMO02','Road surface damage','Demo entry — location and dimensions are illustrative.',30.3641,76.7903,'Medium',6,'In progress','Ambala (demo)',None,'Demo User','2026-10-25 16:15','Draft ready',None),
                ('RG-DEMO03','Small pothole','Demo entry — confirm before using for navigation.',30.3851,76.7622,'Small',2,'Resolved','Ambala (demo)',None,'Demo User','2026-10-20 11:00','Not submitted',None),
            ]
            con.executemany('''INSERT INTO potholes
                (report_code,title,description,latitude,longitude,size,depth_cm,status,road_name,image_filename,reporter_name,created_at,complaint_status,complaint_reference)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', demo)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_globals():
    return {'google_maps_api_key': GOOGLE_MAPS_API_KEY}


@app.route('/')
def index():
    with db() as con:
        reports = con.execute('SELECT * FROM potholes ORDER BY created_at DESC, id DESC').fetchall()
        total = len(reports)
        critical = sum(1 for r in reports if r['size'] == 'Large' and r['status'] != 'Resolved')
        pending = sum(1 for r in reports if r['status'] == 'Reported')
        resolved = sum(1 for r in reports if r['status'] == 'Resolved')
    return render_template('index.html', reports=reports, total=total, critical=critical, pending=pending, resolved=resolved)


@app.route('/report', methods=['POST'])
def create_report():
    try:
        title = request.form.get('title', '').strip()
        lat = float(request.form.get('latitude', ''))
        lng = float(request.form.get('longitude', ''))
        size = request.form.get('size', 'Medium')
        depth = request.form.get('depth_cm', '').strip()
        if not title:
            raise ValueError('Please add a short report title.')
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError('The coordinates are invalid.')
        if size not in {'Small', 'Medium', 'Large'}:
            raise ValueError('Choose a valid pothole size.')
        if depth and not (0 <= float(depth) <= 500):
            raise ValueError('Depth must be between 0 and 500 cm.')
        image_name = None
        photo = request.files.get('photo')
        if photo and photo.filename:
            if not allowed_file(photo.filename):
                raise ValueError('Photo must be PNG, JPG, JPEG or WEBP.')
            safe = secure_filename(photo.filename)
            image_name = f"{uuid.uuid4().hex[:12]}_{safe}"
            photo.save(os.path.join(UPLOAD_FOLDER, image_name))
        code = 'RG-' + uuid.uuid4().hex[:7].upper()
        with db() as con:
            con.execute('''INSERT INTO potholes
                (report_code,title,description,latitude,longitude,size,depth_cm,status,road_name,image_filename,reporter_name,created_at,complaint_status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                code, title, request.form.get('description','').strip(), lat, lng, size,
                float(depth) if depth else None, 'Reported', request.form.get('road_name','').strip(), image_name,
                request.form.get('reporter_name','').strip() or 'Anonymous', datetime.now().strftime('%Y-%m-%d %H:%M'), 'Draft ready'))
        flash(f'Report saved locally. Reference: {code}. Complaint draft is ready; it has NOT been submitted to a municipal authority.', 'success')
    except (ValueError, TypeError) as exc:
        flash(str(exc) or 'Please check the report details.', 'error')
    except Exception:
        flash('Could not save the report. Check the form and try again.', 'error')
    return redirect(url_for('index') + '#report')


@app.route('/api/reports')
def api_reports():
    with db() as con:
        rows = con.execute('SELECT * FROM potholes ORDER BY created_at DESC').fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/report/<int:report_id>/status', methods=['POST'])
def update_status(report_id):
    status = request.form.get('status', '')
    if status not in {'Reported', 'In progress', 'Resolved'}:
        flash('Invalid status selected.', 'error')
    else:
        with db() as con:
            con.execute('UPDATE potholes SET status=? WHERE id=?', (status, report_id))
        flash('Report status updated.', 'success')
    return redirect(url_for('index') + '#reports')


@app.route('/report/<int:report_id>/complaint')
def complaint_draft(report_id):
    with db() as con:
        r = con.execute('SELECT * FROM potholes WHERE id=?', (report_id,)).fetchone()
    if not r:
        flash('Report not found.', 'error')
        return redirect(url_for('index'))
    subject = f"Road pothole complaint: {r['report_code']} — {r['road_name'] or 'Location reported'}"
    body = (f"Dear Municipal Road Maintenance Team,\n\nPlease inspect the reported road hazard below.\n\n"
            f"Report reference: {r['report_code']}\nTitle: {r['title']}\nRoad/area: {r['road_name'] or 'Not provided'}\n"
            f"Coordinates: {r['latitude']}, {r['longitude']}\nGoogle Maps: https://www.google.com/maps?q={r['latitude']},{r['longitude']}\n"
            f"Estimated size: {r['size']}\nEstimated depth (cm): {r['depth_cm'] if r['depth_cm'] is not None else 'Not measured'}\n"
            f"Description: {r['description'] or 'Not provided'}\nReported at: {r['created_at']}\n\n"
            "Please acknowledge this complaint and share an official ticket number.\n\nRegards")
    with db() as con:
        con.execute("UPDATE potholes SET complaint_status='Draft opened' WHERE id=?", (report_id,))
    return render_template('complaint.html', report=r, subject=subject, body=body)


@app.route('/export.csv')
def export_csv():
    with db() as con:
        rows = con.execute('SELECT report_code,title,description,latitude,longitude,size,depth_cm,status,road_name,reporter_name,created_at,complaint_status,complaint_reference FROM potholes ORDER BY created_at DESC').fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys() if rows else ['report_code','title','description','latitude','longitude','size','depth_cm','status','road_name','reporter_name','created_at','complaint_status','complaint_reference'])
    for row in rows:
        writer.writerow(list(row))
    mem = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='roadguard_pothole_reports.csv')


@app.errorhandler(413)
def too_large(_error):
    flash('Photo is too large. Maximum upload size is 8 MB.', 'error')
    return redirect(url_for('index') + '#report')


init_db()
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
