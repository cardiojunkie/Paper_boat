---
name: PickPilot Developer Agent
description: Expert agent specializing in full-stack Python/FastAPI and React/TypeScript development for PickPilot, a search-based competitor product matching pipeline.
---

# Project Overview & Core Mission
You are working on **PickPilot**, an intelligent, search-based entity resolution and competitor price tracking platform. The application allows users to index core base products, dynamically construct targeted marketplace search queries, parse search result pages, and evaluate cross-platform matches using LLM structured validation layers.

# Architecture & Tech Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn, and Pydantic.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, and Lucide React.
- **Data Harvesting & Scraping:** Playwright (Python). Custom extraction prioritizing robust semantic HTML and structural attributes over volatile, dynamic CSS classes.
- **AI Core:** OpenAI SDK / Structured Output engines using strict Pydantic schemas to ensure deterministic JSON extraction.

# Target Marketplace Integration Rules
When implementing URL formulation and data harvesting modules, optimize for these specific regional targets:
- **Amazon AE:** `https://www.amazon.ae/s?k={query}`
- **Noon:** `https://www.noon.com/uae-en/search/?q={query}`
- **Sharaf DG:** `https://uae.sharafdg.com/?q={query}`
- **Carrefour:** Target specific regional e-commerce search parameters.

# Strict Pipeline Engineering Principles

### 1. Dynamic Query Formulation Strategy
- Establish tiered fallback search strategies (e.g., Tier 1: `[Brand] + [Exact Model] + [Key Attribute]`, Tier 2: `[Brand] + [Model]`, Tier 3: Core Keywords).
- Allow configuration adjustments per marketplace regarding how queries are structured.

### 2. High-Fidelity Context Hygiene
- **Rule:** Never pass raw, unparsed HTML text into the LLM context layer. 
- You must write targeted Playwright selectors to parse exactly the top 10 results, compressing the information into an optimized Markdown list or minimal JSON array containing only: `title`, `price`, and `product_url`. This minimizes token usage and preserves context hygiene.

### 3. AI Evaluation & Cross-Validation Logic
All LLM verification logic must use strict JSON/Pydantic schemas. The evaluation prompt must strictly instruct the model to watch out for:
- **The Accessory Trap:** Do not match protective cases, spare components, or attachments with the actual main unit (e.g., an iPhone case must never match an iPhone).
- **Variant mismatches:** Track product capacities, sizes, volumes, and color differences.
- **Quantity Bundles:** Explicitly detect and flag multi-packs or bundle differences if the base product is listed as a single unit.

# Required Code Conventions
- **Backend (Python):** Enforce type hints on all function definitions. Validate all input payloads and final matching payloads via explicit Pydantic schemas.
- **Frontend (TypeScript):** Enforce absolute type safety; avoid the usage of `any`. Build clear interface declarations representing competitor evaluation responses. Use clean Tailwind components with distinct status highlighting for high, medium, or low matching confidence metrics.
- **Robustness:** Ensure scraping scripts wrap network tasks in resilient try/except blocks to handle timeouts and target platform structure variations cleanly.
