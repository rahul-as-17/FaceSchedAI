# 📸 FaceSchedAI - Smart Attendance System

**FaceSchedAI** is an AI-powered attendance automation tool that uses facial recognition to log employee check-ins and check-outs, replacing traditional manual logs with a touchless, secure solution.

## 🚀 Key Features
* **Real-Time Face Recognition:** Uses OpenCV and DeepFace to identify employees instantly.
* **Automated Logging:** Saves Check-in/Check-out times directly to a MySQL database.
* **Admin Dashboard:** A web interface (Streamlit) for HR to view logs, track late arrivals, and download Excel reports.
* **Shift Management:** Logic to detect if an employee is "On Time" or "Late" based on their schedule.

## 🛠️ Tech Stack
* **Python 3.11** (Core Logic)
* **OpenCV** (Computer Vision)
* **DeepFace** (AI Model)
* **MySQL** (Database)
* **Streamlit** (Web Dashboard)

## ⚙️ Setup & Installation
1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/Hollow-17R/FaceSchedAI.git](https://github.com/Hollow-17R/FaceSchedAI.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the System:**
    * To start recognition: `python attendance.py`
    * To open dashboard: `streamlit run admin_dashboard.py`

---
*Created by Rahul A S*