
# Medical Clinic AI Administrator

A Telnyx-powered voice AI assistant that handles appointment scheduling, patient inquiries, and administrative tasks for a medical practice. Built with Flask, FastMCP, and deployed on Railway. Frontend deployed on Vercel.

## Use Case

Healthcare administration involves significant phone-based work: collecting patient information, scheduling appointments, and managing practice logistics. This project demonstrates how Telnyx Voice AI can automate these tasks, allowing medical staff to focus on patient care while the AI handles routine scheduling operations.

## Try It Now

**Phone Number:** `1-406-381-2086`

**Live Dashboard:** [https://telnyx-assignment-dashboard.vercel.app/](https://telnyx-assignment-dashboard.vercel.app/)

> **Note:** Your phone number will need to be verified in the Telnyx system to place calls.

### Demo Script

Call the number above and try these interactions:

1.  **Check available doctors:**
    
    -   "What doctors are available?"
    -   "Who can I see?"
2.  **Book an appointment:**
    
    -   "I'd like to book an appointment with Dr. Smith for tomorrow at 2 PM"
    -   Provide your name and phone number when asked
    -   Confirm the details
3.  **Check availability:**
    
    -   "What times are available with Dr. Jones on Friday, December 17th, 2025?"
4.  **Reschedule an appointment:**
    
    -   "I need to reschedule my appointment with ID 21"
    -   Provide the new date and time
5.  **View your appointments:**
    
    -   "What appointments do I have?"

The dashboard updates in real-time as you interact with the bot.

##  Architecture

```
┌─────────────┐
│   Caller    │
└──────┬──────┘
       │ (Voice)
       ▼
┌─────────────┐
│   Telnyx    │ ◄── Dynamic Webhook Variables
│  Voice AI   │     (Caller Context)
└──────┬──────┘
       │ (Tool Calls)
       ▼
┌─────────────┐
│ MCP Server  │ ◄── Custom tools for appointments
│  (FastMCP)  │     doctors, availability, etc.
└──────┬──────┘
       │ (HTTP)
       ▼
┌─────────────┐
│  Flask API  │ ◄── REST endpoints
│             │     Database operations
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │ (Production) / SQLite (Local)
└─────────────┘

```

### Components

-   **Telnyx Voice AI**: Handles voice interactions and natural language understanding
-   **MCP Server**: Provides tools for the AI assistant to query and modify appointment data
-   **Flask API**: RESTful backend managing appointments, patients, and doctors
-   **PostgreSQL/SQLite**: Database with dual support (Postgres in production, SQLite for local dev)
-   **Frontend Dashboard**: Real-time view of appointments and practice data

##  Core Functionality

 **AI Assistant**: Telnyx Voice AI configured with custom receptionist prompts  
**MCP Server Integration**: 6 custom tools (get_doctors, check_availability, book_appointment, reschedule_appointment, cancel_appointment, get_appointments)  
 **Dynamic Webhook Variables**: Caller context retrieval for personalized greetings  
**Public Deployment**: All services deployed on Railway, frontend on Vercel

##  Tech Stack

### Backend

-   **Python**
-   **Flask** - REST API framework
-   **PostgreSQL** / **SQLite** - Database (production/development)
-   **FastMCP** - Model Context Protocol server
-   **psycopg** - PostgreSQL adapter
-   **httpx** - HTTP client for async operations

### Frontend

-   **HTML/CSS/JavaScript**  - Dashboard interface
-   **Vercel** - Frontend hosting

### Infrastructure

-   **Railway** - Backend and MCP server hosting
-   **Telnyx** - Voice AI platform

## Live Deployments

Service

URL

**Frontend Dashboard**

[https://telnyx-assignment-dashboard.vercel.app/](https://telnyx-assignment-dashboard.vercel.app/)

**Flask API**

[https://telnyx-assignment-production.up.railway.app/sanity](https://telnyx-assignment-production.up.railway.app/sanity)

Can also use /doctors, /appointments and /patients to see those specific JSON endpoints 

**MCP Server**

[https://web-production-24917.up.railway.app/mcp](https://web-production-24917.up.railway.app/mcp)

### API Endpoints

-   `GET /doctors` - List all doctors
-   `GET /patients` - List all patients
-   `GET /appointments` - List appointments (optional `?patient_phone=` filter)
-   `GET /appointments/available?doctor_id=&date=` - Check available time slots (i.e. https://telnyx-assignment-production.up.railway.app/appointments/available?doctor_id=1&date=2025-12-15)
-   `POST /appointments` - Book new appointment
-   `PUT /appointments/<id>` - Update appointment (reschedule or cancel)
-   `POST /webhook/caller-context` - Dynamic webhook for caller information
NOTE- JSON body needed for POST/PUT requests

## GitHub Repositories

-   **Flask API**: [https://github.com/grantkazan/telnyx-assignment](https://github.com/grantkazan/telnyx-assignment)
-   **MCP Server**: [https://github.com/grantkazan/weather-mcp](https://github.com/grantkazan/weather-mcp)
-   **Dashboard**: [https://github.com/grantkazan/telnyx-assignment-dashboard](https://github.com/grantkazan/telnyx-assignment-dashboard)

## Key Features

### Dynamic Caller Recognition

When existing patients call, the webhook retrieves their name. “Thank you for calling…Hi Grant!”

### Data Validation

-   Prevents scheduling appointments in the past
-   Prevents double-booking patients
-   Validates date formats and handles leap years
-   Checks doctor availability before booking

### Confirmation Workflow

The bot confirms all appointment details before booking:

-   Patient name and phone number
-   Doctor name
-   Date and time
-   Waits for explicit user confirmation

### Real-time Dashboard

View all appointments, doctors, and patients in a clean web interface that updates as changes occur through the voice system.

## Testing Coverage

### Happy Path Scenarios

-   Get list of available doctors
-   Check available time slots for a specific doctor and date
-   Retrieve appointment information by appointment ID
-   List all appointments for a patient
-   Book appointment as a new patient (hard to test due to phone number requirements in Telnyx platform)
-   Book appointment as an existing patient
-   Reschedule an existing appointment

### Error Handling Scenarios

-   Prevents double-booking doctors at the same time
-   Rejects invalid dates (e.g., February 35th, September 31st)
-   Correctly identifies leap years (no Feb 29, 2027)
-   Rejects appointments with non-existent doctors
-   Handles user errors gracefully (e.g., sneezing during input, repeating information)
-   Prevents scheduling appointments in the past
-   Prevents patient conflicts (same patient, same time, different doctors)

## Known Issues & Limitations

### Conversational Context

-   When rescheduling multiple appointments in one call, the bot may reference the first appointment ID fetched rather than subsequent ones
-   **Workaround**: Separate calls for multiple appointment updates

### Validation Edge Cases

-   Canceling a non-existent appointment ID returns success (should return 404)
-   Bot confirmation accepts incomplete data if user says "confirm" without providing required info
-   **Note**: Backend validation works correctly; these are UX improvements

### Voice Recognition

-   Phone numbers require clear enunciation for accurate capture
-   Anonymous/blocked caller IDs route to voicemail
-   Bot doesn't explicitly end call after goodbye (continues listening)

### Time Constraints

-   Technically allows appointments 1+ seconds in the future (no minimum buffer time)
-   **Note**: In practice, voice conversation adds 30+ second natural delay

## Future Improvements

### Priority Enhancements

-   **Better appointment management**: Reference appointments by context ("my next appointment") instead of requiring IDs
-   **Waitlist feature**: Call patients when appointments become available due to cancellations
-   **Enhanced patient data**: Support updating phone numbers, addresses, insurance information, etc.
-   **Minimum booking buffer**: Enforce 5-10 minute minimum lead time for appointments. Or other lead time.

### User Experience

-   Multi-appointment conversation tracking improvements
-   More explicit confirmation when appointment details are incomplete
-   Automatic call termination on goodbye

### FINAL NOTE

- All testing and demos can be done with the frontend web page and phone number.
- I'd imagine it's possible to clone all repos and run everything locally, however, I haven't tried this since getting everything working on both, my machine and publicly. 
- It's highly likely your mileage may vary when attempting to clone the repos and set everything else up. Especially regarding ports and environment variables.

