# RoadGuard — Pothole Reporting & Road Safety Dashboard

A mobile-friendly Flask + SQLite project for an M.Sc. Computer Science Semester III demonstration. It lets users record pothole photos, coordinates, estimated size/depth, status, map points, complaint drafts and CSV exports.

## Features
- Professional responsive dashboard with report counters and filters.
- Google Maps JavaScript integration (requires your own API key).
- Browser geolocation capture for latitude/longitude.
- Upload pothole photos (PNG/JPG/JPEG/WEBP; max 8 MB).
- SQLite storage for reports and statuses.
- Size/severity markers, Google Maps coordinate links, and report search.
- Complaint draft generator with copy-to-clipboard and link to official grievance resources.
- CSV export for evaluation/demo.
- Demo records included so the dashboard isn't empty on first launch.

## Important limitations
- The three initial map points are **illustrative demo data**, not verified hazards. Remove them before a real deployment.
- Size/depth are entered by a person; this version does not run computer vision or automatically measure a pothole.
- A complaint is **not automatically registered with a government authority**. The app generates a draft only. Direct registration needs an identified authority, its supported API/portal integration, authentication, and any required permissions. A real acknowledgement number must come from that authority.
- This is a prototype, not a certified navigation/driver-warning system. Do not use it as a safety-critical driving aid.
- Local SQLite and uploaded photos are stored on the host machine. A production deployment needs authentication, moderation, privacy controls, backups, HTTPS and abuse protection.

## Run on Windows 10/11
1. Install Python 3.10+ from python.org and tick **Add Python to PATH** during installation.
2. Extract this ZIP into a folder.
3. Open Command Prompt in the extracted `RoadGuard_Pothole_Project` folder.
4. Create a virtual environment and install dependencies:

   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. (Optional but recommended) Set a Google Maps API key. In Google Cloud Console, create a project, enable **Maps JavaScript API**, enable billing if Google requires it, create an API key and restrict it to the intended website. For local testing, set the key in Command Prompt before launching:

   ```bat
   set GOOGLE_MAPS_API_KEY=YOUR_REAL_KEY_HERE
   ```

   If no key is set, the dashboard still works but the interactive Google map will show a setup placeholder; coordinate links still open Google Maps.
6. Start the app:

   ```bat
   python app.py
   ```
7. Open `http://127.0.0.1:5000` in your browser.

## Open on an Android phone
- For a quick demo, host it on a platform that supports Python/Flask and persistent storage, or run it on a computer and access it from the same Wi-Fi network using that computer's local IP address and a suitable `app.run(host='0.0.0.0')` setting.
- Browser geolocation generally requires HTTPS or localhost. Do not expose Flask's development server directly to the public internet.
- Free hosting providers may sleep, impose resource quotas, or use ephemeral filesystems. If storage is ephemeral, reports/photos may disappear after restart; use persistent storage for real use.

## Project structure
```
RoadGuard_Pothole_Project/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── roadguard.db             # created automatically on first run
├── templates/
│   ├── index.html
│   └── complaint.html
└── static/
    ├── css/style.css
    ├── js/app.js
    └── uploads/             # uploaded photos
```

## Suggested viva explanation
- **Frontend:** HTML, CSS, JavaScript, Google Maps JavaScript API.
- **Backend:** Python Flask routes and validation.
- **Database:** SQLite (`potholes` table).
- **Core workflow:** report form → validate coordinates/photo → save row → display map marker/register → generate complaint draft → export CSV.
- **Future scope:** image-based pothole detection with a trained YOLO model, verified depth estimation, authority-specific complaint APIs, user authentication, duplicate detection, offline reporting and real-time hazard alerts.
