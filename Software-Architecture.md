## The main quality attributes

1. Reliability 
2. Security
3. Usability


## Software Architecture
For our Smart Parcel Locker System we are going for a hybrid architectural approach by going for a Layered Client-Server Architecture with Event-Driven Elements : 
- Client-Server (Overall System): multiple clients (Courier Dashboard, Recipient Portal, Admin View and Physical Locker) communicate over HTTPS/REST API with a shared backend server and database. They need real-time access to compartment availabity and parcel status, but they shoudn't have access to the database directly.
- Layered Architecture (Internal Backend ) : Based on our sequence diagrams --> easier to understand and to divide between the members. Helps with security and information hiding.
- Event-driven elements : mostly for sending asynchronous notification (Notification Gateway) when the parcel has been deposited in its assigned compartment but can be used for hardware malfunction detection, and expiration reminders.
## Security

Security is the most important part of our system. The system logs actions, for traceability and accountability. Furthermore, we ensure that the right entity receives access to the appropriate resources through role-based access control (FR_05), secure login on every endpoint (NFR_01), and pickup codes that are random, unique and single-use, with a 15-minute lockout after 5 wrong attempts (NFR_06). Personal and customs data is encrypted and deleted on request (NFR_02, NFR_03).

## Reliability

Reliability is core to our system. Since the parcel management system facilitates serves many parties and entities it is important that one the parcel management system doesn't allow one or several errors to impact our core service. If for example, one locker goes offline or one door jams, that locker's parcels move to a "Locker Unavailable" status (FR_04) and all other lockers and compartments should keep operating nominally. Operations should use proper concurrency control, so no event is lost or mismanaged. Our target is 99.5% uptime.

## Usability

Usability is key to a smooth experience for all parties. Recipients do not need to log in to track their parcel: they can use the secure code provided by our system, or receive SMS updates on the number the courier registered for them or that they signed up with. Pickup is then two steps to maintain simplicity: enter the code or tap "open" in the app (FR_07), then take the parcel. Opening through the app is only allowed if the phone number has been verified against the one the courier provided. A courier gets a compartment suggested by parcel size (C6) and only needs to confirm it. To avoid long waits, pages respond in under 2 seconds (NFR_04) and a compartment opens within 3 seconds of a valid code (NFR_05). Where usability conflicts with security, such as the lockout after wrong codes, we choose security, which goes back to the principle that we cannot maximise all attributes.
