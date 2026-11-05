# Use case selected: Register a Parcel (Courier)

**Precondition:** be logged in and have a valid JWT.

## Frontend (`CourierDashboard`)
The courier arrives at their dashboard upon successful authentication. The dashboard provides a visual overview of existing registered parcels, packages awaiting compartment assignment, and upcoming deliveries.

From the dashboard, the courier opens the **Parcel Registration Form** to input parcel details into the system:
- **Barcode / External ID** — from the barcode or the external service that is sending the parcel; this is shared with the user for tracking purposes
- **Size of Package** — `SMALL`, `MEDIUM`, `LARGE`.
- **Expected Delivery Date & Time**
- **Any extra notes** — ex : Optional instructions (e.g., "Fragile", "Handle with care").


The courier is also informed that the parcel has been successfully or unsuccessfully registered with feedback on what went wrong in the latter case.

## Backend (on POST)

### 1. Controller Layer (`RegistrationController`)
- Accepts the incoming HTTP POST request containing the courier's form payload.
- Delegates the initilization to the `RegistrationService`.

### 2. Service Layer (`RegistrationService`)
Enforces validation, data manipulation and domain constraints rules : 
1. Sanitization
2. Format and Constrains Validation : required fields, IDs format, dates 
3. Check for duplicates : using tracking IDs
4. Create Parcel Entity:
   - Generates **parcel ID**, a secure, unique identifier within the system (for assignment, delivery at the locker etc.) from a hash of the barcode / external ID
   - Sets the barcode / internal ID as the **tracking number**
   - Initializes the **status** of the parcel to `REGISTERED`
   - Sets the parcel's pickup **deadline** using the esstimated delivery date  
   - Records the time and date
5. Send the `Parcel` object to the data repository where it will stored.
6. Return a payload to the controller with SUCCESS status and parcelID, or throw error if validation fails


### 3. Data Access Layer (`ParcelRepository`)
1. Receives the initialized `Parcel` entity from `ParcelService`.
2. Saves the record directly into the `Parcels` database table/collection.
- **On Success:** Returns the confirmed stored entity record back to the service layer.
- **On Error:** Returns a error response, which the service layer catches to generate readable feedback for the UI.