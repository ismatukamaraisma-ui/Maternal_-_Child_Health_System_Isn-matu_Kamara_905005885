import hashlib
import json
import os
from datetime import date
from getpass import getpass

DATA_FILE = "mchc_data.json"
MAX_ATTEMPTS = 3
# Change this to your institution's real access code.
INSTITUTION_PIN = "MCHC2026"

# Tuples: fixed values that must never change while the program runs.
DEFAULT_VACCINES = ("BCG", "Polio 1", "Polio 2")
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class Person:
    """Base class: a name and a password that is stored only as a hash."""

    def __init__(self, full_name, password=None, password_hash=None):
        self.full_name = full_name
        if password_hash is None:
            password_hash = Person.hash_password(password)
        self.__password_hash = password_hash

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, entered_password):
        return Person.hash_password(entered_password) == self.__password_hash

    def get_password_hash(self):
        return self.__password_hash

    @staticmethod
    def is_valid_name(name):
        letters = 0
        for character in name:
            if character.isalpha():
                letters += 1
            elif character not in " -'.":
                return False
        return letters >= 2

    @staticmethod
    def is_valid_password(password):
        return len(password) >= 6

    @staticmethod
    def normalize_phone(phone):
        return phone.replace(" ", "").replace("-", "")

    @staticmethod
    def is_valid_phone(phone):
        digits = phone
        if phone.startswith("+"):
            digits = phone[1:]
        return digits.isdecimal() and 8 <= len(digits) <= 15

    @staticmethod
    def is_valid_address(address):
        return len(address) >= 3

    @staticmethod
    def split_date(text):
        """Turn 'DD-MM-YYYY' into a tuple (day, month, year), or None if the format is wrong."""
        parts = text.split("-")
        if len(parts) != 3:
            return None
        day_text, month_text, year_text = parts
        if not (day_text.isdecimal() and month_text.isdecimal() and year_text.isdecimal()):
            return None
        if len(day_text) != 2 or len(month_text) != 2 or len(year_text) != 4:
            return None
        return (int(day_text), int(month_text), int(year_text))

    @staticmethod
    def is_valid_date(text):
        parts = Person.split_date(text)
        if parts is None:
            return False
        day, month, year = parts  # tuple unpacking
        if year < 1900 or month < 1 or month > 12:
            return False
        days_this_month = DAYS_IN_MONTH[month - 1]
        if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            days_this_month = 29
        if day < 1 or day > days_this_month:
            return False
        if date(year, month, day) > date.today():
            return False
        return True

    @staticmethod
    def today_text():
        today = date.today()
        return str(today.day).zfill(2) + "-" + str(today.month).zfill(2) + "-" + str(today.year)

    @staticmethod
    def same_text(first, second):
        return " ".join(first.lower().split()) == " ".join(second.lower().split())


class Vaccination:
    def __init__(self, name, completed=False, date_completed=None):
        self.name = name
        self.completed = completed
        self.date_completed = date_completed

    def get_status(self):
        if not self.completed:
            return "Due"
        if self.date_completed is None:
            return "Completed"
        return "Completed (" + self.date_completed + ")"

    def mark_completed(self, date_given):
        self.completed = True
        self.date_completed = date_given

    def to_list(self):
        return [self.name, self.completed, self.date_completed]

    @classmethod
    def from_list(cls, data):
        name, completed, date_completed = data
        return cls(name, completed, date_completed)


