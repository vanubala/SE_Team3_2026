## Stakeholders:

Primary: Courier (Requirement provider, validator), Recipient (Requirement provider, validator, Administrator (Requirement provider, decision-maker, validator)
Secondary: Host businesses (Requirement provider, constraint source), Senders (Requirement provider, validator)

External: Administration des douanes et accises (Constraint source, requirement provider), EU regulations (Constraint source, requirement provider)
Hidden: IT operations and development team (Maintainer/operator), locker hardware company and their maintenance team (Domain expert, constraint source)


| Activity | Tasks |
|---|---|
| Deliver a parcel (courier) | Log in (FR_05, FR_10, FR_13, NFR_01); register the parcel; choose a compartment (FR_12, FR_27, NFR_04); place and confirm (FR_03, FR_09, NFR_05) |
| Track a parcel (recipient) | Log in (FR_01, FR_05, NFR_01); find the parcel (FR_06, NFR_04); follow its status (FR_03, FR_04, FR_06) |
| Collect a parcel (recipient) | Get notified (FR_15, FR_16, FR_23); find the locker; open the compartment (FR_02, FR_07, FR_19, FR_20, NFR_05, NFR_06) |
| Monitor lockers (administrator) | Check availability (FR_25, NFR_04); change locker status |
| Manage the network (administrator) | Edit locations, compartments and courier accounts (FR_05, FR_11, FR_21, NFR_01) |
| Send a parcel (sender) | Create the shipment (FR_01, FR_19, FR_23); drop off at a locker (FR_26, FR_27, NFR_05); follow the delivery (FR_03, FR_06); handle returns (FR_04, FR_22, FR_24) |



## Conflicts

| Conflict | Perspective 1 | Perspective 2 |
|---|---|---|
| Pickup deadline | Recipients: long deadlines and extensions. | Management and couriers: compartments freed quickly to keep capacity for new parcels. |
| Privacy vs investigation | Administrators and customs: full recipient details and long history. | EU: data minimisation and short retention. |
| Opening hours | Recipients: 24/7 access to their parcel. | Host businesses: access only during their opening hours, no disturbance. |
| Cost vs quality | Management: low development and operating cost. | Recipients and IT team: SMS alerts, offline locker mode, 99.5% uptime. |


## Requirements

### Functional requirements

| ID | Requirement |
|---|---|
| FR_01 | Users can register with email or phone. |
| FR_02 | Guest recipients (no account) can collect parcels using only the code sent via SMS/email. |
| FR_03 | The system should support parcel statuses such as: Registered → In Transit → Ready for Pickup → Collected. |
| FR_04 | The system should support exceptional statuses such as: Delayed, Customs Hold, Locker Unavailable, Pickup Expired, and Returned to Sender. |
| FR_05 | Role-based access control: recipient, sender, courier, administrator. |
| FR_06 | Recipients, senders and administrators can view parcel history, active parcels, and receipts. |
| FR_07 | Recipient opens the compartment by entering the PIN or tapping "open" in the app via Bluetooth/NFC when on site. |
| FR_08 | Users can delete their account. |
| FR_09 | Courier can report exceptions: parcel damaged, doesn't fit, wrong locker, door jammed. |
| FR_10 | Courier logs in and sees the list of parcels assigned to that locker. |
| FR_11 | Admins can register a locker site with location (GPS, address), opening hours, access restrictions (e.g. inside a mall), with photos. |
| FR_12 | A courier can see the locker locations and the free compartments of each size at a location. |
| FR_13 | Couriers authenticate on the terminal via app QR code, or PIN, tied to their carrier company. |
| FR_14 | Courier collects expired, returned, or sender-dropped parcels; each removal is scanned and confirmed. |
| FR_15 | Templates are configurable per language, users can switch the language. |
| FR_16 | Reminders are sent to recipients before expiry. |
| FR_17 | Recipient can extend the pickup deadline once (paid option). |
| FR_18 | An administrator can export the customs records for one parcel or a date range when customs makes an official request. The export contains only the fields customs needs, and each export is logged with who made it, when, and the request reference. |
| FR_19 | Payment for sending and overdue fees via card. |
| FR_20 | Cash-on-delivery: pickup is blocked until payment is confirmed in the app or at a terminal card reader. |
| FR_21 | Configurable pricing per locker, size and region. |
| FR_22 | When the pickup window ends, the parcel is marked "expired" and added to the courier's collection list. |
| FR_23 | Integration with SMS/email/push providers and payment gateways. |
| FR_24 | Refunds for failed or cancelled services. |
| FR_25 | Automatic alerts on anomalies: door left open, forced opening, offline terminal, power on battery, temperature out of range. |
| FR_26 | At the terminal, the sender enters the code, the right-size compartment opens, the parcel is deposited, and a receipt is issued. |
| FR_27 | Allocation picks the smallest compartment that fits, to maximize utilization. |


### Non-functional requirements

| ID | Requirement |
|---|---|
| NFR_01 | All login endpoints must be secure. |
| NFR_02 | If a user deletes their account, their data must be removed from the system database within 24 hours. |
| NFR_03 | Encrypt customs-relevant backlogs in accordance with GDPR requirements. |
| NFR_04 | Page loads and searches must respond in < 2 seconds for 95% of requests under normal load. |
| NFR_05 | A compartment must open in < 3 seconds after a valid pickup code is entered. |
| NFR_06 | Pickup codes must be random, unique and single-use, becoming invalid after collection or expiry. Code entry must be locked for 15 minutes after 5 incorrect attempts. |
