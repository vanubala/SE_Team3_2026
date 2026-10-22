recipient use case diagram (plant uml code) (original before re-formatting):

@startuml
left to right direction

title Recipient Use Case Model

skinparam shadowing false
skinparam packageStyle rectangle
skinparam usecase {
    BackgroundColor #E6E6E6
    BorderColor black
}
skinparam actor {
    BorderColor black
}

actor Recipient as R
actor Database as DB
actor "Locker Hardware" as LH

rectangle "Recipient Use Case System" {

    usecase "Tracking" as Tracking
    usecase "Authentication" as Auth
    usecase "Receive Notification\nand Code" as Notify
    usecase "Pickup" as Pickup
    usecase "Report" as Report

    Tracking ..> Auth : <<include>>
    Notify ..> Auth : <<include>>
    Pickup ..> Notify : <<include>>
    Report ..> Pickup : <<extend>>
}

R -- Tracking
R -- Notify
R -- Pickup
R -- Report

Tracking -- DB
Auth -- DB
Notify -- DB
Notify -- LH
Pickup -- LH

@enduml
