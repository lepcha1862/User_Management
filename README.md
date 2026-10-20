# User_Management

**Expected:** `Count : ` shows at least 4-5 occurrences of the hostname. If not, edit the file.

---

### Report outline

**What it does:** Gives you the **exact section structure + screenshot assignments + word count** so the PDF writes itself. Just fill in the brackets with the screenshots you've been saving.

**Structure:**

| Section | Pages | Content |
|---|---|---|
| **Cover** | 0.5 | Title, SID `02230125`, module, date |
| **1. Architecture** | 1 | Redraw Figure 1 with your specific names (`usermgmt-02230125`, `api-hpa`, `postgres-vpa`, 2/6 replicas). Annotate the traffic path: `Browser → 127.0.0.1:80 → minikube tunnel → ingress-nginx → Ingress rule (host) → Service api → Deployment pods → postgres` |
| **2. M1 evidence** | 0.5 | Screenshots: `kubectl get nodes`, `kubectl get pods -A` (with 3 VPA pods), `kubectl get storageclass`, `kubectl top nodes` |
| **3. M2 evidence** | 1 | `kubectl get statefulset,pod,pvc,pv` + `describe pvc` + **the persistence test sequence 9-3 → 9-8** |
| **4. M3 evidence** | 1 | Dockerfile, `image ls`, `kubectl get deploy,rs,pods,svc`, `describe pod` (probes), **CRUD sequence 12-1 → 12c-4** |
| **5. M4 evidence** | 0.5 | Ingress YAML, `describe ingress` (rules + endpoints), hosts entry, **15-1 vs 15-2** |
| **6. M5 evidence** | 2 | HPA YAML, `top pods`, **the timeline table**, `describe hpa` (4 SuccessfulRescale events), VPA YAML + recommendations, **the two written answers from my previous message** (HPA/VPA conflict, why "Off") |
| **7. Troubleshooting** | 1 | See below |
| **8. Conclusion** | 0.5 | 2-3 sentences on what worked / what was learned |

**Section 7 — Troubleshooting:**

> **Problem:** `PUT /users/2` returned `200 OK` but the `name` field was unchanged after the request.
>
> **Diagnosis:** I ran `kubectl logs -n usermgmt-02230125 deploy/api --tail=20` and saw only gunicorn boot lines — no per-request access logs — so I added a temporary Flask request logger and observed that the PUT request body arrived empty. I then tested with PowerShell inline JSON (`curl.exe -d '{\"name\":\"Alice Updated\"}'`) and discovered that PowerShell 5.1 splits the string across argv in a way that `curl.exe` interprets as multiple arguments, producing an empty body.
>
> **Fix:** I switched to writing the JSON body to a file and using `curl.exe --data-binary "@body-update.json"`. Verified with:
> ```
> curl.exe -s -X PUT http://localhost:8080/users/4 --data-binary "@body-update.json" -H "Content-Type: application/json"
> → {"created_at":"...","email":"charlie.updated@example.com","id":4,"name":"Charlie Updated"}
> ```
> The takeaway was that PowerShell's native quoting semantics are not compatible with `curl.exe`'s `-d` flag — the file-based payload is the reliable idiom for any JSON POST/PUT.

**Alternative troubleshooting entry (if you prefer):** the VPA `vpa-tls-certs` secret failure — `kubectl describe pod -n kube-system -l app=vpa-admission-controller` showed `MountVolume.SetUp failed for volume "tls-certs" : secret "vpa-tls-certs" not found`, fixed by generating the cert manually with `openssl` and `kubectl create secret generic`.


# Redeploy From Scratch — `usermgmt-02230125`

**Purpose:** Delete every application resource in the namespace and re-apply all manifests from the repo. No config changes, no rebuild, no cluster restart.

**Prerequisite:** `minikube tunnel` is running (Admin PowerShell) and the `127.0.0.1 usermgmt-02230125.local` hosts entry is present. `minikube image load usermgmt-api:1.0` was done previously.

---

## STEP 0 — Go to repo root

```powershell
cd "D:\Advanced System Administration\Assignment\User_Management"
```

---

## STEP 1 — Delete everything in the namespace

```powershell
kubectl delete namespace usermgmt-02230125 --wait=true
kubectl get namespaces | Select-String usermgmt
# (no output expected)
```

---

## STEP 2 — Confirm the API image is still loaded

```powershell
minikube image ls | Select-String usermgmt
# expected: docker.io/library/usermgmt-api:1.0
```

---

## STEP 3 — Re-apply all 10 manifests in numeric order

```powershell
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-postgres-secret.yaml
kubectl apply -f k8s/11-postgres-headless-service.yaml
kubectl apply -f k8s/12-postgres-statefulset.yaml
kubectl apply -f k8s/20-api-configmap.yaml
kubectl apply -f k8s/21-api-deployment.yaml
kubectl apply -f k8s/22-api-service.yaml
kubectl apply -f k8s/40-ingress.yaml
kubectl apply -f k8s/50-api-hpa.yaml
kubectl apply -f k8s/51-postgres-vpa.yaml
```

---

## STEP 4 — Wait for rollouts

```powershell
kubectl rollout status statefulset/postgres -n usermgmt-02230125 --timeout=180s
kubectl rollout status deployment/api       -n usermgmt-02230125 --timeout=180s
```

---

## STEP 5 — Verify all resources

```powershell
kubectl get all -n usermgmt-02230125
kubectl get pvc,ingress,hpa,vpa -n usermgmt-02230125
```

