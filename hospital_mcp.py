import os
import random
import datetime
from urllib.parse import quote
from fastmcp import FastMCP
from pymongo import MongoClient
from dotenv import load_dotenv

# Initialize FastMCP Server
mcp = FastMCP("Hospital Doctor & Booking System")

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["hospital_db"]
doctors_collection = db["doctors"]
appointments_collection = db["appointments"]

@mcp.tool()
def search_doctors(specialty: str) -> str:
    """CRITICAL: You MUST use this tool to search for doctors. DO NOT invent or make up doctor names. Pass the specialty (e.g., 'cardiologist', 'endocrinologist')."""
    spec = specialty.strip()
    
    # Fuzzy match specialty from MongoDB
    matched_doctors = list(doctors_collection.find({"specialty": {"$regex": spec, "$options": "i"}}))
            
    if not matched_doctors:
        # Fallback to general physician
        matched_doctors = list(doctors_collection.find({"specialty": {"$regex": "general physician", "$options": "i"}}))
        
    result = "Please ask the user to select one of the following doctors by showing these exact options:\n\n"
    for doc in matched_doctors:
        btn_text = f"{doc['name']} ({doc['exp']}) - {doc['hospital']}"
        result += f"[Option: {btn_text}]\n"
        
    return result

@mcp.tool()
def get_doctor_slots(doctor_selection: str) -> str:
    """CRITICAL: You MUST use this tool to get available slots for a selected doctor. Pass the exact doctor name/details."""
    # Generate tomorrow's date
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Default slots available in the hospital
    all_slots = ["10:00 AM", "11:00 AM", "02:00 PM", "04:30 PM", "05:30 PM"]
    
    # Check MongoDB for ALREADY BOOKED slots for this doctor tomorrow
    booked_appointments = list(appointments_collection.find({
        "doctor_details": doctor_selection,
        "date": tomorrow
    }))
    booked_times = [apt["time_slot"] for apt in booked_appointments]
    
    # Filter out booked slots
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    if not available_slots:
        return f"No slots available for {doctor_selection} tomorrow. Ask the user to select another doctor."
    
    result = f"Please ask the user to select a time slot for {doctor_selection} by showing these exact options:\n\n"
    for slot in available_slots:
        result += f"[Option: {tomorrow} at {slot}]\n"
        
    return result

@mcp.tool()
def book_appointment(doctor_selection: str, time_slot: str) -> str:
    """CRITICAL: You MUST use this tool to book an appointment and get the Google Calendar link."""
    # Generate booking ID
    booking_id = f"APT-{random.randint(10000, 99999)}"
    
    # Split the time slot string (e.g. "2026-05-04 at 10:00 AM")
    parts = time_slot.split(" at ")
    apt_date = parts[0] if len(parts) > 1 else str(datetime.date.today())
    apt_time = parts[1] if len(parts) > 1 else time_slot
    
    # Save to MongoDB
    appointments_collection.insert_one({
        "booking_id": booking_id,
        "doctor_details": doctor_selection,
        "date": apt_date,
        "time_slot": apt_time,
        "created_at": datetime.datetime.utcnow()
    })
    
    # Parse date and time if possible to generate a good calendar link
    # Converting '2026-05-04' to '20260504'
    cal_date = apt_date.replace("-", "")
    
    # Map basic times to UTC (mock approach for Google Calendar link)
    time_map = {
        "10:00 AM": ("T100000Z", "T110000Z"),
        "11:00 AM": ("T110000Z", "T120000Z"),
        "02:00 PM": ("T140000Z", "T150000Z"),
        "04:30 PM": ("T163000Z", "T173000Z"),
        "05:30 PM": ("T173000Z", "T183000Z"),
    }
    
    t_start, t_end = time_map.get(apt_time, ("T100000Z", "T110000Z"))
    start_time = f"{cal_date}{t_start}"
    end_time = f"{cal_date}{t_end}"
    
    text = quote(f"Appointment with {doctor_selection}")
    details = quote(f"Booking ID: {booking_id}\nBooked via AI Health Assistant.")
    
    cal_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={text}&dates={start_time}/{end_time}&details={details}"
    
    return f"Booking Confirmed! ID: {booking_id}\n\nPlease give this exact link to the user: [Add to Google Calendar]({cal_link})"

if __name__ == "__main__":
    mcp.run(transport="stdio")
