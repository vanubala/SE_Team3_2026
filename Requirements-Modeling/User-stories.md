#original combined usecase diagram before re-formatting

@startuml SmartParcelLocker_Combined
left to right direction
skinparam packageStyle rectangle
skinparam actorStyle default
skinparam usecase {
  BackgroundColor #F1F1F1
  BorderColor #555555
}

' ===== Primary actors (left) =====
actor "Recipient" as Recipient
actor "Courier" as Courier
actor "Administrator" as Admin

' ===== Secondary actors (right) =====
actor "Locker Hardware" as Locker <<Actor>>
actor "Notification Gateway" as Gateway <<Service>>
actor "Maintenance Team" as Maint <<Actor>>

rectangle "Smart Parcel Locker System" {

  ' ---- Courier use cases ----
  usecase "Authenticate Courier" as UC_AuthCourier
  usecase "Register Parcel" as UC_Register
  usecase "Assign Compartment" as UC_Assign
  usecase "Deposit Parcel" as UC_Deposit
  usecase "Report Exception" as UC_ReportEx

  ' ---- Recipient use cases ----
  usecase "Authenticate Recipient" as UC_AuthRecipient
  usecase "Track Parcel" as UC_Track
  usecase "Receive Pickup Notif & Code" as UC_Notif
  usecase "Pickup Parcel" as UC_Pickup
  usecase "Report Issue" as UC_ReportIssue

  ' ---- Administrator use cases ----
  usecase "Authenticate Admin" as UC_AuthAdmin
  usecase "Visualise Locker Availabilities" as UC_Visualise
  usecase "Receive Operational Status" as UC_OpStatus
  usecase "Change Locker Status" as UC_ChangeStatus
  usecase "Report to Maintenance Team" as UC_ReportMaint
}

' ===== Courier associations =====
Courier --> UC_Register
Courier --> UC_Deposit

UC_Register ..> UC_AuthCourier : <<include>>
UC_Assign   ..> UC_Register    : <<include>>
UC_Deposit  ..> UC_Assign      : <<include>>
UC_ReportEx ..> UC_Deposit     : <<extend>>\n(if issue during deposit)

UC_Deposit --> Locker

' ===== Recipient associations =====
Recipient --> UC_Track
Recipient --> UC_Pickup

UC_Track  ..> UC_AuthRecipient : <<include>>
UC_Pickup ..> UC_Notif         : <<include>>
UC_ReportIssue ..> UC_Pickup   : <<extend>>\n(if door jammed, code unreadable, empty locker)

UC_Notif  --> Gateway
UC_Pickup --> Locker

' ===== Administrator associations =====
Admin --> UC_Visualise
Admin --> UC_OpStatus

UC_Visualise ..> UC_AuthAdmin : <<include>>
UC_OpStatus  ..> UC_AuthAdmin : <<include>>
UC_ChangeStatus ..> UC_OpStatus : <<extend>>\n(after operational fault)
UC_ReportMaint  ..> UC_OpStatus : <<extend>>\n(if hardware fault detected)

UC_OpStatus     --> Locker
UC_ChangeStatus --> Locker
UC_ReportMaint  --> Maint

@enduml
