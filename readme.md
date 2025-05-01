
# Salon AI Agent Design

This document outlines the design choices made for the Salon AI Agent, focusing on key components such as help requests, knowledge base updates, supervisor timeouts, scalability, and modularization.

## 1. Modeling Help Requests

Help requests represent customer queries that require a supervisor's attention. They are stored in a Firebase Realtime Database to allow real-time updates and quick access.

### Firebase Database Structure

```json
{
  "HelpRequests": {
    "<help_request_id>": {
      "question": "The customer's question",
      "status": "pending | resolved | unresolved",
      "created_at": "timestamp",
      "resolved_at": "timestamp",
      "answer": "Supervisor's response (if resolved)"
    }
  }
}
```

### Fields Breakdown:
- **question**: The customer's query that needs to be answered.
- **status**: The current state of the request — "pending" (awaiting supervisor response), "resolved" (answered by supervisor), or "unresolved" (timed out).
- **created_at**: The timestamp when the help request was created.
- **resolved_at**: The timestamp when the request was resolved or timed out.
- **answer**: The supervisor's answer, only populated if the request is resolved.

### Relationships:
- **HelpRequests** are independent entities.
- When the request is resolved by the supervisor, the `answer` field is populated, and `status` is updated to "resolved".

### Handling Help Request Lifecycle:
1. **Pending**: A help request is created when the AI cannot respond to the customer's query. The request remains in a "pending" state.
2. **Timeout**: After a predefined timeout period (5 minutes), if no response is provided by the supervisor, it is automatically marked as "unresolved".
3. **Resolved**: When the supervisor responds, the `status` is updated to "resolved", and the answer is provided to the customer.

---

## 2. Knowledge Base Updates

The knowledge base is a critical component to improve the agent's responses. It is updated dynamically based on supervisor-provided answers and customer queries.

### Structure:
The knowledge base is stored as a local `JSON` file. Each new question-answer pair is added to the file for persistence.

### File Structure:

```json
{
  "question1": "answer1",
  "question2": "answer2"
}
```

### Update Process:
1. **New Questions**: If the agent is unable to provide an answer, the supervisor provides the answer, and the knowledge base is updated with this new question-answer pair.
2. **Learning from Supervisor**: When a supervisor responds to a pending help request, the response is saved to the knowledge base for future use.

---

## 3. Handling Supervisor Timeouts

Time-sensitive requests, such as pending help requests, must be managed carefully to ensure a smooth user experience.

### Timeout Handling:
- A timeout period (set to 5 minutes in this case) is tracked using a timestamp (`created_at`).
- Once the timeout period has passed, if the request is still in a "pending" state, it is automatically marked as "unresolved".
- This ensures that users are informed of the status of their request if no action is taken by the supervisor in a timely manner.

---

## 4. Scaling Considerations (From 10/day to 1,000/day)

To scale this system efficiently, we need to consider factors such as database performance, API rate limits, and the potential load on both the agent and supervisor systems.

### Key Scaling Strategies:
1. **Firebase**:
   - Firebase is used for real-time updates, which works well for small to medium-scale applications. For a higher volume of requests, Firebase Realtime Database may become a bottleneck. In that case, a more scalable solution like Firestore would be ideal.
2. **Asynchronous Processing**:
   - We use asyncio to handle help requests and responses asynchronously, which ensures that multiple requests can be processed concurrently without blocking other operations.
3. **Rate Limiting and Caching**:
   - Implementing caching mechanisms (e.g., Redis) and rate limiting on API calls can help ensure that the system remains performant under heavy load.

---

## 5. Modularizing the Agent, Help Requests, and Text-Back Handling

To ensure that the system is maintainable, extensible, and clean, the following modular design approach is adopted:

### 1. **Agent Module**:
   - The **SimpleSalonAgent** class encapsulates all the logic related to handling customer queries, including generating responses and triggering help requests.

### 2. **Help Request Module**:
   - The help request handling logic is separated into functions that interact with Firebase, making it easy to modify without affecting other components.

### 3. **Text-Back Handling**:
   - The supervisor’s responses are handled in the `supervisor_responds` function, which updates the help request in Firebase and notifies the agent when a supervisor has resolved a query.

### 4. **Separation of Concerns**:
   - Each part of the system is modularized, ensuring that changes in one area do not affect others.

---

## 6. Setup and Execution

1. **Environment Variables**:
   - Ensure to load the environment variables using `dotenv` before starting the application.
   
2. **Firebase Credentials**:
   - The `firebase_credentials.json` file should be placed in the project directory to authenticate with Firebase.

3. **Running the Application**:
   - The agent is started by calling the `cli.run_app()` function. Make sure to pass in the correct `entrypoint_fnc` as shown in the script.

---

## 7. Supervisor Interaction

Supervisors can resolve help requests through the `supervisor_responds` function, which updates the request status and provides an answer.

### Example:
```python
def supervisor_responds(help_request_id: str, supervisor_answer: str):
    help_requests_ref.child(help_request_id).update({
        'status': 'resolved',
        'answer': supervisor_answer,
        'resolved_at': datetime.utcnow().isoformat(),
    })
    logger.info(f"Supervisor resolved request {help_request_id} with answer: {supervisor_answer}")
```

This function updates the Firebase database and informs the agent when a supervisor has resolved a query.

---

## 8. Conclusion

The design ensures that the system is scalable, modular, and easy to maintain. By separating concerns into manageable modules (Agent, Help Requests, Knowledge Base, Supervisor Interaction), the system can evolve and adapt to growing customer needs.
