import mysql.connector
from faker import Faker

fake = Faker()

def generate_person_with_assets():
    person_data = {
        "name": fake.name(),
        "address": fake.address(),
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "assets": generate_random_assets()
    }
    return person_data

def generate_random_assets():
    num_assets = fake.random_int(min=5, max=10)
    assets = []

    for _ in range(num_assets):
        asset = {
            "asset_type": fake.random_element(elements=("Real Estate", "Stocks", "Vehicles", "Jewelry", "Cash", "Laptops", "Mobiles")),
            "asset_count": fake.random_int(min=1, max=50),
            "asset_value": fake.random_int(min=1000, max=1000000)
        }
        assets.append(asset)

    return assets

def create_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="DBMS*fall2023",
            database="assets"
        )
        cursor = conn.cursor()

        # Create a table to store person data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            address VARCHAR(255),
            email VARCHAR(255),
            phone_number VARCHAR(20)
        )
        """)

        # Create a table to store asset data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            person_id INT,
            asset_type VARCHAR(50),
            asset_count INT,
            asset_value INT,
            FOREIGN KEY (person_id) REFERENCES people (id)
        )
        """)

        conn.commit()
        print("Database created successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            conn.close()

def insert_data_into_database(person_data):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="DBMS*fall2023",
            database="assets"
        )
        cursor = conn.cursor()

        # Insert person data
        cursor.execute("""
        INSERT INTO people (name, address, email, phone_number)
        VALUES (%s, %s, %s, %s)
        """, (person_data["name"], person_data["address"], person_data["email"], person_data["phone_number"]))

        person_id = cursor.lastrowid  # Get the ID of the inserted person

        # Insert asset data
        for asset in person_data["assets"]:
            cursor.execute("""
            INSERT INTO assets (person_id, asset_type, asset_count, asset_value)
            VALUES (%s, %s, %s, %s)
            """, (person_id, asset["asset_type"], asset["asset_count"], asset["asset_value"]))

        conn.commit()
        print("Data inserted into the MySQL database.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            conn.close()

if __name__ == "__main__":
    create_database()

    person_data = generate_person_with_assets()
    insert_data_into_database(person_data)