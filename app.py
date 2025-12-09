from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
import pyodbc
import requests
from decimal import Decimal

app = Flask(__name__)

# 1. CONFIGURATION 

DB_SERVER = 'localhost'
DB_DATABASE = 'MAL2018'
DB_USERNAME = 'SA' 
DB_PASSWORD = 'C0mp2001!' 

# Using SQL Server driver
conn_str = f'DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD}'

# 2. SWAGGER / API SETUP

api = Api(app, 
          version='1.0', 
          title='Trail Service API (CW2)', 
          description='A micro-service for managing hiking trails',
          doc='/swagger') 

ns = api.namespace('trails', description='Trail operations')

# 3. DATA MODELS

# MODEL 1:  CREATE & UPDATE 
trail_model = api.model('Trail', {
    'Email': fields.String(required=True, description='University Email (e.g. ada@plymouth.ac.uk)'),
    'Password': fields.String(required=True, description='University Password'),
    'Trail_Name': fields.String(required=True, description='Name of the trail'),
    'Description': fields.String(description='Trail description'),
    'Length_km': fields.Float(required=True, description='Length in KM'),
    'Start_Location': fields.String(required=True, description='Start point'),
    'End_Location': fields.String(required=True, description='End point'),
    'Difficulty_ID': fields.Integer(required=True, description='1=Easy, 2=Moderate, 3=Hard'),
    'RouteType_ID': fields.Integer(required=True, description='1=Loop, 2=Out&Back, etc'),
    'User_ID': fields.Integer(required=True, description='ID of the user creating the trail')
})

# MODEL 2: DELETE
auth_model = api.model('AuthOnly', {
    'Email': fields.String(required=True, description='University Email'),
    'Password': fields.String(required=True, description='University Password')
})

# 4. HELPER FUNCTIONS

def get_db_connection():
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def check_auth(json_data):
    """Reusable function to check University Auth"""
    user_email = json_data.get('Email')
    user_password = json_data.get('Password')
    
    if not user_email or not user_password:
         return False, "Email and Password are required."

    auth_url = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"
    credentials = {"email": user_email, "password": user_password}
    
    try:
        response = requests.post(auth_url, json=credentials)
        if response.status_code != 200:
            return False, "Authentication Failed! Invalid credentials."
        
        verified_user = response.json()
        if verified_user[1] != 'True': 
             return False, "Authentication Failed!"
             
        return True, "Success"
    except Exception as e:
        return False, f"Service Error: {str(e)}"

# 5. ROUTES

@ns.route('/')
class TrailList(Resource):
    @ns.doc('list_trails')
    def get(self):
        """List all trails (Public - No Auth needed)"""
        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}, 500
        
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM CW2.TrailDetailsView") 
            trails = []
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))

                for key, value in row_dict.items():
                    if isinstance(value, Decimal):
                        row_dict[key] = float(value)
                trails.append(row_dict)
            return trails, 200
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @ns.doc('create_trail')
    @ns.expect(trail_model)
    def post(self):
        """Create a new trail (Authentication Required)"""
        data = request.json
        
        # 1. SECURITY CHECK
        is_valid, message = check_auth(data)
        if not is_valid:
            return {"message": message}, 401

        # 2. DATABASE INSERT
        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}, 500
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                EXEC CW2.AddTrail ?, ?, ?, ?, ?, ?, ?, ?
            """, 
            data['User_ID'], data['Difficulty_ID'], data['RouteType_ID'], 
            data['Trail_Name'], data['Description'], data['Length_km'], 
            data['Start_Location'], data['End_Location']
            )
            conn.commit()
            return {'message': 'Trail created successfully'}, 201
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

@ns.route('/<int:id>')
@ns.response(404, 'Trail not found')
@ns.param('id', 'The Trail identifier')
class Trail(Resource):
    @ns.doc('get_trail')
    def get(self, id):
        """Fetch a trail (Public - No Auth needed)"""
        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}, 500
        cursor = conn.cursor()
        try:
            cursor.execute("EXEC CW2.GetTrail ?", id)
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                result = dict(zip(columns, row))
    
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                return result, 200
            else:
                return {'message': 'Trail not found'}, 404
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()
        
    @ns.doc('update_trail')
    @ns.expect(trail_model)
    def put(self, id):
        """Update a trail (Authentication Required)"""
        data = request.json

        # 1. SECURITY CHECK 
        is_valid, message = check_auth(data)
        if not is_valid:
            return {"message": message}, 401

        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}, 500
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Trail_ID FROM CW2.Trail WHERE Trail_ID = ?", id)
            if not cursor.fetchone():
                return {'message': 'Trail not found'}, 404

            cursor.execute("""
                EXEC CW2.UpdateTrail ?, ?, ?, ?, ?, ?, ?, ?, ?
            """, 
            id,                     
            data['Trail_Name'], data['Description'], data['Length_km'],      
            data['Start_Location'], data['End_Location'], data['Difficulty_ID'],  
            data['RouteType_ID'], data['User_ID']         
            )
            conn.commit()
            return {'message': 'Trail updated successfully'}, 200
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

    @ns.doc('delete_trail')
    @ns.expect(auth_model) 
    def delete(self, id):
        """Delete a trail (Authentication Required)"""
        data = request.json

        # 1. SECURITY CHECK
        # Check if data exists 
        if not data:
             return {"message": "Authentication required. Please provide Email and Password."}, 400

        is_valid, message = check_auth(data)
        if not is_valid:
            return {"message": message}, 401

        conn = get_db_connection()
        if not conn:
            return {"error": "Database connection failed"}, 500
        cursor = conn.cursor()
        try:
            cursor.execute("EXEC CW2.DeleteTrail ?", id)
            conn.commit()
            return {'message': 'Trail deleted'}, 204
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)