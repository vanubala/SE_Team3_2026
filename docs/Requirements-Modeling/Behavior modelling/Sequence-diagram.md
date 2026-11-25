### Admin Sequence Diagram Code

```text
@startuml
title UC3: Administrator monitoring locker availability and operational status

actor Administrator
boundary AdminDashboardUI
control MonitoringController
entity "LockerMonitoringService" as Service <<service>>
database LockerRepository <<repo>>

Administrator -> AdminDashboardUI : requestLockerOverview()
activate AdminDashboardUI

AdminDashboardUI -> MonitoringController : fetchLockerStatusAndOccupancy()
activate MonitoringController

MonitoringController -> Service : aggregateSystemMetrics()
activate Service

Service -> LockerRepository : findAllLockersAndCompartmentStatus()
activate LockerRepository

LockerRepository --> Service : lockerStatuses (available, occupied, maintenance)
deactivate LockerRepository

Service --> MonitoringController : returnMonitoringData(occupancyRates, operationalStatuses)
deactivate Service

MonitoringController --> AdminDashboardUI : renderMonitoringDashboard(metrics)
deactivate MonitoringController

AdminDashboardUI --> Administrator : displayLockerStatusOverview()
deactivate AdminDashboardUI

@enduml