class Patient(Person):
    ANTENATAL = "Antenatal"
    POSTNATAL = "Postnatal"
    total_patients = 0

    def __init__(self, full_name, password, care_type, child_name, phone, address,
                 patient_id=None, password_hash=None, last_visit="",
                 history=None, vaccinations=None):
        super().__init__(full_name, password, password_hash)
        self.care_type = care_type
        self.child_name = child_name
        self.phone = phone
        self.address = address
        if patient_id is None:
            patient_id = Patient.generate_patient_id()
        self.patient_id = patient_id
        self.last_visit = last_visit
        self.history = history if history is not None else []
        if vaccinations is None:
            vaccinations = []
            if care_type == Patient.POSTNATAL:
                vaccinations = Patient.default_vaccinations()
        self.vaccinations = vaccinations

    @classmethod
    def generate_patient_id(cls):
        cls.total_patients += 1
        return "MCH" + str(cls.total_patients).zfill(3)

    @staticmethod
    def default_vaccinations():
        return [Vaccination(name) for name in DEFAULT_VACCINES]

    def is_antenatal(self):
        return self.care_type == Patient.ANTENATAL

    def get_last_visit(self):
        if self.last_visit == "":
            return "No visit yet"
        return self.last_visit

    def add_visit_note(self, note, staff_name):
        visit_date = Person.today_text()
        self.history.append(visit_date + " - " + note + " (by " + staff_name + ")")
        self.last_visit = visit_date

    def has_vaccine(self, vaccine_name):
        for vaccine in self.vaccinations:
            if Person.same_text(vaccine.name, vaccine_name):
                return True
        return False

    def add_vaccination(self, vaccine_name):
        self.vaccinations.append(Vaccination(vaccine_name))

    def display_basic(self):
        print("\n===== PATIENT INFORMATION =====")
        print("Patient ID   : " + self.patient_id)
        print("Care Type    : " + self.care_type)
        print("Mother Name  : " + self.full_name)
        if not self.is_antenatal():
            print("Child Name   : " + self.child_name)
        print("Phone Number : " + self.phone)
        print("Address      : " + self.address)
        print("Last Visit   : " + self.get_last_visit())

    def display_history(self):
        print("\n===== PATIENT HISTORY =====")
        if len(self.history) == 0:
            print("No history recorded yet.")
        for item in self.history:
            print("- " + item)

    def display_vaccinations(self):
        print("\n===== IMMUNIZATION STATUS =====")
        if self.is_antenatal():
            print("Not applicable yet. Immunization starts after the baby is born (postnatal).")
            return
        if len(self.vaccinations) == 0:
            print("No vaccinations recorded yet.")
        for vaccine in self.vaccinations:
            print("- " + vaccine.name + ": " + vaccine.get_status())

    def display_full_record(self):
        self.display_basic()
        self.display_history()
        self.display_vaccinations()

    @staticmethod
    def print_table_header():
        header = f"{'No.':<4}{'ID':<8}{'Type':<11}{'Mother':<22}{'Child':<20}{'Phone':<16}{'Last Visit':<12}"
        print(header)
        print("-" * len(header))

    def display_table_row(self, number):
        child = "-" if self.is_antenatal() else self.child_name
        print(f"{number:<4}{self.patient_id:<8}{self.care_type:<11}{self.full_name:<22.21}"
              f"{child:<20.19}{self.phone:<16}{self.get_last_visit():<12}")

    def to_list(self):
        return [
            self.patient_id,
            self.get_password_hash(),
            self.full_name,
            self.care_type,
            self.child_name,
            self.phone,
            self.address,
            self.last_visit,
            self.history,
            [vaccine.to_list() for vaccine in self.vaccinations],
        ]

    @classmethod
    def from_list(cls, data):
        (patient_id, password_hash, full_name, care_type, child_name, phone,
         address, last_visit, history, vaccine_items) = data
        return cls(
            full_name=full_name,
            password=None,
            care_type=care_type,
            child_name=child_name,
            phone=phone,
            address=address,
            patient_id=patient_id,
            password_hash=password_hash,
            last_visit=last_visit,
            history=history,
            vaccinations=[Vaccination.from_list(item) for item in vaccine_items],
        )


class Staff(Person):
    HEALTH_WORKER = "Health Worker"
    RECEPTIONIST = "Receptionist"
    total_staff = 0

    def __init__(self, full_name, password, role, staff_id=None, password_hash=None):
        super().__init__(full_name, password, password_hash)
        self.role = role
        if staff_id is None:
            staff_id = Staff.generate_staff_id(role)
        self.staff_id = staff_id

    @classmethod
    def generate_staff_id(cls, role):
        cls.total_staff += 1
        prefix = "HW" if role == Staff.HEALTH_WORKER else "RC"
        return prefix + str(cls.total_staff).zfill(3)

    def to_list(self):
        return [self.staff_id, self.get_password_hash(), self.full_name, self.role]

    @classmethod
    def from_list(cls, data):
        staff_id, password_hash, full_name, role = data
        return cls(full_name, None, role, staff_id, password_hash)


