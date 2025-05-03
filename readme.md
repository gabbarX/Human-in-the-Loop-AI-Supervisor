
# Salon AI Agent – Setup and Execution Guide

This guide provides detailed instructions on setting up, running, and understanding the design of the Salon AI Agent System. The project is divided into two main components:
- `app.py` – The user-facing frontend interface.
- `FakeSalon.py` – The backend AI agent logic server.

---

## 📚 Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Script Overview](#2-script-overview)
    - A. [Frontend Interface – app.py](#a-frontend-interface--apppy)
    - B. [AI Agent Server – FakeSalon.py](#b-ai-agent-server--fakesalonpy)
3. [Running the Full System](#3-running-the-full-system)
4. [Help Request Lifecycle](#4-help-request-lifecycle)
5. [Knowledge Base Management](#5-knowledge-base-management)
6. [Handling Supervisor Timeouts](#6-handling-supervisor-timeouts)
7. [Scaling Considerations](#7-scaling-considerations)
8. [Modular Architecture](#8-modular-architecture)
9. [Supervisor Interaction](#9-supervisor-interaction)
10. [Conclusion](#10-conclusion)

---

## 1. Environment Setup

- Requires **Python 3.8+**
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

- Create a `.env` file with required environment variables (e.g., Firebase config).
- Place `firebase_credentials.json` in the root directory for Firebase access.

---

## 2. Script Overview

### A. Frontend Interface – `app.py`

- Handles user interactions and supervisor responses.
- Forwards unresolved queries to supervisors.
- Lets supervisors resolve help requests.

Run with:
```bash
python app.py
```

### B. AI Agent Server – `FakeSalon.py`

- Powers the AI logic.
- Uses a local knowledge base to answer questions.
- Creates help requests when unsure of an answer.

Run with:
```bash
python FakeSalon.py
```

Ensure this script includes:
```python
cli.run_app(entrypoint_fnc=...)
```
where `entrypoint_fnc` initializes the `SimpleSalonAgent`.

---

## 3. Running the Full System

Step 1: Start the AI Agent backend:
```bash
python FakeSalon.py console
```

Step 2: Start the frontend interface:
```bash
python app.py
```

Both components sync via **Firebase Realtime Database** for real-time updates and communication.

---

## 4. Help Request Lifecycle

Help requests represent customer queries the AI can't resolve.

### Firebase Structure:
```json
{
  "HelpRequests": {
    "<id>": {
      "question": "User's question",
      "status": "pending | resolved | unresolved",
      "created_at": "timestamp",
      "resolved_at": "timestamp",
      "answer": "Supervisor response"
    }
  }
}
```

### States:
- `pending`: Awaiting supervisor response.
- `resolved`: Answered by a supervisor.
- `unresolved`: Timed out after 5 minutes with no response.

---

## 5. Knowledge Base Management

Stored as a local JSON file:

```json
{
  "question1": "answer1",
  "question2": "answer2"
}
```

- Updated when a supervisor answers an unresolved question.
- Enhances the agent’s capabilities over time.

---

## 6. Handling Supervisor Timeouts

- Help requests timeout after **5 minutes**.
- If no response is received, status changes from `pending` to `unresolved`.
- Ensures users are not left waiting indefinitely.

---

## 7. Scaling Considerations

To handle up to 1,000 requests/day:

### Strategies:
- **Switch to Firestore** if Firebase becomes a bottleneck.
- Use **asyncio** for concurrent request handling.
- Integrate **caching** (e.g., Redis) and **rate limiting**.

---

## 8. Modular Architecture

Ensures maintainability and scalability:

### Components:
- **Agent Module**: `SimpleSalonAgent` handles queries and fallback logic.
- **Help Request Module**: Manages Firebase help request logic.
- **Supervisor Handling**: Uses `supervisor_responds()` for updates.
- **Separation of Concerns**: Independent modules for better clarity and updates.

---

## 9. Supervisor Interaction

Supervisors resolve help requests using:

```python
def supervisor_responds(help_request_id: str, supervisor_answer: str):
    help_requests_ref.child(help_request_id).update({
        'status': 'resolved',
        'answer': supervisor_answer,
        'resolved_at': datetime.utcnow().isoformat(),
    })
    logger.info(f"Supervisor resolved request {help_request_id} with answer: {supervisor_answer}")
```

---

## 10. Conclusion

This system is designed for clarity, scalability, and modularity. Real-time help request handling via Firebase and knowledge base learning from supervisors ensures continual improvement.

For issues or contributions, feel free to fork the repo or open a PR.

---

End of Guide
