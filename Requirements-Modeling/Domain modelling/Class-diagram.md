### Class Diagram — PlantUML Source Code


plantuml
@startuml
title Smart Parcel Locker System - Class Diagram

top to bottom direction
hide circle
hide empty members
hide methods
skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam monochrome true
skinparam classBackgroundColor white
skinparam classBorderColor black
skinparam classBorderThickness 1
skinparam defaultFontName Arial
skinparam roundcorner 0
skinparam nodesep 80
skinparam ranksep 80

abstract class User {
  userId : String
  name : String
  email : String [0..1]
  phoneNumber : String [0..1]
  accountReference : String [0..1]
}

class Courier
class Administrator
class Recipient

class DeliveryCompany {
  companyId : String
  name : String
}

class Locker {
  lockerId : String
  address : String
  gpsLocation : String
  openingHours : String
  operationalStatus : String
  /freeCompartmentCount : Integer
  /occupiedCompartmentCount : Integer
}

class Compartment {
  compartmentId : String
  sizeCategory : String
  operationalStatus : String
  occupancyStatus : String
  /isAvailable : Boolean
}

class Parcel {
  parcelId : String
  trackingNumber : String
  sizeCategory : String
  registeredAt : DateTime
  status : String
  /pickupDeadline : DateTime [0..1]
  notes : String [0..1]
}

class PickupCode {
  code : String
  issuedAt : DateTime
  expiresAt : DateTime
  usedAt : DateTime [0..1]
}

class Notification {
  notificationId : String
  channel : String
  destination : String
  instructions : String
  deliveryStatus : String
  sentAt : DateTime [0..1]
}

class ParcelEvent {
  eventId : String
  occurredAt : DateTime
  eventType : String
  resultingStatus : String
  details : String [0..1]
}

class SupportRequest {
  requestId : String
  reportedAt : DateTime
  description : String
  status : String
}

' Generalization: the hollow triangle points to User.
User <|-- Recipient
User <|-- Courier
User <|-- Administrator

' Numbers in quotes are multiplicities at the respective endpoints.
' The final > gives the reading direction of the relationship label.
Courier "0..*" -- "1" DeliveryCompany : uses account from >
Administrator "0..*" -- "1" DeliveryCompany : uses account from >

Locker "1" *-- "1..*" Compartment : contains >
Recipient "1" -- "0..*" Parcel : receives >
Courier "1" -- "0..*" Parcel : registers >
Parcel "0..1" -- "0..1" Compartment : assigned to >

Parcel "1" -- "0..1" PickupCode : has >
Parcel "1" -- "0..*" Notification : has >
Parcel "1" -- "1..*" ParcelEvent : has history of >
User "0..1" -- "0..*" ParcelEvent : is actor in >
Compartment "0..1" -- "0..*" ParcelEvent : involved in >

User "1" -- "0..*" SupportRequest : reports >
SupportRequest "0..*" -- "0..1" Locker : concerns >
SupportRequest "0..*" -- "0..1" Parcel : concerns >

@enduml