**Expected:**

| Resource | Ready / State |
|---|---|
| `statefulset.apps/postgres` | `1/1` |
| `deployment.apps/api` | `2/2` |
| `pod/postgres-0` | `1/1 Running` |
| `pod/api-...` (×2) | `1/1 Running` |
| `service/api` | `ClusterIP` on port 80 |
| `service/postgres` | `ClusterIP None` on port 5432 |
| `persistentvolumeclaim/data-postgres-0` | `Bound` |
| `ingress.networking.k8s.io/usermgmt-ingress` | host `usermgmt-02230125.local` |
| `horizontalpodautoscaler.autoscaling/api-hpa` | 2/6, `cpu: X%/50%` |
| `verticalpodautoscaler.autoscaling.k8s.io/postgres-vpa` | `MODE=Off` |

---

## STEP 6 — Access through the ingress hostname

```powershell
curl.exe -s -i http://usermgmt-02230125.local/users
```

**Expected (fresh PVC):**

```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 2

[]
```

Empty array = **fresh PVC, empty `users` table** = redeploy succeeded.

---

## STEP 7 — Full CRUD smoke test through the ingress

```powershell
# Create
'{"name":"Alice","email":"alice@example.com"}' | Out-File -Encoding ascii body.json
curl.exe -s -X POST http://usermgmt-02230125.local/users `
  -H "Content-Type: application/json" `
  --data-binary "@body.json"

# List (should show Alice with id=1)
curl.exe -s http://usermgmt-02230125.local/users

# Update
'{"name":"Alice Updated"}' | Out-File -Encoding ascii body-update.json
curl.exe -s -X PUT http://usermgmt-02230125.local/users/1 `
  -H "Content-Type: application/json" `
  --data-binary "@body-update.json"

# Delete
curl.exe -s -X DELETE http://usermgmt-02230125.local/users/1

# List again (should be [])
curl.exe -s http://usermgmt-02230125.local/users
```

**Expected responses:**

| Call | Response |
|---|---|
| POST | `{"id":1,"name":"Alice","email":"alice@example.com",...}` — 201 |
| GET /users | `[{"id":1,"name":"Alice",...}]` |
| PUT /users/1 | `{"id":1,"name":"Alice Updated",...}` |
| DELETE /users/1 | `{"deleted":1}` |
| GET /users | `[]` |

---

## Troubleshooting

### `kubectl delete namespace` hangs > 60s

PVC finalizer is stuck. Force it:

```powershell
kubectl patch pvc data-postgres-0 -n usermgmt-02230125 -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch namespace usermgmt-02230125 -p '{"spec":{"finalizers":[]}}' --type=merge
kubectl delete namespace usermgmt-02230125 --force --grace-period=0
```

Then resume from **STEP 2**.

### STEP 2 returns nothing (image lost)

Reload the image:

```powershell
cd "D:\Advanced System Administration\Assignment\User_Management"
docker build -t usermgmt-api:1.0 ./app
minikube image load usermgmt-api:1.0
minikube image ls | Select-String usermgmt
```

Then resume from **STEP 3**.

### `curl` fails with `Could not resolve host`

Tunnel or hosts entry gone. Restart tunnel (Admin PowerShell):

```powershell
minikube tunnel
```

Leave running. Retry **STEP 6**.

### `curl` returns `404 Not Found` (nginx page)

Wrong `Host:` header or ingress rule not synced. Confirm:

```powershell
kubectl describe ingress usermgmt-ingress -n usermgmt-02230125
```

Check `Rules:` block shows `usermgmt-02230125.local / api:80`. If missing, re-apply `k8s/40-ingress.yaml`.

### API pods `1/1 Running` but `/ready` returns 503

Postgres not yet ready, or password mismatch. Diagnose:

```powershell
kubectl logs -n usermgmt-02230125 deploy/api --tail=30
kubectl exec -n usermgmt-02230125 postgres-0 -- pg_isready -U appuser -d usermgmt
```

### HPA shows `<unknown>/50%`

Metrics-server stale. Restart it:

```powershell
kubectl rollout restart -n kube-system deploy/metrics-server
Start-Sleep -Seconds 30
kubectl get hpa -n usermgmt-02230125
```

---

## One-line summary

```powershell
cd "D:\Advanced System Administration\Assignment\User_Management"; `
kubectl delete namespace usermgmt-02230125 --wait=true; `
minikube image ls | Select-String usermgmt; `
kubectl apply -f k8s/00-namespace.yaml; `
kubectl apply -f k8s/10-postgres-secret.yaml; `
kubectl apply -f k8s/11-postgres-headless-service.yaml; `
kubectl apply -f k8s/12-postgres-statefulset.yaml; `
kubectl apply -f k8s/20-api-configmap.yaml; `
kubectl apply -f k8s/21-api-deployment.yaml; `
kubectl apply -f k8s/22-api-service.yaml; `
kubectl apply -f k8s/40-ingress.yaml; `
kubectl apply -f k8s/50-api-hpa.yaml; `
kubectl apply -f k8s/51-postgres-vpa.yaml; `
kubectl rollout status statefulset/postgres -n usermgmt-02230125 --timeout=180s; `
kubectl rollout status deployment/api -n usermgmt-02230125 --timeout=180s; `
kubectl get pvc,ingress,hpa,vpa -n usermgmt-02230125; `
curl.exe -s -i http://usermgmt-02230125.local/users
```
```
