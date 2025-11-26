# EcoRescue – Disaster Response & Coordination (Bangalore)

EcoRescue is a disaster response coordination system that models high-risk zones, shelters, volunteers, and real-time detections to support efficient rescue and evacuation operations in Bangalore.  
The current dataset focuses on key localities such as Indira Nagar, Bellandur, Electronic City Phase I, and RajaRajeshwari Nagar (configured as a high-risk red zone).

---

## Overview

EcoRescue is designed as the backend data layer for an emergency management platform.  
It tracks which areas are at risk, where shelters are located, how many beds are available, which volunteers are free or assigned, and which detections (incidents) are currently active.  
Assignments then link volunteers, detections, and shelters into concrete “missions”.

This repository currently contains:
- A complete MySQL schema for the EcoRescue database.
- Seed data for Bangalore zones, shelters, volunteers, detections, and assignments.
- Example queries to explore and debug the system.

---

## Features

- **Risk-zoned localities**
  - Models Bangalore areas like **Indira Nagar**, **Bellandur**, **Electronic City Phase I**, and **RajaRajeshwari Nagar**.
  - Per-zone risk levels using `ENUM('Safe','Caution','Elevated','Severe')` and a color code (e.g., green, yellow, orange, red).
  - `RajaRajeshwari Nagar` is set as a **Severe (red)** zone to simulate a critical area.

- **Shelter management**
  - Exactly **two shelters per zone**, with realistic Indian names and locations.
  - For RR Nagar, one shelter is explicitly modeled as **“RV College of Engineering”** to act as a major relief center.
  - Tracks `available_beds` vs `total_beds` to monitor capacity.

- **Volunteer tracking**
  - Each volunteer has:
    - `status`: `Available` or `Assigned`
    - `zone_id`: current assigned zone
    - `location`: granular textual location (e.g., “RR Nagar - Ideal Homes”, “E-City - Wipro Gate”).

- **Incident detections**
  - `Detections` table logs:
    - `zone_id` of the incident
    - `detected_people` (approx number of affected people)
    - `detection_time`
    - `location` (e.g., “RR Nagar - Mysore Road Flood Zone”, “Bellandur - EcoWorld Bus Stop”)
  - Includes multiple scenarios per zone to simulate realistic workloads.

- **Rescue assignments**
  - `Assignments` link:
    - `volunteer_id`
    - `detection_id`
    - `shelter_id`
  - Tracks `status` (`Pending` / `Completed`) and `assignment_time`.
  - Enables queries like “Which volunteer is taking which people from where to which shelter?”.

---

## Tech Stack

- **Database:** MySQL (tested with MySQL 8+)
- **Schema style:** Relational, with foreign key constraints for referential integrity
- **Intended usage:**
  - Backend for a web/mobile emergency response app
  - Data source for dashboards (e.g., risk maps, shelter capacity views)
  - Testbed for algorithms like optimal volunteer-shelter assignment and load balancing

---

## Possible Extensions

- **Frontend dashboard**
  - Map-based UI showing:
    - Zones colored by risk.
    - Shelter capacity indicators.
    - Live incident markers and active missions.

- **Optimization / AI layer**
  - Algorithms to:
    - Suggest best volunteer–shelter pairing based on distance and capacity.
    - Re-route missions when a shelter nears full capacity.

- **Integration with external data**
  - Weather, flood forecasts, or IoT sensors feeding detections.
  - SMS / WhatsApp alert integration for volunteers and affected residents.

- **Role-based access control**
  - Separate permissions for:
    - Admins (configure zones, shelters)
    - Field coordinators (manage assignments)
    - Volunteers (view assigned missions and update status)

