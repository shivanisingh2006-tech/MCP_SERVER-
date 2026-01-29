
# 🗡️ Switchblade – MCP Server (gRPC) with Lateral Movement Lab

## 📌 Overview

Switchblade is an implementation of the **Model Context Protocol (MCP)** using **gRPC** for communication between an MCP client and MCP server.

This project includes a **hands-on security lab** demonstrating **lateral movement** through a **DMZ pivot** into an **internal private service**, enforcing execution-context–based access instead of direct network exposure.

---

## 🎯 Goal

Validate execution-context–based access rather than direct network exposure.

Internal resources are reachable **only by pivoting through the DMZ**.

---

## 🧩 Key Components

### 🖥️ MCP Client & Server
- Run outside Docker (host system)
- Communicate using gRPC
- Send execution requests (scan, execute, retrieve)

### 🚪 DMZ Pivot
- Exposed to the host using mapped ports
- Accepts remote command execution
- Acts as the pivot point for lateral movement

### 🏦 Internal Bank
- Connected only to a private Docker network
- Hosts sensitive data
- ❌ Not directly reachable from the host

---

## 🏗️ Architecture

[MCP Client]
|
| gRPC
v
[MCP Server]
|
| SSH / Command Execution
v
[DMZ Pivot Container]
|
| Private Docker Network
v
[Internal Bank Container]
---

## 🌐 Docker Network Design

Two Docker networks are used:

### 🌍 Public Network
- Exposes DMZ services to the host
- Used for initial access

### 🔒 Private Network
- Shared only between DMZ and Internal Bank
- Prevents direct external access to internal services

---

## 🔐 Internal Bank Service

- Service: `python -m http.server`
- Port: `8000`
- Scope: Private Docker network only
- Data directory: `/bank_data`
- Sensitive file: `/bank_data/accounts.txt`

❗ This file is never exposed externally.

---

## ⚙️ MCP Communication Model

- MCP client ↔ MCP server communication uses gRPC
- MCP server controls execution context
- Commands run only where explicitly executed
- MCP does not bypass Docker or network isolation

---

## 🧪 Lateral Movement Testing

### 🔍 Step 1: External Enumeration
- MCP client scanned `127.0.0.1`
- Identified DMZ-exposed ports (e.g. `2222`, `8080`)
- Internal services were not directly accessible

### 🚪 Step 2: Pivot to DMZ
- MCP server executed commands inside the DMZ container
- Execution context verified
- Commands were not running on the host

### 🔓 Step 3: Access Internal Bank from DMZ

From the DMZ execution context, MCP executed:
### ✅ Results Summary

- ✔ External → DMZ access

- ✔ DMZ → Internal Bank access

- ❌ External → Internal Bank direct access blocked

```bash
curl http://internal_bank:8000/accounts.txt
