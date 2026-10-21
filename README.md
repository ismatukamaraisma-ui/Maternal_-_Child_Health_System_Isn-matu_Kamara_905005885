READ ME
MATERNAL AND CHILD HEALTH CLINIC SYSTEM (MCHC)

About the project:
MCHC is a Python console program built with Object-Oriented Programming. It solves a real health problem: keeping track of mothers and their children at a Maternal and Child Health Clinic. It belongs to the Health domain, as a Patient Record System with vaccination tracking.
A mother registers as an Antenatal patient (baby not yet born) or a Postnatal patient (baby born) and receives an automatically generated Patient ID (for example MCH001). Health workers record visit notes and update the child’s immunization status. Staff members receive their own ID (for example HW001 or RC002) when they sign up.

Features:
Register a new patient with mother’s name, child’s name (postnatal only), phone number, address and password
Patient ID and staff ID generated automatically
Three user roles: Patient, Receptionist and Health Worker, each with its own menu
Patients log in to view their own information, history and immunization status
Receptionists register patients, view all patients and search by ID or name
Health workers can also add visit notes, view history and update immunizations
Default vaccines (BCG, Polio 1, Polio 2) added for postnatal patients, with new vaccines and completion dates recorded
Staff sign-up protected by an institution PIN
A “Forgot my ID” option that checks name, address and phone number
Input checks and clear messages, such as “Wrong password.” and “Attempts left: 2”
Accounts locked after 3 failed login attempts
Duplicate patients blocked (same mother name and phone number)
Data is saved to a local file and reloaded when the program starts




How it meets Digital Public Goods (DPG) standards

Open-source: the full source code is public on GitHub, and anyone can read, run and improve it.
Inclusive and accessible: it uses simple numbered text menus and plain-language prompts. It needs no internet, no installation beyond Python, and no special hardware. Every menu has a “go back” or “log out” option, and every wrong input gets a helpful message.
Privacy-respecting: passwords are never stored as plain text, because only a SHA-256 hash is kept. Patients see only their own record, and receptionists cannot see visit history or immunization details. Records are saved only in a local file (mchc_data.json) on the user’s own computer and are never sent anywhere. This file holds contact details and health notes, so it is excluded from GitHub with .gitignore. Only the code is public, never real patient data.
Modular and reusable: the code is split into separate classes (Person, Vaccination, Patient, Staff, MCHCSystem), and each class can be reused in another project.

Security note:
The institution PIN for staff sign-up is set in the code as INSTITUTION_PIN. The value in this public repository is only an example. Any institution using the program must change it to its own secret code before real use.

OOP concepts used
Concept	Place being used
Classes, attributes and objects	Person, Vaccination, Patient, Staff and MCHCSystem
Data structure: list	self.patients and self.staff_members in MCHCSystem, plus history and vaccinations in Patient
Tuples	DEFAULT_VACCINES and DAYS_IN_MONTH constants, and split_date returning (day, month, year)
Instance methods	add_visit_note, check_password, get_status, mark_completed, display_full_record
Class methods	generate_patient_id, generate_staff_id, from_list
Static methods	hash_password, is_valid_phone, is_valid_date, default_vaccinations
Inheritance	Patient and Staff extend Person
Encapsulation	Private __password_hash in Person



Project structure:
mchc.py: the whole program (all classes and the main menu)
mchc_data.json: created automatically when the program runs, and not uploaded to GitHub

How to run:
Install Python 3.8 or newer. No extra libraries are needed.
Download mchc.py into a folder.
Open a terminal in that folder and run: python mchc.py
