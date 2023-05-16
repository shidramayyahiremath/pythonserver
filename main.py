from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = '__C10ud93r5__'

db_file = 'mydatabase.db'

is_loggedin =0
# Create tables call befoere running app

def create_tables():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Create the 'users' table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                           (userid INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT NOT NULL,
                           password TEXT NOT NULL,
                           is_logged_in INTEGER DEFAULT 0)''')

        # Create the 'car_data' table
        cursor.execute('''CREATE TABLE IF NOT EXISTS car_data
                        (userid INTEGER,
                        carname TEXT NOT NULL,
                        temperature REAL NOT NULL,
                        fanspeed INTEGER NOT NULL,
                        FOREIGN KEY (userid) REFERENCES users(userid))''')


def insert_user(username, password):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Insert a new user into the 'users' table
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()


def insert_car_data(userid, carname, temperature, fanspeed):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Insert car data into the 'car_data' table
        cursor.execute(
            "INSERT INTO car_data (userid, carname, temperature, fanspeed) VALUES (?, ?, ?, ?)",
            (userid, carname, temperature, fanspeed)
        )
        conn.commit()

@app.route('/signup', methods=['POST'])
def signup():
    try:
        username =request.args.get('username')
        password=request.args.get('password')
    except Exception as e:
        raise Exception('Error authenticating user: ' + str(e))
def get_user_id(username):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Execute the query to get the user ID
        cursor.execute("SELECT userid FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        return result[0] if result else None


def get_car_data(userid):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()

        # Execute the query to get the car data for the user
        cursor.execute("SELECT carname, temperature, fanspeed FROM car_data WHERE userid = ?", (userid,))
        result = cursor.fetchone()

        return result if result else None


@app.errorhandler(500)
def internal_server_error(error):
    response = {
        'message': 'Internal Server Error',
        'error': str(error)
    }
    return jsonify(response), 500


def authenticate_user(username, password):
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()

            # Execute the query to check the username and password
            query = "SELECT * FROM users WHERE username = ? AND password = ?"
            cursor.execute(query, (username, password))
            result = cursor.fetchone()

            if result:
                print("Username and password match.")
                return True
            else:
                print("Invalid username or password.")
                return False

    except Exception as e:
        raise Exception('Error authenticating user: ' + str(e))

def update_login_status(userid, is_logged_in):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_logged_in = ? WHERE userid = ?", (int(is_logged_in), userid))
    conn.commit()
    conn.close()

@app.route('/login', methods=['POST'])
def login():
    try:
        # Extract username and password from the request headers
        username = request.args.get('username')
        password = request.args.get('password')
        print("username:" + username)
        print("password" + password)
        # Check the username and password against the database
        if authenticate_user(username, password):
            print("Username and password match.")
            # Get the user ID for the authenticated user
            userid = get_user_id(username)
            is_loggedin =1;
            update_login_status(userid, is_loggedin)
            car_data = get_car_data(userid)

            if car_data:
                carname, temperature, fan_speed = car_data
                response = {
                    'userid':userid,
                    'car': carname,
                    'temperature': temperature,
                    'fan_speed': fan_speed
                }
            else:
                response = {
                    'message': 'No car data found for the user.'
                }
        else:
            response = {
                'message': 'Authentication failed. Invalid username or password.'
            }

        return jsonify(response)

    except Exception as e:
        # Handle any exceptions or errors that occurred
        response = {
            'message': 'Internal Server Error',
            'error': str(e)
        }
        return jsonify(response), 500


@app.route('/logout', methods=['POST'])
def logout():
    try:
        userid = request.form.get('userid')
        is_loggedin =0
        if not userid:
            return jsonify({"error": "Missing userid parameter"})

        if is_user_exists(userid):
            return jsonify({"userid": userid, "status": True})
        else:
            return jsonify({"userid": userid, "status": False})

    except Exception as e:
        return jsonify({"error": str(e)})


def is_user_exists(userid):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    update_logged_in_status(userid, 0)
    # Execute a query to check if the user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE userid = ?", (userid,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    # Return True if the user exists, False otherwise
    return result[0] == 1


def update_logged_in_status(userid, is_logged_in):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_logged_in = ? WHERE userid = ?", (int(is_logged_in), userid))
    conn.commit()
    conn.close()


@app.route('/getAvailableVehicles', methods=['GET'])
def getAvailableVehicles():
    try:
        if request.method == 'GET':
            userid = request.args.get('userid')
            # Retrieve the available vehicles for the user from the database
            available_vehicles = fetch_available_vehicles(userid)
            # Return the response with the available vehicles
            return jsonify({"vehicleVIns": available_vehicles})
        # Handle other request methods
        return jsonify({"error": "Error message"})

    except Exception as e:
        return jsonify({"error": str(e)})


def fetch_available_vehicles(userid):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Execute the query to retrieve available vehicles for the user
    cursor.execute("SELECT carname FROM car_data WHERE userid = ?", (userid,))

    results = cursor.fetchall()

    # Close the connection
    conn.close()

    # Extract the vehicle names from the results
    available_vehicles = [result[0] for result in results]

    return available_vehicles


@app.route('/getUserOptions', methods=['GET'])
def getUserOptions():
    try:
        if request.method == 'GET':
            userid = request.args.get('userid')

            # Retrieve the temperature and fan speed options for the user from the database
            user_options = fetch_user_options(userid)

            if user_options:
                temperature, fan_speed = user_options
                # Return the response with the user options
                return jsonify({"userid": userid, "temperature": temperature, "fan_speed": fan_speed})
            else:
                # User options not found
                return jsonify({"error": "User options not found"})

        # Handle other request methods
        return jsonify({"error": "Error message"})
    except Exception as e:
        return jsonify({"error": str(e)})


def fetch_user_options(userid):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Execute the query to retrieve temperature and fan speed options for the user
    cursor.execute("SELECT temperature, fanspeed FROM car_data WHERE userid = ?", (userid,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    return result  # Returns a tuple (temperature, fan_speed) or None if not found


@app.route('/setUserOptions', methods=['POST'])
def setUserOptions():
    try:
        if request.method == 'POST':
            userid = request.form.get('userid')
            temperature = request.form.get('temperature')
            fan_speed = request.form.get('fanspeed')
            car_name = request.form.get('carname')
            # Update the temperature and fan speed options for the user in the database
            success = update_user_options(userid, car_name, temperature, fan_speed)

            if success:
                return jsonify({"userid": userid, "status": "Options updated successfully"})
            else:
                return jsonify({"error": "Failed to update user options"})

        # Handle other request methods
        return jsonify({"error": "Error message"})
    except Exception as e:
        return jsonify({"error": str(e)})


def update_user_options(userid, carname, temperature, fan_speed):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM car_data WHERE userid = ?", (userid,))
    # Check if there is an existing entry for the user in the database
    cursor.execute("SELECT COUNT(*) FROM car_data WHERE userid = ?", (userid,))
    result = cursor.fetchone()

    if result[0] > 0:
        # An existing entry exists for the user, update the options
        cursor.execute("UPDATE car_data SET carname=?, temperature = ?, fanspeed = ? WHERE userid = ?",
                       (temperature, fan_speed, userid))
    else:
        # No existing entry, insert a new entry
        cursor.execute("INSERT INTO car_data (userid, carname, temperature, fanspeed) VALUES (?, ?, ?, ?)",
                       (userid, carname, temperature, fan_speed))

    # Commit the changes to the database
    conn.commit()
    # Check if the update was successful
    success = cursor.rowcount > 0
    # Close the connection
    conn.close()
    return success  # Returns True if the update was successful, False otherwise


if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    create_tables()
    # Inserting a new user
    insert_user("John", "123")

    # Retrieving the user ID for John
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM users WHERE username = 'John'")
    userid = cursor.fetchone()[0]
    print(userid)
    conn.close()

    # Inserting car data for John
    insert_car_data(userid, "Honda", 29, 5)
    app.run()
