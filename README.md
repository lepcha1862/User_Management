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


### Fresh-cluster redeploy test

**What it does:** Deletes your namespace, re-runs the README from scratch, confirms everything comes back.

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
