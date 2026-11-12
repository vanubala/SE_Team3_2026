## Reliability

The most important quality attribute in our project is reliability. Since the parcel management system facilitates serves many parties and entities it is important that one the parcel management system doesn't allow one or several errors to impact our core service. If for example, one locker goes offline or one door jams, that locker's parcels move to a "Locker Unavailable" status (FR_04) and all other lockers and compartments should keep operating nominally. Operations should use proper concurrency control, so no event is lost or mismanaged. Our target is 99.5% uptime.
