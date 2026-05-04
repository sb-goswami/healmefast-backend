import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("Error: MONGODB_URI is not set in .env")
    exit(1)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client["hospital_db"]
doctors_collection = db["doctors"]
appointments_collection = db["appointments"]

DOCTORS = [
    # 1. Cardiologists
    {"id": "DOC-C1", "name": "Dr. R. Sharma", "specialty": "Cardiologist", "exp": "15 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-C2", "name": "Dr. S. Gupta", "specialty": "Cardiologist", "exp": "10 Yrs", "hospital": "Max Care Heart Institute"},
    {"id": "DOC-C3", "name": "Dr. A. Verma", "specialty": "Cardiologist", "exp": "20 Yrs", "hospital": "City Central Hospital"},
    
    # 2. Endocrinologists
    {"id": "DOC-E1", "name": "Dr. K. Patel", "specialty": "Endocrinologist", "exp": "12 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-E2", "name": "Dr. N. Singh", "specialty": "Endocrinologist", "exp": "8 Yrs", "hospital": "Fortis Care"},
    {"id": "DOC-E3", "name": "Dr. P. Nair", "specialty": "Endocrinologist", "exp": "25 Yrs", "hospital": "City Central Hospital"},
    
    # 3. Dermatologists
    {"id": "DOC-D1", "name": "Dr. A. Kulkarni", "specialty": "Dermatologist", "exp": "5 Yrs", "hospital": "Skin City Clinic"},
    {"id": "DOC-D2", "name": "Dr. M. Banerjee", "specialty": "Dermatologist", "exp": "14 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-D3", "name": "Dr. S. Iyer", "specialty": "Dermatologist", "exp": "9 Yrs", "hospital": "Fortis Care"},
    
    # 4. Orthopedics
    {"id": "DOC-O1", "name": "Dr. T. Reddy", "specialty": "Orthopedic", "exp": "18 Yrs", "hospital": "Max Care Bone & Joint"},
    {"id": "DOC-O2", "name": "Dr. S. Das", "specialty": "Orthopedic", "exp": "9 Yrs", "hospital": "City Central Hospital"},
    {"id": "DOC-O3", "name": "Dr. R. Mehra", "specialty": "Orthopedic", "exp": "22 Yrs", "hospital": "Apollo Hospital"},
    
    # 5. General Physicians
    {"id": "DOC-G1", "name": "Dr. M. Joshi", "specialty": "General Physician", "exp": "5 Yrs", "hospital": "Neighborhood Clinic"},
    {"id": "DOC-G2", "name": "Dr. V. Rao", "specialty": "General Physician", "exp": "25 Yrs", "hospital": "City Central Hospital"},
    {"id": "DOC-G3", "name": "Dr. L. Fernandez", "specialty": "General Physician", "exp": "11 Yrs", "hospital": "Apollo Hospital"},

    # 6. Neurologists
    {"id": "DOC-N1", "name": "Dr. A. Bhatia", "specialty": "Neurologist", "exp": "16 Yrs", "hospital": "NeuroBrain Institute"},
    {"id": "DOC-N2", "name": "Dr. P. Sen", "specialty": "Neurologist", "exp": "12 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-N3", "name": "Dr. K. Desai", "specialty": "Neurologist", "exp": "21 Yrs", "hospital": "Max Care"},

    # 7. Pediatricians
    {"id": "DOC-P1", "name": "Dr. S. Agarwal", "specialty": "Pediatrician", "exp": "8 Yrs", "hospital": "Kids Care Clinic"},
    {"id": "DOC-P2", "name": "Dr. N. Menon", "specialty": "Pediatrician", "exp": "14 Yrs", "hospital": "Fortis Care"},
    {"id": "DOC-P3", "name": "Dr. J. Kaur", "specialty": "Pediatrician", "exp": "20 Yrs", "hospital": "City Central Hospital"},

    # 8. Psychiatrists
    {"id": "DOC-PS1", "name": "Dr. R. Kapoor", "specialty": "Psychiatrist", "exp": "15 Yrs", "hospital": "Mind Wellness Center"},
    {"id": "DOC-PS2", "name": "Dr. M. Ali", "specialty": "Psychiatrist", "exp": "10 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-PS3", "name": "Dr. V. Sharma", "specialty": "Psychiatrist", "exp": "25 Yrs", "hospital": "City Central Hospital"},

    # 9. Gynecologists
    {"id": "DOC-GY1", "name": "Dr. A. Gupta", "specialty": "Gynecologist", "exp": "12 Yrs", "hospital": "Women's Health Clinic"},
    {"id": "DOC-GY2", "name": "Dr. S. Reddy", "specialty": "Gynecologist", "exp": "18 Yrs", "hospital": "Max Care"},
    {"id": "DOC-GY3", "name": "Dr. P. Chopra", "specialty": "Gynecologist", "exp": "8 Yrs", "hospital": "Fortis Care"},

    # 10. Gastroenterologists
    {"id": "DOC-GA1", "name": "Dr. T. Jain", "specialty": "Gastroenterologist", "exp": "14 Yrs", "hospital": "Digestive Health Institute"},
    {"id": "DOC-GA2", "name": "Dr. R. Naidu", "specialty": "Gastroenterologist", "exp": "20 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-GA3", "name": "Dr. M. Patel", "specialty": "Gastroenterologist", "exp": "7 Yrs", "hospital": "City Central Hospital"},

    # 11. Pulmonologists
    {"id": "DOC-PU1", "name": "Dr. K. Singhal", "specialty": "Pulmonologist", "exp": "15 Yrs", "hospital": "Lung Care Center"},
    {"id": "DOC-PU2", "name": "Dr. V. Dubey", "specialty": "Pulmonologist", "exp": "11 Yrs", "hospital": "Max Care"},
    {"id": "DOC-PU3", "name": "Dr. S. Chatterjee", "specialty": "Pulmonologist", "exp": "22 Yrs", "hospital": "Apollo Hospital"},

    # 12. Oncologists
    {"id": "DOC-ON1", "name": "Dr. A. Mathur", "specialty": "Oncologist", "exp": "25 Yrs", "hospital": "Cancer Treatment Center"},
    {"id": "DOC-ON2", "name": "Dr. N. Joshi", "specialty": "Oncologist", "exp": "18 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-ON3", "name": "Dr. P. Yadav", "specialty": "Oncologist", "exp": "12 Yrs", "hospital": "Fortis Care"},

    # 13. Ophthalmologists
    {"id": "DOC-OP1", "name": "Dr. S. Bansal", "specialty": "Ophthalmologist", "exp": "10 Yrs", "hospital": "Clear Vision Eye Care"},
    {"id": "DOC-OP2", "name": "Dr. M. Khanna", "specialty": "Ophthalmologist", "exp": "16 Yrs", "hospital": "Max Care"},
    {"id": "DOC-OP3", "name": "Dr. R. Mishra", "specialty": "Ophthalmologist", "exp": "20 Yrs", "hospital": "City Central Hospital"},

    # 14. ENT Specialists
    {"id": "DOC-EN1", "name": "Dr. K. Ahuja", "specialty": "ENT Specialist", "exp": "8 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-EN2", "name": "Dr. T. Roy", "specialty": "ENT Specialist", "exp": "15 Yrs", "hospital": "City Central Hospital"},
    {"id": "DOC-EN3", "name": "Dr. V. Prasad", "specialty": "ENT Specialist", "exp": "24 Yrs", "hospital": "Fortis Care"},

    # 15. Urologists
    {"id": "DOC-UR1", "name": "Dr. A. Saxena", "specialty": "Urologist", "exp": "12 Yrs", "hospital": "Kidney Care Clinic"},
    {"id": "DOC-UR2", "name": "Dr. M. Soni", "specialty": "Urologist", "exp": "19 Yrs", "hospital": "Apollo Hospital"},
    {"id": "DOC-UR3", "name": "Dr. R. Bhatt", "specialty": "Urologist", "exp": "14 Yrs", "hospital": "Max Care"}
]

def seed_db():
    print("Clearing existing doctors...")
    doctors_collection.delete_many({})
    
    print("Clearing existing test appointments...")
    appointments_collection.delete_many({})
    
    print(f"Inserting {len(DOCTORS)} doctors into hospital_db...")
    doctors_collection.insert_many(DOCTORS)
    
    print("✅ Seed successful!")
    print("\nDoctors in DB:")
    for doc in doctors_collection.find():
        print(f" - {doc['name']} ({doc['specialty']})")

if __name__ == "__main__":
    seed_db()
