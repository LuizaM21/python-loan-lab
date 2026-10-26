# Exam 3 — Mock interview

Time: 45 minutes. Your mentor plays the interviewer.

You may read these questions before. Practise the answers out loud. In the exam, you have no
notes. The mentor may ask follow-up questions.

## Questions

1. Tell me about yourself, and why a developer role now. (60 seconds)
2. Your background is Scala. What is different when you write Python, and how do you stay safe without a compiler?
3. Design a REST API for loan repayments. Which endpoints, status codes, and how do you stop a double charge?
4. Walk me through how a request flows through your Flask app, from the URL to the database commit.
5. What is the N+1 problem? How do you detect and fix it in SQLAlchemy and in Django?
6. Two repayments for the same loan arrive at the same time. What can go wrong and how do you prevent it?
7. Flask or Django for a new project here? Why?
8. **Live coding (10 minutes):** implement a rate limiter: at most N calls per key per sliding window, with an injectable clock. Talk while you code. Then: how would you test it?
9. An endpoint's p95 went from 80 ms to 900 ms after a release. What do you do?
10. Explain the GIL. When do you use threads, asyncio or processes?
11. How do you ship this service: Docker image, Kubernetes, configuration, health checks?
12. How do you use AI coding agents, and how do you make sure the output is correct?

Possible extra questions:

- When would you use MongoDB instead of PostgreSQL?
- What is the transactional outbox?
- Mutable default arguments: what is the bug?
- How do you review a colleague's pull request?
- How would you handle a database migration on a large live table?
- What is your experience with C++? (Be honest.)
- Tell me about a disagreement in a team and how you solved it. (STAR)
- Where are your gaps, and how are you closing them?

## Scoring

The mentor scores each answer from 1 to 4. See `instructor/answer-keys/exam-3-mock-interview-key.md`.

Pass: average 3 or more, and no score of 1 on questions 3, 4, 5, 6, 8, or 9.
