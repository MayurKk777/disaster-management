from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime, timedelta
import math  # For approximate distance

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React runs here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust for your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Harsha@2426',
    'database': 'ecorescue'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Load YOLO model
model = YOLO('yolov8n.pt')  # Pretrained on COCO, detects 'person'

# Approximate distance function (e.g., Euclidean for simplicity)
def approximate_distance(loc1, loc2):
    # Assume loc is 'lat,lon' string, parse and compute
    l1 = list(map(float, loc1.split(',')))
    l2 = list(map(float, loc2.split(',')))
    return math.sqrt((l1[0] - l2[0])**2 + (l1[1] - l2[1])**2)

@app.get("/dashboard")
def get_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Total people detected (sum last 30 min)
    cursor.execute("SELECT SUM(detected_people) as total FROM Detections WHERE detection_time > NOW() - INTERVAL 30 MINUTE")
    total_people = cursor.fetchone()['total'] or 0
    
    # Available beds
    cursor.execute("SELECT SUM(available_beds) as total FROM Shelters")
    available_beds = cursor.fetchone()['total'] or 0
    
    # Active volunteers
    cursor.execute("SELECT COUNT(*) as active FROM Volunteers WHERE status = 'Available'")
    active_vol = cursor.fetchone()['active']
    cursor.execute("SELECT COUNT(*) as total FROM Volunteers")
    total_vol = cursor.fetchone()['total']
    
    # Critical zones
    cursor.execute("SELECT COUNT(*) as critical FROM Zones WHERE risk_level IN ('Severe', 'Elevated')")
    critical_zones = cursor.fetchone()['critical']
    
    # Zone details
    cursor.execute("""
        SELECT z.id, z.name, z.risk_level, z.last_update,
               (SELECT SUM(detected_people) FROM Detections d WHERE d.zone_id = z.id AND d.detection_time > NOW() - INTERVAL 30 MINUTE) as detected,
               (SELECT SUM(available_beds) FROM Shelters s WHERE s.zone_id = z.id) as beds,
               (SELECT COUNT(*) FROM Volunteers v WHERE v.zone_id = z.id) as volunteers,
               (SELECT COUNT(*) FROM Detections d WHERE d.zone_id = z.id AND d.detection_time > NOW() - INTERVAL 30 MINUTE) as freq
        FROM Zones z
    """)
    zones = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "total_people": total_people,
        "available_beds": available_beds,
        "active_volunteers": f"{active_vol}/{total_vol}",
        "critical_zones": critical_zones,
        "zones": zones
    }

@app.post("/upload_image")
async def upload_image(zone_id: int, file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Detect people
    results = model(img)
    detected_people = len([r for r in results[0].boxes.cls if r == 0])  # 0 is 'person' class
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert detection
    cursor.execute("INSERT INTO Detections (zone_id, detected_people, location) VALUES (%s, %s, %s)",
                   (zone_id, detected_people, 'Default Location'))  # Replace with actual loc
    conn.commit()
    
    # AI Agent logic
    process_agent(zone_id, detected_people)
    
    cursor.close()
    conn.close()
    
    return {"detected": detected_people}

def process_agent(zone_id, detected_people):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch shelters in zone, sorted by distance (approx) and beds
    cursor.execute("SELECT * FROM Shelters WHERE zone_id = %s ORDER BY available_beds DESC", (zone_id,))
    shelters = cursor.fetchall()
    
    # Fetch available volunteers
    cursor.execute("SELECT * FROM Volunteers WHERE zone_id = %s AND status = 'Available'", (zone_id,))
    volunteers = cursor.fetchall()
    
    assigned_beds = 0
    for shelter in shelters:
        if detected_people <= 0:
            break
        assignable = min(detected_people, shelter['available_beds'])
        # Update beds
        cursor.execute("UPDATE Shelters SET available_beds = available_beds - %s WHERE id = %s",
                       (assignable, shelter['id']))
        assigned_beds += assignable
        detected_people -= assignable
        
        # Assign volunteer if available
        if volunteers:
            vol = volunteers.pop(0)
            cursor.execute("INSERT INTO Assignments (volunteer_id, detection_id, shelter_id) VALUES (%s, LAST_INSERT_ID(), %s)",
                           (vol['id'], shelter['id']))
            cursor.execute("UPDATE Volunteers SET status = 'Assigned' WHERE id = %s", (vol['id'],))
    
    conn.commit()
    
    # Update risk
    update_risk(zone_id)
    
    # TODO: Send notifications (integrate Twilio or similar for SMS/WhatsApp)
    # For now, skip as no external API

def update_risk(zone_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(detected_people) FROM Detections WHERE zone_id = %s AND detection_time > NOW() - INTERVAL 30 MINUTE", (zone_id,))
    people_load = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(available_beds) FROM Shelters WHERE zone_id = %s", (zone_id,))
    avail_beds = cursor.fetchone()[0] or 0
    shelter_overload = max(0, people_load - avail_beds)
    
    cursor.execute("SELECT COUNT(*) FROM Detections WHERE zone_id = %s AND detection_time > NOW() - INTERVAL 30 MINUTE", (zone_id,))
    detection_freq = cursor.fetchone()[0]
    
    risk = (people_load * 0.5) + (shelter_overload * 0.3) + (detection_freq * 0.2)
    
    if risk > 200:
        level = 'Severe'
        color = 'red'
    elif risk > 100:
        level = 'Elevated'
        color = 'orange'
    elif risk > 50:
        level = 'Caution'
        color = 'yellow'
    else:
        level = 'Safe'
        color = 'green'
    
    cursor.execute("UPDATE Zones SET risk_level = %s, color = %s, last_update = NOW() WHERE id = %s",
                   (level, color, zone_id))
    conn.commit()
    cursor.close()
    conn.close()