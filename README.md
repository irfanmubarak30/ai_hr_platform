# 🧠 AI-Driven Recruitment Automation & Decision System

An end-to-end AI-powered system designed to automate candidate evaluation, decision-making, and recruitment workflows using **LLM-based scoring, event-driven pipelines, and multi-source data integration**.

---

## 🧠 System Overview

This system is built as a **real-time decision automation pipeline** that ingests candidate data from multiple sources, processes it through AI models, and executes actions based on intelligent evaluation.

Unlike traditional HR tools, this platform focuses on:

* **Automated decision-making**
* **Real-time event handling**
* **AI-driven scoring and ranking**
* **End-to-end workflow orchestration**

---

## ⚙️ System Architecture

### 🔄 End-to-End Pipeline

Email / LinkedIn Input
→ Data Extraction
→ Structured Parsing
→ AI Evaluation
→ Decision Engine
→ Storage Layer
→ Action Triggers (Scheduling / Calls / Notifications)

---

## 🧩 Core Components

### 📥 Data Ingestion Layer

* Gmail listener (polling-based event system)
* LinkedIn scraping via Apify APIs
* Handles unstructured inputs (emails, PDFs, profiles)

---

### 📄 Parsing & Preprocessing Engine

* PDF parsing using `pdfplumber`
* Text normalization and structuring
* Feature extraction (skills, experience, education)

---

### 🤖 AI Evaluation Module

* LLM-based candidate scoring (Gemini / Groq)
* Evaluates across:

  * Technical skills
  * Experience relevance
  * Achievements
  * Educational background
* Outputs structured scores (0–10) with reasoning

---

### 🧠 Decision Engine

* Rule-based + AI-assisted decision logic
* Threshold-based filtering:

  * Score ≥ 6 → shortlisted
  * Score < 6 → rejected
* Can be extended to adaptive or learned thresholds

---

### 🔁 Workflow Automation Engine

* Event-triggered execution pipeline
* Automates:

  * Interview scheduling (Google Calendar)
  * Candidate notifications
  * AI voice calls (ElevenLabs)
* Handles asynchronous workflows

---

### 💾 Storage & Integration Layer

* Google Sheets for structured tracking
* Google Drive for CV storage
* Maintains candidate lifecycle data

---

## 📊 System Flow

### 📧 Email-Based Pipeline

1. Gmail listener polls inbox
2. CV extracted from email
3. File uploaded to Google Drive
4. Text extracted using parser
5. AI evaluates candidate
6. Score stored in Google Sheets
7. Decision applied
8. If shortlisted → interview + AI call triggered

---

### 🔍 LinkedIn Sourcing Pipeline

1. Input: role + location + experience
2. Apify API fetches candidate profiles
3. Profile data parsed and structured
4. AI evaluates candidates
5. Ranked candidates displayed in dashboard

---

## ⚡ Key Features

* End-to-end recruitment automation
* AI-driven candidate evaluation (LLMs)
* Real-time event-based processing
* Multi-source data ingestion
* Automated scheduling and communication
* Voice-based candidate interaction
* Scalable modular architecture

---

## 🎥 Demo

![Demo](assets/demo.gif)

---

## 🛠 Tech Stack

* **Backend:** Python, Flask
* **AI Models:** Google Gemini, Groq LLMs
* **Parsing:** pdfplumber
* **APIs:** Gmail API, Google Drive, Google Sheets, Apify, ElevenLabs
* **Automation:** Event-driven workflows
* **Data:** JSON + Google Sheets

---

## 📡 System Characteristics

* Event-driven architecture
* Asynchronous workflow execution
* Modular pipeline design
* Scalable integration with external APIs
* Real-time decision processing

---

## 🎯 Applications

* AI-driven decision automation systems
* Workflow orchestration platforms
* Enterprise process automation
* Intelligent candidate evaluation pipelines

---

## 🧠 Key Concepts Demonstrated

* AI-based decision systems
* Pipeline architecture & orchestration
* Event-driven automation
* Multi-source data integration
* Real-time workflow execution
* Human-in-the-loop extensibility

---

## 🚀 Possible Extensions

* Replace polling with event streaming (Kafka / Webhooks)
* Add learning-based ranking models
* Deploy on distributed infrastructure
* Integrate real-time dashboards with analytics
* Optimize latency for large-scale pipelines

---

⭐ *Designed as an intelligent decision-making system rather than a traditional HR application*
