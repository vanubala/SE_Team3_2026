# 📦 Smart Parcel Locker Management System

> A platform for managing parcel delivery and collection through shared smart lockers.

Couriers drop parcels into secure locker compartments. Recipients get a pickup code and collect the parcel when it suits them. Administrators keep the locker network running.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Actors](#-actors)
- [Core Features](#-core-features)
- [Repository Structure](#-repository-structure)
- [Project Progress](#-project-progress)
- [Team Members](#-team-members)

---

## 🔍 Overview

Missed deliveries cost couriers time and frustrate recipients. The **Smart Parcel Locker System** fixes this with a network of shared lockers where:

- **Couriers** register incoming parcels and deposit them in a suitable compartment
- **Recipients** get a pickup notification and code, then collect their parcel
- **Administrators** monitor locker availability and operational status, and send hardware faults to maintenance

This repository holds the **requirements engineering and modelling** work for the system.

---

## 👥 Actors

| Actor | Type | Role |
|-------|------|------|
| **Courier** | Primary | Registers parcels and deposits them into assigned compartments |
| **Recipient** | Primary | Tracks parcels, receives pickup codes and collects parcels |
| **Administrator** | Primary | Monitors locker availability and status and manages faults |
| **Locker Hardware** | Secondary (system) | Physical lockers: open/close doors and report their status |
| **Notification Gateway** | Secondary (service) | Sends pickup notifications and codes to recipients |
| **Maintenance Team** | Secondary | Fixes reported hardware faults |

---

## ✨ Core Features

### 🚚 Courier
- Authenticate as a courier
- Register an incoming parcel
- Get a suitable compartment assigned automatically
- Deposit the parcel into the locker
- Report exceptions during deposit

### 📬 Recipient
- Authenticate as a recipient
- Track parcel status
- Receive a pickup notification and access code
- Pick up the parcel from the locker
- Report issues (door jammed, code unreadable, empty locker)

### 🛠️ Administrator
- Authenticate as an administrator
- See locker availability at a glance
- Receive the operational status of lockers
- Change a locker's status after an operational fault
- Report hardware faults to the maintenance team


---


## Team members

| Name | GitHub username | Responsible for |
| :--- | :--- | :--- |
| Vanathy BALACHANDRAN | vanubala | Frontend |
| WAICMAN GONCALVES Andres | andresgit763 | Backend |
| Christos NASOPOULOS | chris4nas | Authentication |
| Vasileios PANDIS | vasilispandis | Database |
| Raed CHAUDRY | RJawad1223 | Interactive features |
| Serhii ILLARIONOV | woodstockdelirium | Interactive features |

## Planning

**GitHub Project URL:** https://github.com/users/vanubala/projects/1

<p align="center"><i>Made by the Smart Parcel Locker team</i></p>
