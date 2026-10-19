# User_Management

**Expected:** `Count : ` shows at least 4-5 occurrences of the hostname. If not, edit the file.

---

### 🔹 STEP 20b — Report outline (≤8 pages PDF, M6's 0.25 marks)

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

**Section 7 — Troubleshooting (the 0.25-mark one, requires a real diagnosis with commands):**

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

---

### 🔹 STEP 20c — Demo Q&A crib sheet (M6's 0.5 marks)

**What it does:** Anticipates every question listed in the assignment and gives a concise answer. Memorize the bold line; the rest is context.

| Question | Canned answer |
|---|---|
| **Why does a StatefulSet suit a database better than a Deployment?** | **StatefulSet gives stable network identity (`postgres-0`), ordered start/stop, and `volumeClaimTemplates` that bind a unique PVC to each replica.** A Deployment creates anonymous pods with random names and needs a shared (usually RWX) PVC — which our hostpath provisioner doesn't support. |
| **What would change with a Deployment + one PVC?** | If the Pod was ever moved to another node, the PV couldn't reattach unless the `nodeAffinity` matched; also, only one replica could run at a time (RWO volume). No stable DNS name. No ordered restarts. |
| **What happens to the PVC when you delete the StatefulSet?** | **The PVC is retained** — that's how StatefulSet enforces data safety. To delete it, you must `kubectl delete pvc data-postgres-0` explicitly. This is why we could safely delete and recreate the StatefulSet during development. |
| **If `postgres-0` is restarted, what happens to the api Pods?** | **They fail readiness.** `/ready` does `SELECT 1`; when Postgres is unreachable, all api pods return 503 from readiness → they're removed from `api` Service endpoints → Ingress has no backend → clients see 503. They auto-recover when Postgres returns. |
| **Why does the HPA need CPU requests?** | **The HPA target is a *percentage of the request*, not an absolute value.** Without `resources.requests.cpu: 100m`, the HPA cannot compute utilisation and refuses to scale (it reports `<unknown>/50%`). Requests are also what the scheduler uses to pick nodes. |
| **Where does traffic enter the cluster, and which object decides which Service receives it?** | **Entry point = the ingress-nginx controller** (exposed on `127.0.0.1:80` by `minikube tunnel`). The **`Ingress` object** (`usermgmt-ingress`) matches the `Host:` header against its `rules[].host` and forwards to `service.api:80`. The Service then round-robins to one of the two api pods. |
| **(Bonus) How would you prove persistence to a skeptic?** | **Delete `postgres-0` while watching `kubectl get pods -w`; the StatefulSet recreates it within 20s. Then `kubectl exec postgres-0 -- psql -c "SELECT * FROM users"` returns the same rows** — proof that the PVC reattached, not a fresh volume. |
| **(Bonus) Why "Off" update mode on the VPA?** | **Eviction of a singleton DB pod breaks readiness for the entire API tier.** See the report paragraph in Step 19. |

---

### 🔹 STEP 20d — Fresh-cluster redeploy test (safety net, ~10 min)

**What it does:** Deletes your namespace, re-runs the README from scratch, confirms everything comes back. This is **what the marker will do** — you want to catch any missing step *now*.

**Why needed:** Submitting with a broken README is the #1 cause of marks being lost in M6. This is the highest-value 10 minutes you can spend.

### Commands

```powershell
# 20d-1. Delete everything you created
kubectl delete namespace usermgmt-02230125 --wait=true
kubectl get namespaces | Select-String usermgmt   # should be empty

# 20d-2. Follow the README step by step
# (open README.md, execute commands verbatim, but SKIP steps 1–3 if you don't want to rebuild the cluster)

# 20d-3. Once the README completes, verify everything
kubectl get all -n usermgmt-02230125
kubectl get pvc,ingress,hpa,vpa -n usermgmt-02230125
curl.exe http://usermgmt-02230125.local/users
