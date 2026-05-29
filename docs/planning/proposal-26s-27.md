# Project Proposal: SUSTech Student Productivity Agent

**Team ID:** 26s-27  
**Project Name:** SUSTech Student Productivity Agent  
**Target Audience:** Students of Southern University of Science and Technology (SUSTech)

---

## 5.2 Functional Requirements (5 Distinct Features)

- **Feature 1: Unified Identity & Authentication Gateway**  
  A centralized security module providing secure user onboarding via SUSTech institutional emails. It includes a robust password recovery system using an SMTP-based verification code service and utilizes JWT (JSON Web Tokens) for persistent, secure session management.

- **Feature 2: Multi-Source Academic Data Integrator (Perception Layer)**  
  An automated "harvester" that synchronizes academic data from heterogeneous sources including Blackboard (assignments/announcements), TIS (grades/student profiles), and Institutional Email (IMAP/SMTP). It uses CAS (Central Authentication Service) ticket-passing (for BB and TIS) or specific verification code (for Email) to maintain security without storing raw passwords.

- **Feature 3: Intelligent Agentic Scheduler & Planner (Reasoning Layer)**  
  A clean, Apple Calendar-style interface that serves as the centralized "Source of Truth" for the user’s academic life. It automatically populates and renders course timetables, assignment deadlines, and institutional announcements harvested by the Multi-Source Academic Data Integrator (Feature 2). It allows users to manually manage personal events and TODOs, providing a comprehensive visual overview of their daily and weekly commitments at a glance.

- **Feature 4: Multi-Source Intelligent Agent (Reasoning & Executive Layer)**  
  An autonomous LLM-powered co-pilot that acts as the system’s "Brain" by reading data from the Scheduler & Planner and interacting with the Local Workspace. It processes natural language queries to perform the following:
  - **Reasoning & Planning:** Reads information from the scheduler to perform "conflict detection" and generates optimized study plans or daily agendas (e.g., "I have three midterms next week, help me prioritize my tasks").
  - **SUSTech Online Bridge:** Acts as a real-time bridge to SUSTech Online (https://sustech.online/) to retrieve high-accuracy administrative info (e.g., "GPA calculation" or "Dorm handbook") and re-renders it within the Agent UI.
  - **Workspace Co-pilot:** Directly invokes the Local File Management system with explicit permission to perform batch operations, such as renaming lab assignments (e.g., Lab1_v2.zip to Name_ID_Lab1.zip) or converting formats (e.g., Markdown to PDF).

- **Feature 5: Local Workspace & File Management Co-pilot**  
  A system-level toolset allowing the user to perform file operations conveniently on the user’s local machine (with explicit permission). Capabilities include batch renaming of lab assignments (e.g., Lab1_Final_v2.zip to Name_ID_Lab1.zip), format conversion (Markdown to PDF).

## 5.3 Non-Functional Requirements

- **Security & Privacy:** Mandatory encryption for stored session cookies and email app passwords. The system must follow the "Human-in-the-Loop" principle, requiring user confirmation before the Agent executes any destructive or important actions (e.g., deleting files or sending emails).
- **Usability:** A minimalist Vue 3-based desktop GUI (Tauri shell) with a dedicated "Thought Trace" area, allowing users to view structured agent reasoning steps in real time (planning, tool selection, and observation).
- **Performance:** Background synchronization of academic data should be non-blocking. The Agent should respond to natural language queries in a short time. **TODO:**
- **Reliability:** Robust error handling for CAS session expiration, providing clear prompts for the user to re-authenticate when a session becomes invalid.
- **Code Style:**  
  Follow naming standards using `kebab-case` for Vue component filenames, `camelCase` for variables/functions, `PascalCase` for TypeScript interfaces/classes and `UPPER_SNAKE_CASE` for constants; enforce formatting and linting with Prettier (line length 120), ESLint for Vue/TS and Clippy for Rust, while banning unused variables/imports and hardcoded credentials in favor of environment variables; structure code modularly by responsibility, cap function length at 50 lines and file length at 500 lines, and add docstrings or comments for public functions with JSDoc and Rustdoc; adhere to Conventional Commits, require pull request code reviews before merging, and keep a clean linear Git history without merge commits for feature branches.

## 5.4 Technical Requirements (To be determined)

- **Frontend Stack:**  
  Vue 3 (Composition API), Vite, Tailwind CSS (for minimalist UI), Axios for API communication, Pinia for state management, ECharts for Thought Trace visualization (Agent), Tauri 2 for desktop packaging, SQLite for local persistence, and Tauri Commands/Events for secure frontend-native communication (IPC).

- **Backend Stack:**  
  Python 3.10+, Tauri Plugin Python (embeds Python logic into Tauri desktop shell), LangGraph for Agentic Loop orchestration, Pydantic v2 for data validation, and Celery for lightweight async task processing (background academic data sync).

- **LLM Integration:**  
  OpenAI GPT-4o or DeepSeek-V3/R1 via API for reasoning and tool calling.

- **Database:**  
  SQLite for local data persistence (User profiles, academic metadata, and chat history). Tauri FS API for secure local file read/write.

- **Protocols:**  
  SMTP/IMAP (Email), CAS (Authentication), HTTPS (Web requests), and AES-256 (Data encryption).

## 5.5 Data Requirements

- **User Data:**  
  SUSTech Email, hashed passwords, and encrypted CAS session cookies.

- **Academic Data:**  
  Scraped HTML content from Blackboard, JSON responses from TIS, and raw MIME emails from the SUSTech exchange server.

- **Acquisition Method:**  
  - **CAS Simulation:** Capturing tickets via redirect URLs to obtain JSESSIONID.  
  - **Email Sync:** Connecting via `imap.exmail.qq.com` using user-generated App Passwords.  
  - **File System:** Local directory indexing via Python `os` and `shutil` modules.
