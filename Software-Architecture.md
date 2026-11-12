## The main quality attributes

1. Reliability 
2. Security
3. Usability


## Software Architecture
For our Smart Parcel Locker System we are going for a hybrid architectural approach by going for a Layered Client-Server Architecture with Event-Driven Elements : 
- Client-Server (Overall System): multiple clients (Courier Dashboard, Recipient Portal, Admin View and Physical Locker) communicate over HTTPS/REST API with a shared backend server and database. They need real-time access to compartment availabity and parcel status, but they shoudn't have access to the database directly.
- Layered Architecture (Internal Backend ) : Based on our sequence diagrams --> easier to understand and to divide between the members. Helps with security and information hiding.
- Event-driven elements : mostly for sending asynchronous notification (Notification Gateway) when the parcel has been deposited in its assigned compartment but can be used for hardware malfunction detection, and expiration reminders.