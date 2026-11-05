Use case selected: Register a Parcel (Courier)

Methods:

Classes:

## Description / Overview

**Precondition:** be logged in and have a valid JWT.

### Input (courier, on the app UI)

The courier fills out the information:

- **Barcode / internal ID** — from the barcode or the internal courier DB; this is shared with the user for tracking purposes
- **Size of package**
- **Expected delivery date and time**
- **Any extra notes**

### Backend (on POST)

1. This POST arrives to our servers.
2. We sanitize.
3. We ensure all mandatory fields are filled and all character boundaries / characteristics are met.
4. We then use methods to calculate:
   - **parcel ID** from a hash of the barcode / internal ID
   - set the barcode / internal ID as the **tracking number**
   - set the **status** of the parcel to `Registered`
   - set the parcel **deadline**
5. We then add all of this to our DB of Parcels.
