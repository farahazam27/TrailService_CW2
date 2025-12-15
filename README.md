# TrailService API (MAL2018 CW2)

**Student ID:** BSCS2509261
**Module:** Information Management & Retrieval

## Project Overview
This project is a RESTful micro-service designed to manage hiking trail data for the "Trail Application". It allows users to Create, Read, Update, and Delete (CRUD) trails stored in a Microsoft SQL Server database.

The API is built using **Python (Flask)** and documents its endpoints automatically using **Swagger UI**.

## Features
* **CRUD Operations:** Full management of trail data (Name, Length, Location, Difficulty, etc.).
* **Security (LSEP):** Integrated with the University of Plymouth Authenticator API.
    * *Create, Update, and Delete* operations require valid University credentials.
    * *Read* operations are public.
* **Data Integrity:** Validates Foreign Keys (User_ID, Difficulty_ID) before insertion.
* **Documentation:** Interactive API documentation via Swagger.

## Technologies Used
* **Python 3.x**
* **Flask & Flask-RESTx** (Web Framework)
* **PyODBC** (Database Connection)
* **Microsoft SQL Server** (Backend Database)
* **Swagger UI** (API Documentation)

## Prerequisites
To run this project, you must have:
1.  Python installed.
2.  Access to a Microsoft SQL Server instance (Localhost or University Server).
3.  The `CW2` Database Schema set up (using the provided SQL script).

## How to Run
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/farahazam27/TrailService_CW2.git](https://github.com/farahazam27/TrailService_CW2.git)
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    python app.py
    ```
4.  **Access the API:**
    Open your browser and navigate to: `http://127.0.0.1:5000/swagger`

## Authentication Guide
To test the secure endpoints (POST, PUT, DELETE), you must provide valid University credentials in the JSON Request Body:

```json
{
  "Email": "ada@plymouth.ac.uk",
  "Password": "insecurePassword",
  "Trail_Name": "Test Trail",
  ...
}
