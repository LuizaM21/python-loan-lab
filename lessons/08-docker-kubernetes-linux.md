# 08 — Docker, Kubernetes and Linux

Time: 75 minutes.

Goal: run the app the way production does (container, PostgreSQL, Kubernetes) and debug it there.

## Learn: the Dockerfile in this repo

```dockerfile
FROM python:3.12-slim AS builder                 # pinned, slim base; build wheels here
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
FROM python:3.12-slim                            # multi-stage: build tools stay behind
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 # no .pyc files, logs not buffered
RUN useradd --system app                          # never run as root
COPY --from=builder /wheels /wheels              # dependencies first: cached until they change
COPY loanlab ./loanlab                           # code last: changes every commit
USER app
HEALTHCHECK CMD ... /api/health
CMD ["gunicorn", ...]                            # exec form: gunicorn is PID 1 and gets SIGTERM
```

| Rule | Why |
| --- | --- |
| Pin the base image | builds are repeatable |
| Dependencies before code | a code change does not reinstall everything |
| Multi-stage | smaller image, fewer CVEs |
| Non-root user | a break-out from the app is not root |
| Exec-form `CMD` | graceful shutdown: signals reach the app |
| Config from environment | the same image runs in every environment (12-factor) |
| Never bake secrets into the image | anyone with the image can read them |

## Learn: Kubernetes basics

| Object | Does |
| --- | --- |
| Deployment | keeps N identical pods running; rolling updates |
| Pod | one or more containers that share network and volumes |
| Service | a stable name and port in front of the pods |
| ConfigMap / Secret | configuration / sensitive configuration, as env vars or files |
| readinessProbe | "send me traffic?" Failing = removed from the Service, not restarted |
| livenessProbe | "am I alive?" Failing = container restarted |
| requests / limits | scheduling guarantee / hard cap. Over the memory limit = OOMKilled; over CPU = throttled |

## Learn: Linux you will use while debugging

`ps aux | grep gunicorn`, `top`, `ss -tlnp` (who listens on which port), `curl -v`, `df -h`,
`du -sh *`, `tail -f`, `grep -R "text" .`, `env`, `kill -TERM <pid>` vs `kill -9`,
`journalctl -u <service>`; and in Kubernetes: `kubectl get pods`, `describe`, `logs -f`,
`exec -it <pod> -- sh`, `top pod`, `rollout status`, `rollout undo`.

## In this repo

| File | Shows |
| --- | --- |
| `Dockerfile` | multi-stage, non-root, healthcheck, gunicorn |
| `.dockerignore` | keeps `.git`, `.venv`, caches out of the build context |
| `docker-compose.yml` | API + PostgreSQL + MongoDB, with health conditions |
| `k8s/` | Deployment, Service, ConfigMap, probes, resources, security context |

## Do

### 1. Build and run

```bash
docker build -t loanlab:dev .
docker run --rm -p 5080:5080 loanlab:dev
curl localhost:5080/api/health
docker image ls loanlab
docker history loanlab:dev
```

Change one line in `loanlab/money.py` (a comment) and build again. Which layers were rebuilt?

### 2. Compose with PostgreSQL and MongoDB

```bash
MONGO_URL=mongodb://mongo:27017 docker compose up --build    # without MONGO_URL: in-memory event log
```

The API now uses PostgreSQL (`DATABASE_URL`) and MongoDB (`MONGO_URL`, needs your lesson 06
work). Open and repay a loan, then look in both databases:

```bash
docker compose exec postgres psql -U loanlab -c "select reference, outstanding, status from loans;"
docker compose exec mongo mongosh loanlab --eval "db.events.find().limit(3)"
```

### 3. Concurrency, for real

Repeat the lesson 07 test (20 users repaying the same loan at once) against the Compose stack.
With `with_for_update` the total repaid never exceeds the loan amount. Remove `with_for_update`
in `services.py`, rebuild, repeat: can you overpay? Put it back. Write the result in `notes/day-4.md`.

### 4. Kubernetes with kind

```bash
kind create cluster
docker build -t loanlab:dev . && kind load docker-image loanlab:dev
kubectl apply -f k8s/
kubectl get pods -w
kubectl port-forward svc/loanlab 5080:80
```

Then: scale to 3 replicas (`kubectl scale deployment/loanlab --replicas=3`); break the readiness
probe path in `k8s/deployment.yaml` and apply: what happens to the rollout? `kubectl rollout undo`.
Set the memory limit to `64Mi`, apply, and watch for `OOMKilled` in `kubectl describe pod`.

Note: in Kubernetes each pod has its own SQLite file here, so data differs per pod. In
production `DATABASE_URL` points at PostgreSQL. Explain in your notes why that matters.

### 5. Graceful shutdown

`docker run` the image, start a slow request (`/api/stats/portfolio` with `DEMO_LOANS`), and
`docker stop` the container. Does the request finish? Read about gunicorn's `--graceful-timeout`
and Kubernetes' `terminationGracePeriodSeconds`.

### Practice bug hunt 2

`instructor/bug.sh random 2`. Two bugs this time. Find, prove with a test, fix. Think about every
layer: service rules, API contract, security, and speed with a lot of data.

## Check yourself

1. Why copy `requirements.txt` and install before copying the code?
2. Why exec-form `CMD`? What is PID 1's job?
3. Readiness vs liveness: what happens when each fails?
4. Requests vs limits. What happens over the memory limit? Over the CPU limit?
5. How do config and secrets reach the container? Why not bake them into the image?
6. Why can't you run this app with SQLite on 3 pods?
7. A pod restarts every few minutes. Which commands do you run, in which order?

## Say it in the interview

- "My images are multi-stage, slim, pinned, non-root, with a healthcheck and an exec-form CMD,
  and the same image runs in every environment with config from env vars and secrets."
- "I set readiness and liveness probes separately and size requests and limits from load-test
  numbers, not guesses."
