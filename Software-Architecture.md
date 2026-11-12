## Security

Security is the most important part of our system. The system logs actions, for traceability and accountability. Furthermore, we ensure that the right entity receives access to the appropriate resources through role-based access control (FR_05), secure login on every endpoint (NFR_01), and pickup codes that are random, unique and single-use, with a 15-minute lockout after 5 wrong attempts (NFR_06). Personal and customs data is encrypted and deleted on request (NFR_02, NFR_03).

## Reliability

Reliability is core to our system. Since the parcel management system facilitates serves many parties and entities it is important that one the parcel management system doesn't allow one or several errors to impact our core service. If for example, one locker goes offline or one door jams, that locker's parcels move to a "Locker Unavailable" status (FR_04) and all other lockers and compartments should keep operating nominally. Operations should use proper concurrency control, so no event is lost or mismanaged. Our target is 99.5% uptime.