class MCHCSystem:
    def __init__(self):
        self.patients = []
        self.staff_members = []
        # One key is added here for every failed attempt (a list is the only data structure used).
        self.failed_attempts = []
        self.staff_signup_locked = False

    # ---------- Saving and loading ----------
    def save_data(self):
        data = [
            Patient.total_patients,
            Staff.total_staff,
            [patient.to_list() for patient in self.patients],
            [staff.to_list() for staff in self.staff_members],
        ]
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        except OSError as error:
            print("\nWarning: could not save data (" + str(error) + ").")

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("unexpected file format")
            total_patients, total_staff, patient_items, staff_items = data
            self.patients = [Patient.from_list(item) for item in patient_items]
            self.staff_members = [Staff.from_list(item) for item in staff_items]
            Patient.total_patients = total_patients
            Staff.total_staff = total_staff
        except (ValueError, TypeError, OSError):
            print("\nWarning: saved data could not be read. The system will start empty.")
            try:
                os.replace(DATA_FILE, DATA_FILE + ".bak")
            except OSError:
                pass
            self.patients = []
            self.staff_members = []
            Patient.total_patients = 0
            Staff.total_staff = 0

    # ---------- Input helpers ----------
    @staticmethod
    def ask(prompt):
        try:
            return input(prompt).strip()
        except EOFError:
            raise SystemExit

    @staticmethod
    def ask_hidden(prompt):
        try:
            return getpass(prompt).strip()
        except EOFError:
            raise SystemExit

    def ask_required(self, prompt):
        while True:
            value = self.ask(prompt)
            if value != "":
                return value
            print("This field cannot be empty.")

    def ask_name(self, prompt):
        while True:
            value = self.ask(prompt)
            if Person.is_valid_name(value):
                return value
            print("Please enter a valid name (letters only, at least 2 characters).")

    def ask_phone(self, prompt):
        while True:
            value = Person.normalize_phone(self.ask(prompt))
            if Person.is_valid_phone(value):
                return value
            print("Please enter a valid phone number (8 to 15 digits).")

    def ask_address(self, prompt):
        while True:
            value = self.ask(prompt)
            if Person.is_valid_address(value):
                return value
            print("Please enter a valid address (at least 3 characters).")

    def ask_new_password(self):
        while True:
            password = self.ask_hidden("Create a password (at least 6 characters): ")
            if not Person.is_valid_password(password):
                print("Password is too short. Use at least 6 characters.")
                continue
            if self.ask_hidden("Confirm your password: ") != password:
                print("The passwords do not match. Please try again.")
                continue
            return password

    def ask_date_or_today(self, prompt):
        while True:
            value = self.ask(prompt)
            if value == "":
                return Person.today_text()
            if Person.is_valid_date(value):
                return value
            print("Please enter a valid date as DD-MM-YYYY, or press Enter for today.")

    def ask_care_type(self, allow_back=False):
        while True:
            print("\nIs the patient Antenatal or Postnatal?")
            print("1. Antenatal (pregnant, baby not yet born)")
            print("2. Postnatal (baby has been born)")
            if allow_back:
                print("3. Go back")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                return Patient.ANTENATAL
            if choice == "2":
                return Patient.POSTNATAL
            if allow_back and choice == "3":
                return None
            print("\nInvalid option!")

    def pause(self):
        self.ask("\nPress Enter to continue...")

    @staticmethod
    def print_id_card(title, card_id):
        print("\n+------------------------------------+")
        print("  " + title)
        print("  " + card_id)
        print("+------------------------------------+")

    # ---------- Lookups ----------
    def find_patient(self, patient_id):
        for patient in self.patients:
            if patient.patient_id.lower() == patient_id.lower():
                return patient
        return None

    def find_staff(self, staff_id, role):
        for staff in self.staff_members:
            if staff.staff_id.lower() == staff_id.lower() and staff.role == role:
                return staff
        return None

    def find_duplicate(self, mother_name, phone):
        for patient in self.patients:
            if Person.same_text(patient.full_name, mother_name) and patient.phone == phone:
                return patient
        return None

    def select_patient(self):
        patient_id = self.ask_required("\nEnter Patient ID: ")
        patient = self.find_patient(patient_id)
        if patient is None:
            print("\nNo Such Patient Registered!")
        return patient

    def print_patient_table(self, patients):
        if len(patients) == 0:
            print("\nNo patients registered yet.")
            return
        print()
        Patient.print_table_header()
        for number, patient in enumerate(patients, start=1):
            patient.display_table_row(number)
        print("\nTotal patients: " + str(len(patients)))

    def search_patient(self, full):
        query = self.ask_required("\nEnter Patient ID or name to search: ").lower()
        matches = []
        for patient in self.patients:
            if (patient.patient_id.lower() == query
                    or query in patient.full_name.lower()
                    or query in patient.child_name.lower()):
                matches.append(patient)

        if len(matches) == 0:
            print("\nNo Such Patient Registered!")
        elif len(matches) == 1:
            if full:
                matches[0].display_full_record()
            else:
                matches[0].display_basic()
        else:
            print("\n" + str(len(matches)) + " patients found:")
            self.print_patient_table(matches)
            print("Search again with an exact Patient ID to see one record.")

    # ---------- Login protection ----------
    def is_locked(self, key):
        return self.failed_attempts.count(key) >= MAX_ATTEMPTS

    def clear_failures(self, key):
        self.failed_attempts = [item for item in self.failed_attempts if item != key]

    def register_failure(self, key):
        """Returns True when the account has just become locked."""
        self.failed_attempts.append(key)
        count = self.failed_attempts.count(key)
        if count >= MAX_ATTEMPTS:
            print("\nToo many failed attempts. This account is locked until the system is restarted.")
            return True
        print("Attempts left: " + str(MAX_ATTEMPTS - count))
        return False

    # ---------- Registration and sign up ----------
    def register_patient(self, by_staff, care_type=None):
        print("\n--- Register New Patient ---")
        if care_type is None:
            care_type = self.ask_care_type(allow_back=True)
            if care_type is None:
                return None

        print("\nRegistering an " + care_type + " patient.")
        mother_name = self.ask_name("Enter Mother's Name: ")
        child_name = ""
        if care_type == Patient.POSTNATAL:
            child_name = self.ask_name("Enter Child's Name: ")
        phone = self.ask_phone("Enter Phone Number: ")
        address = self.ask_address("Enter Address: ")

        duplicate = self.find_duplicate(mother_name, phone)
        if duplicate is not None:
            print("\nPatient Already Registered!")
            if by_staff:
                print("Patient ID: " + duplicate.patient_id)
            else:
                print("Please go back and choose 'I forgot my ID' to get your ID.")
            return None

        if by_staff:
            print("\nAsk the patient to create her own password.")
        password = self.ask_new_password()

        patient = Patient(mother_name, password, care_type, child_name, phone, address)
        self.patients.append(patient)
        self.save_data()

        print("\nCongratulations! You have successfully registered.")
        self.print_id_card("PATIENT ID", patient.patient_id)
        print("Please do not forget this ID and password. You need both to log in.")
        return patient

    def staff_sign_up(self, role):
        print("\n--- " + role + " Sign Up ---")
        if self.staff_signup_locked:
            print("Staff sign-up is locked until the system is restarted.")
            return None

        verified = False
        for attempt in range(1, MAX_ATTEMPTS + 1):
            pin = self.ask_hidden("Enter the institution PIN: ")
            if Person.hash_password(pin) == Person.hash_password(INSTITUTION_PIN):
                verified = True
                break
            print("Wrong institution PIN. Attempts left: " + str(MAX_ATTEMPTS - attempt))

        if not verified:
            self.staff_signup_locked = True
            print("\nToo many wrong PINs. Staff sign-up is locked until the system is restarted.")
            return None

        name = self.ask_name("Enter your full name: ")
        password = self.ask_new_password()
        staff = Staff(name, password, role)
        self.staff_members.append(staff)
        self.save_data()

        print("\nSign up successful!")
        self.print_id_card("YOUR STAFF ID", staff.staff_id)
        print("Please write this ID down. You need it and your password to log in.")
        self.pause()
        return staff

    # ---------- Log in ----------
    def staff_login(self, role):
        print("\n--- " + role + " Log In ---")
        while True:
            staff_id = self.ask_required("Enter your Staff ID: ")
            key = "staff:" + staff_id.lower()

            if self.is_locked(key):
                print("\nThis account is locked until the system is restarted.")
                return None

            staff = self.find_staff(staff_id, role)
            if staff is None:
                print("\nThis ID is not registered. Please sign up first.")
                return None

            password = self.ask_hidden("Enter your password: ")
            if staff.check_password(password):
                self.clear_failures(key)
                print("\nWelcome, " + staff.full_name + "!")
                return staff

            print("\nWrong password.")
            if self.register_failure(key):
                return None

    def patient_login(self, care_type):
        print("\n--- " + care_type + " Patient Log In ---")
        while True:
            patient_id = self.ask_required("Enter your Patient ID: ")
            key = "patient:" + patient_id.lower()

            if self.is_locked(key):
                print("\nThis account is locked until the system is restarted.")
                return None

            patient = self.find_patient(patient_id)
            if patient is None:
                print("\nThis ID is not registered. Please sign up first.")
                return None

            if patient.care_type != care_type:
                print("\nThis ID is registered as a " + patient.care_type + " patient. "
                      "Please go back and choose " + patient.care_type + ".")
                return None

            password = self.ask_hidden("Enter your password: ")
            if patient.check_password(password):
                self.clear_failures(key)
                print("\nWelcome back, " + patient.full_name + "!")
                return patient

            print("\nWrong password.")
            if self.register_failure(key):
                return None

    def recover_patient_id(self):
        """A mother who forgot her ID proves who she is with name, address and phone."""
        print("\n--- Forgot My ID ---")
        name = self.ask_required("Enter your name (mother's name): ")
        key = "recover:" + " ".join(name.lower().split())
        if self.is_locked(key):
            print("\nRecovery is locked for this name until the system is restarted.")
            return
        address = self.ask_required("Enter your Address: ")
        phone = Person.normalize_phone(self.ask_required("Enter your Phone Number: "))

        for patient in self.patients:
            if (Person.same_text(patient.full_name, name)
                    and Person.same_text(patient.address, address)
                    and patient.phone == phone):
                print("\nYour Patient ID is " + patient.patient_id + ". Please keep it safe.")
                self.clear_failures(key)
                return

        print("\nThose details do not match any patient.")
        self.register_failure(key)

    # ---------- Menus ----------
    def patient_menu(self, patient):
        patient.display_full_record()
        while True:
            print("\n===== PATIENT MENU =====")
            print("Logged in as: " + patient.full_name + " (" + patient.patient_id + ")")
            print("1. View my information")
            print("2. View my history")
            print("3. View my immunization status")
            print("4. Log out")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                patient.display_basic()
            elif choice == "2":
                patient.display_history()
            elif choice == "3":
                patient.display_vaccinations()
            elif choice == "4":
                print("\nYou have been logged out.")
                return
            else:
                print("\nInvalid option!")

    def receptionist_menu(self, staff):
        while True:
            print("\n===== RECEPTIONIST MENU =====")
            print("Logged in as: " + staff.full_name + " (" + staff.staff_id + ")")
            print("1. Register new patient")
            print("2. View all patients")
            print("3. Search patient")
            print("4. Log out")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                self.register_patient(by_staff=True)
            elif choice == "2":
                self.print_patient_table(self.patients)
            elif choice == "3":
                self.search_patient(full=False)
            elif choice == "4":
                print("\nYou have been logged out.")
                return
            else:
                print("\nInvalid option!")

    def health_worker_menu(self, staff):
        while True:
            print("\n===== HEALTH WORKER MENU =====")
            print("Logged in as: " + staff.full_name + " (" + staff.staff_id + ")")
            print("1. Register new patient")
            print("2. View all patients")
            print("3. Search patient")
            print("4. View patient history")
            print("5. View immunization status")
            print("6. Add visit note")
            print("7. Update immunization")
            print("8. Log out")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                self.register_patient(by_staff=True)
            elif choice == "2":
                self.print_patient_table(self.patients)
            elif choice == "3":
                self.search_patient(full=True)
            elif choice == "4":
                patient = self.select_patient()
                if patient is not None:
                    patient.display_history()
            elif choice == "5":
                patient = self.select_patient()
                if patient is not None:
                    patient.display_vaccinations()
            elif choice == "6":
                self.add_visit_note(staff)
            elif choice == "7":
                self.update_immunization()
            elif choice == "8":
                print("\nYou have been logged out.")
                return
            else:
                print("\nInvalid option!")

    # ---------- Health worker actions ----------
    def add_visit_note(self, staff):
        patient = self.select_patient()
        if patient is None:
            return
        note = self.ask_required("Enter visit note: ")
        patient.add_visit_note(note, staff.full_name)
        self.save_data()
        print("\nVisit note added for " + patient.full_name + " (" + patient.patient_id + ").")

    def update_immunization(self):
        patient = self.select_patient()
        if patient is None:
            return
        if patient.is_antenatal():
            print("\n" + patient.full_name + " is an Antenatal patient. "
                  "Immunization can only be updated after the baby is born.")
            return

        while True:
            patient.display_vaccinations()
            print("\n1. Mark a vaccine as completed")
            print("2. Add a new vaccine")
            print("3. Back")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                self.mark_vaccine_completed(patient)
            elif choice == "2":
                self.add_vaccine(patient)
            elif choice == "3":
                return
            else:
                print("\nInvalid option!")

    def mark_vaccine_completed(self, patient):
        if len(patient.vaccinations) == 0:
            print("\nNo vaccines to update.")
            return
        print()
        for number, vaccine in enumerate(patient.vaccinations, start=1):
            print(str(number) + ". " + vaccine.name + " - " + vaccine.get_status())

        text = self.ask("\nEnter the number of the vaccine: ")
        if not text.isdecimal() or not 1 <= int(text) <= len(patient.vaccinations):
            print("\nInvalid vaccine number!")
            return

        vaccine = patient.vaccinations[int(text) - 1]
        if vaccine.completed:
            print("\n" + vaccine.name + " is already marked as completed.")
            return

        date_given = self.ask_date_or_today("Date given (DD-MM-YYYY, or press Enter for today): ")
        vaccine.mark_completed(date_given)
        self.save_data()
        print("\n" + vaccine.name + " marked as completed.")

    def add_vaccine(self, patient):
        name = self.ask_required("Enter the new vaccine name: ")
        if patient.has_vaccine(name):
            print("\nThat vaccine is already on the list.")
            return
        patient.add_vaccination(name)
        self.save_data()
        print("\n" + name + " added as Due.")

    # ---------- Welcome flow ----------
    def patient_entry(self):
        care_type = self.ask_care_type(allow_back=True)
        if care_type is None:
            return
        while True:
            print("\n--- Patient (" + care_type + ") ---")
            print("Please enter:")
            print("1. To log in")
            print("2. To sign up")
            print("3. I forgot my ID")
            print("4. To go back")
            choice = self.ask("\nChoose an option: ")
            if choice == "1" or choice == "2":
                if choice == "1":
                    patient = self.patient_login(care_type)
                else:
                    patient = self.register_patient(by_staff=False, care_type=care_type)
                    if patient is not None:
                        self.pause()
                if patient is not None:
                    self.patient_menu(patient)
                    return
            elif choice == "3":
                self.recover_patient_id()
            elif choice == "4":
                return
            else:
                print("\nInvalid option!")

    def staff_entry(self, role):
        while True:
            print("\n--- " + role + " ---")
            print("Please enter:")
            print("1. To log in")
            print("2. To sign up")
            print("3. To go back")
            choice = self.ask("\nChoose an option: ")
            if choice == "1" or choice == "2":
                if choice == "1":
                    staff = self.staff_login(role)
                else:
                    staff = self.staff_sign_up(role)
                if staff is not None:
                    if role == Staff.HEALTH_WORKER:
                        self.health_worker_menu(staff)
                    else:
                        self.receptionist_menu(staff)
                    return
            elif choice == "3":
                return
            else:
                print("\nInvalid option!")

    def run(self):
        self.load_data()
        while True:
            print("\n=====================================")
            print("     Hello, welcome to the MCHC")
            print("=====================================")
            print("Please enter:")
            print("1. To use as a Health Worker")
            print("2. To use as a Patient")
            print("3. To use as a Receptionist")
            print("4. To exit")
            choice = self.ask("\nChoose an option: ")
            if choice == "1":
                self.staff_entry(Staff.HEALTH_WORKER)
            elif choice == "2":
                self.patient_entry()
            elif choice == "3":
                self.staff_entry(Staff.RECEPTIONIST)
            elif choice == "4":
                self.save_data()
                print("\nYou have exited the system. Goodbye.")
                return
            else:
                print("\nInvalid option!")


def main():
    system = MCHCSystem()
    try:
        system.run()
    except (SystemExit, KeyboardInterrupt):
        system.save_data()
        print("\nInput closed. Goodbye.")


if __name__ == "__main__":
    main()
