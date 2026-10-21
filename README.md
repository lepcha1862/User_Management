
# User Management System — Three-Tier Microservices on Kubernetes

## Project Overview

This project deploys a three-tier User Management application on a local Kubernetes cluster using Minikube and Docker Desktop.

The application consists of:

1. **Frontend:** Static HTML and JavaScript served by Nginx.
2. **Backend API:** Flask REST API using `psycopg2`.
3. **Database:** PostgreSQL 16.4 deployed using a StatefulSet and PersistentVolumeClaim.

### Technology Stack

- Docker Desktop
- Minikube v1.39.0
- Kubernetes
- PostgreSQL 16.4
- Flask and Python
- Nginx
- Kubernetes Ingress
- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Metrics Server
- `hey` load-testing tool

### Project Configuration

| Component | Configuration |
|---|---|
| Project directory | `D:\Advanced System Administration\Assignment\User_Management` |
| Namespace | `usermgmt-02230125` |
| Hostname | `usermgmt-02230125.local` |
| API image | `usermgmt-api:1.3` |
| Frontend image | `usermgmt-frontend:1.0` |
| PostgreSQL StatefulSet | `postgres` |
| API Deployment | `api` |
| Frontend Deployment | `frontend` |
| API replicas | 2 initially |
| Frontend replicas | 2 initially |
| PostgreSQL replicas | 1 |
| PostgreSQL storage | 1 Gi PVC |
| HPA minimum replicas | 2 |
| HPA maximum replicas | 6 |
| HPA CPU target | 50% |

---

# PART 1 — ENVIRONMENT SETUP AND COMPLETE DEPLOYMENT

## Step 1: Open PowerShell

Open PowerShell and navigate to the project directory.

```powershell
cd "D:\Advanced System Administration\Assignment\User_Management"
```

Check the installed tools.

```powershell
docker --version
kubectl version --client
minikube version
```

Verify that Docker Desktop is running.

```powershell
docker info
```

**Expected result:** Docker should return information about the running Docker engine.

## Step 2: Start Minikube

Start the Kubernetes cluster using the Docker driver.

```powershell
minikube start --driver=docker --cpus=2 --memory=4096
```

Check the cluster status.

```powershell
minikube status
kubectl cluster-info
kubectl get nodes -o wide
```

**Expected result:** The Minikube node should be in the `Ready` state.

## Step 3: Enable Required Kubernetes Add-ons

Enable Ingress and Metrics Server.

```powershell
minikube addons enable ingress
minikube addons enable metrics-server
```

Check the system pods.

```powershell
kubectl get pods -n kube-system
```

Check the Ingress controller.

```powershell
kubectl get pods -n ingress-nginx
```

Wait until the required pods are running.

## Step 4: Verify the Project Structure

List the project files.

```powershell
Get-ChildItem
Get-ChildItem -Recurse -Filter "*.yaml"
```

The deployment manifests should include the following files:

```text
00-namespace.yaml
10-postgres-secret.yaml
11-postgres-headless-service.yaml
12-postgres-statefulset.yaml
13-postgres-init-configmap.yaml
20-api-configmap.yaml
21-api-deployment.yaml
22-api-service.yaml
30-frontend-deployment.yaml
31-frontend-service.yaml
40-ingress.yaml
50-api-hpa.yaml
51-postgres-vpa.yaml
```

The PostgreSQL initialization ConfigMap is optional if the project does not use it.

**Important:** Use the actual filenames present in your project. Apply manifests in dependency order.

## Step 5: Build the Backend API Image

Navigate to the backend API directory containing its Dockerfile.

```powershell
docker build -t usermgmt-api:1.3 ./backend
```

If the backend is in a subdirectory, navigate there before running the command or specify the correct build context.

Verify the image.

```powershell
docker images
```

## Step 6: Build the Frontend Image

Navigate to the frontend directory containing its Dockerfile.

```powershell
docker build -t usermgmt-frontend:1.0 ./frontend
```

Verify both application images.

```powershell
docker images
```

## Step 7: Load Images into Minikube

Load the API image.

```powershell
minikube image load usermgmt-api:1.3
```

Load the frontend image.

```powershell
minikube image load usermgmt-frontend:1.0
```

Verify the images are available.

```powershell
minikube image ls
```

**Why is this necessary?**

Minikube runs its own container environment. Loading locally built images makes them available to the Kubernetes workloads without requiring an image registry.

## Step 8: Create the Kubernetes Namespace

Apply the namespace manifest.

```powershell
kubectl apply -f k8s/00-namespace.yaml
```

Verify the namespace.

```powershell
kubectl get namespaces
kubectl get namespace usermgmt-02230125
```

## Step 9: Configure PostgreSQL

Apply the PostgreSQL Secret.

```powershell
kubectl apply -f k8s/10-postgres-secret.yaml
```

Create the headless Service.

```powershell
kubectl apply -f k8s/11-postgres-headless-service.yaml
```

Apply the StatefulSet.

```powershell
kubectl apply -f k8s/12-postgres-statefulset.yaml
```

If the project uses the initialization ConfigMap, apply it before the StatefulSet when required by its configuration.

```powershell
kubectl apply -f k8s/13-postgres-init-configmap.yaml
```

Check the database resources.

```powershell
kubectl get pods -n usermgmt-02230125
kubectl get statefulsets -n usermgmt-02230125
kubectl get services -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
```

Wait for PostgreSQL to become ready.

```powershell
kubectl rollout status statefulset/postgres -n usermgmt-02230125 --timeout=180s
```

Verify the database pod.

```powershell
kubectl get pod postgres-0 -n usermgmt-02230125
```

**Expected result:** `postgres-0` should be running and ready.

## Step 10: Deploy the Backend API

Apply the API configuration.

```powershell
kubectl apply -f k8s/20-api-configmap.yaml
```

Deploy the API.

```powershell
kubectl apply -f k8s/21-api-deployment.yaml
```

Create the API Service.

```powershell
kubectl apply -f k8s/22-api-service.yaml
```

Wait for the API rollout.

```powershell
kubectl rollout status deployment/api -n usermgmt-02230125 --timeout=180s
```

Check the API resources.

```powershell
kubectl get deployment api -n usermgmt-02230125
kubectl get pods -n usermgmt-02230125 -o wide
kubectl get service api -n usermgmt-02230125
```

Inspect API logs if the pods fail to start.

```powershell
kubectl logs deployment/api -n usermgmt-02230125
```

## Step 11: Deploy the Frontend

Apply the frontend Deployment.

```powershell
kubectl apply -f k8s/30-frontend-deployment.yaml
```

Create the frontend Service.

```powershell
kubectl apply -f k8s/31-frontend-service.yaml
```

Wait for the rollout.

```powershell
kubectl rollout status deployment/frontend -n usermgmt-02230125 --timeout=180s
```

Check the frontend.

```powershell
kubectl get deployment frontend -n usermgmt-02230125
kubectl get pods -n usermgmt-02230125
kubectl get service frontend -n usermgmt-02230125
```

## Step 12: Configure Ingress

Apply the Ingress manifest.

```powershell
kubectl apply -f k8s/40-ingress.yaml
```

Check the Ingress.

```powershell
kubectl get ingress -n usermgmt-02230125
kubectl describe ingress usermgmt-ingress -n usermgmt-02230125
```

Confirm that the hostname and paths match the actual Ingress manifest.

## Step 13: Configure HPA

Apply the Horizontal Pod Autoscaler.

```powershell
kubectl apply -f k8s/50-api-hpa.yaml
```

Check its configuration.

```powershell
kubectl get hpa -n usermgmt-02230125
kubectl describe hpa api-hpa -n usermgmt-02230125
```

The intended configuration is:

- Minimum replicas: 2
- Maximum replicas: 6
- Target CPU utilization: 50%

HPA requires working resource requests and a functioning Metrics Server.

## Step 14: Configure VPA

Apply the PostgreSQL VPA manifest.

```powershell
kubectl apply -f k8s/51-postgres-vpa.yaml
```

Check the VPA.

```powershell
kubectl get vpa -n usermgmt-02230125
kubectl describe vpa postgres-vpa -n usermgmt-02230125
```

The project uses recommendation-only mode (`Off`) for PostgreSQL. This allows VPA to provide resource recommendations without automatically changing the pod's resource requests.

If VPA has not been installed, follow the installation procedure documented in the project README before applying the manifest. Installing the VPA components may require Git Bash and OpenSSL for certificate generation.

## Step 15: Configure Local Hostname Access

Open PowerShell as Administrator.

Start the Minikube tunnel in a separate terminal.

```powershell
minikube tunnel
```

Keep that terminal running while testing the application.

Open the Windows hosts file.

```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```

Add the following entry if it is not already present.

```text
127.0.0.1 usermgmt-02230125.local
```

Save the file.

Verify hostname resolution.

```powershell
ping usermgmt-02230125.local
```

A successful ping is not required for HTTP functionality in every configuration; use the HTTP smoke tests below as the definitive application check.

## Step 16: Verify the Complete Deployment

Check all resources.

```powershell
kubectl get all -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
kubectl get ingress -n usermgmt-02230125
kubectl get hpa -n usermgmt-02230125
kubectl get vpa -n usermgmt-02230125
```

Check the frontend.

```powershell
curl.exe -i http://usermgmt-02230125.local/
```

Check the users endpoint.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

Check the health endpoint.

```powershell
curl.exe -i http://usermgmt-02230125.local/healthz
```

Check the readiness endpoint.

```powershell
curl.exe -i http://usermgmt-02230125.local/ready
```

The endpoints and their routing must match the actual application and Ingress configuration.

**Part 1 is complete when** the frontend loads, the API responds, PostgreSQL is ready, and the expected Kubernetes resources are healthy.

---

# PART 2 — REDEPLOYMENT PROCEDURE

## Step 1: Navigate to the Project

```powershell
cd "D:\Advanced System Administration\Assignment\User_Management"
```

Check the current resources.

```powershell
kubectl get all -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
```

## Step 2: Rebuild the Application Images if Required

If the source code has changed, rebuild the API image from its backend directory.

```powershell
docker build -t usermgmt-api:1.3 .
```

Rebuild the frontend image from its frontend directory.

```powershell
docker build -t usermgmt-frontend:1.0 .
```

If the image tag changes, update the corresponding Deployment manifest before redeploying.

## Step 3: Load the Images into Minikube

```powershell
minikube image load usermgmt-api:1.3
minikube image load usermgmt-frontend:1.0
```

Verify that the images are available.

```powershell
minikube image ls
```

## Step 4: Remove the Existing Namespace if a Full Reset Is Required

**Warning:** Deleting the namespace deletes its Kubernetes resources, including the PVC object. Depending on the PersistentVolume reclaim policy and storage configuration, the underlying database data may also be deleted.

Back up important data before performing a destructive reset.

```powershell
kubectl delete namespace usermgmt-02230125
```

Wait for namespace deletion.

```powershell
kubectl get namespace usermgmt-02230125
```

If deletion remains stuck, inspect the namespace conditions and finalizers before attempting any forceful cleanup.

For a routine application update, prefer applying the updated manifests without deleting the namespace.

## Step 5: Recreate the Namespace and Apply Manifests

Apply the namespace.

```powershell
kubectl apply -f 00-namespace.yaml
```

Apply the database resources.

```powershell
kubectl apply -f 10-postgres-secret.yaml
kubectl apply -f 11-postgres-headless-service.yaml
```

If used, apply the database initialization ConfigMap at the appropriate point.

```powershell
kubectl apply -f 13-postgres-init-configmap.yaml
```

Apply the PostgreSQL StatefulSet.

```powershell
kubectl apply -f 12-postgres-statefulset.yaml
```

Wait for PostgreSQL.

```powershell
kubectl rollout status statefulset/postgres -n usermgmt-02230125 --timeout=180s
```

Apply the API resources.

```powershell
kubectl apply -f 20-api-configmap.yaml
kubectl apply -f 21-api-deployment.yaml
kubectl apply -f 22-api-service.yaml
```

Apply the frontend resources.

```powershell
kubectl apply -f 30-frontend-deployment.yaml
kubectl apply -f 31-frontend-service.yaml
```

Apply Ingress and autoscaling resources.

```powershell
kubectl apply -f 40-ingress.yaml
kubectl apply -f 50-api-hpa.yaml
kubectl apply -f 51-postgres-vpa.yaml
```

Use only the manifest files that exist in the project.

## Step 6: Verify the Rollouts

```powershell
kubectl rollout status statefulset/postgres -n usermgmt-02230125 --timeout=180s
kubectl rollout status deployment/api -n usermgmt-02230125 --timeout=180s
kubectl rollout status deployment/frontend -n usermgmt-02230125 --timeout=180s
```

Inspect the resources.

```powershell
kubectl get pods -n usermgmt-02230125 -o wide
kubectl get deployments -n usermgmt-02230125
kubectl get services -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
kubectl get ingress -n usermgmt-02230125
kubectl get hpa -n usermgmt-02230125
kubectl get vpa -n usermgmt-02230125
```

## Step 7: Test the Application Again

```powershell
curl.exe -i http://usermgmt-02230125.local/
curl.exe -i http://usermgmt-02230125.local/users
curl.exe -i http://usermgmt-02230125.local/healthz
curl.exe -i http://usermgmt-02230125.local/ready
```

Test the CRUD operations as described in Part 3.

**Part 2 is complete when** all three tiers are healthy and the application passes its smoke tests after redeployment.

---

# PART 3 — VERIFICATION, DEMONSTRATIONS, AND TESTING

## Step 1: Demonstrate Kubernetes Resources

Show all resources in the application namespace.

```powershell
kubectl get all -n usermgmt-02230125
```

Show Deployments.

```powershell
kubectl get deployments -n usermgmt-02230125
kubectl describe deployment api -n usermgmt-02230125
kubectl describe deployment frontend -n usermgmt-02230125
```

Show Pods.

```powershell
kubectl get pods -n usermgmt-02230125 -o wide
```

Show Services.

```powershell
kubectl get services -n usermgmt-02230125
kubectl describe service api -n usermgmt-02230125
kubectl describe service frontend -n usermgmt-02230125
kubectl describe service postgres -n usermgmt-02230125
```

Show persistent storage.

```powershell
kubectl get pvc -n usermgmt-02230125
kubectl get pv
```

Show Ingress.

```powershell
kubectl get ingress -n usermgmt-02230125
kubectl describe ingress usermgmt-ingress -n usermgmt-02230125
```

## Step 2: Demonstrate the Request Path

The intended request flow is:

```text
Browser
   |
   v
usermgmt-02230125.local
   |
   v
Windows hosts file + Minikube tunnel
   |
   v
Ingress Controller
   |
   +---- "/" ----------------> Frontend Service
   |                               |
   |                               v
   |                         Frontend Pods
   |
   +---- "/users" ----------> API Service
   +---- "/healthz" --------> API Service
   +---- "/ready" ----------> API Service
                                   |
                                   v
                                API Pods
                                   |
                                   v
                              PostgreSQL Service
                                   |
                                   v
                              postgres-0 Pod
                                   |
                                   v
                              PersistentVolume
```

Confirm the actual path rules in `40-ingress.yaml`. The diagram must be adjusted if the manifest uses different paths.

## Step 3: Demonstrate the CRUD API

### 3.1 Retrieve Users

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

**Expected result:** An HTTP response containing the users collection, subject to the API's response format.

### 3.2 Create a User

Create a JSON request body.

```powershell
@'
{
  "name": "Demo User",
  "email": "demo@example.com"
}
'@ | Set-Content -Encoding ascii user.json
```

Send the request.

```powershell
curl.exe -i -X POST `
  http://usermgmt-02230125.local/users `
  -H "Content-Type: application/json" `
  --data-binary "@user.json"
```

The field names must match the API's actual validation rules.

### 3.3 Retrieve the Users Again

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

Confirm that the newly created user appears in the response.

### 3.4 Update a User

Replace `USER_ID` with the ID returned by the create request.

```powershell
@'
{
  "name": "Updated Demo User",
  "email": "updated@example.com"
}
'@ | Set-Content -Encoding ascii update-user.json
```

```powershell
curl.exe -i -X PUT `
  http://usermgmt-02230125.local/users/USER_ID `
  -H "Content-Type: application/json" `
  --data-binary "@update-user.json"
```

### 3.5 Delete a User

```powershell
curl.exe -i -X DELETE `
  http://usermgmt-02230125.local/users/USER_ID
```

Verify the result.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

**Demonstration evidence:** Capture the create, read, update, and delete responses.

## Step 4: Demonstrate Metrics Server

Check the Metrics Server deployment.

```powershell
kubectl get deployment metrics-server -n kube-system
```

Check node metrics.

```powershell
kubectl top nodes
```

Check pod metrics in the application namespace.

```powershell
kubectl top pods -n usermgmt-02230125
```

If metrics are unavailable, inspect the Metrics Server logs.

```powershell
kubectl logs deployment/metrics-server -n kube-system
```

Metrics may take a short time to become available after cluster startup.

## Step 5: Demonstrate HPA

Inspect the Horizontal Pod Autoscaler.

```powershell
kubectl get hpa -n usermgmt-02230125
kubectl describe hpa api-hpa -n usermgmt-02230125
```

Watch the API replica count.

```powershell
kubectl get hpa api-hpa -n usermgmt-02230125 --watch
```

In another terminal, monitor the API pods.

```powershell
kubectl get pods -n usermgmt-02230125 --watch
```

Check the configured resource requests.

```powershell
kubectl get deployment api -n usermgmt-02230125 -o yaml
```

The API HPA is configured with a minimum of two replicas, a maximum of six replicas, and a CPU utilization target of 50%.

**Important:** HPA scaling depends on actual resource utilization, resource requests, available metrics, and workload behavior. Do not claim that the Deployment reached six replicas unless the observed output confirms it.

## Step 6: Demonstrate VPA

Check the VPA resource.

```powershell
kubectl get vpa -n usermgmt-02230125
kubectl describe vpa postgres-vpa -n usermgmt-02230125
```

Inspect its recommendation fields in the output.

The VPA is configured in recommendation-only mode (`Off`). It can provide resource recommendations without automatically applying new resource requests to PostgreSQL pods.

If recommendations are missing, verify that the VPA components are installed and healthy.

```powershell
kubectl get pods -n kube-system
```

Do not report recommendations that are absent from the actual output.

## Step 7: Demonstrate Resource Requests and Limits

Inspect the API Deployment.

```powershell
kubectl get deployment api -n usermgmt-02230125 -o yaml
```

Inspect the frontend Deployment.

```powershell
kubectl get deployment frontend -n usermgmt-02230125 -o yaml
```

Inspect the PostgreSQL StatefulSet.

```powershell
kubectl get statefulset postgres -n usermgmt-02230125 -o yaml
```

The intended resource settings documented for the project are:

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---|---:|---:|---:|---:|
| API | 100m | 500m | 128Mi | 256Mi |
| Frontend | 20m | 100m | 32Mi | 64Mi |
| PostgreSQL | 100m | 500m | 256Mi | 512Mi |

Verify each value against the live manifest or resource specification before reporting it as the deployed configuration.

## Step 8: Install and Run `hey`

Check whether `hey` is installed.

```powershell
hey -version
```

If the command is unavailable, install `hey` using the appropriate installation instructions for your operating system.

Run a three-minute test with 50 concurrent workers.

```powershell
hey -z 3m -c 50 http://usermgmt-02230125.local/users
```

For a heavier test, run:

```powershell
hey -z 3m -c 200 http://usermgmt-02230125.local/users
```

Run only one test at a time if you want clearer measurements.

During the test, observe the HPA:

```powershell
kubectl get hpa api-hpa -n usermgmt-02230125 --watch
```

Observe pod counts:

```powershell
kubectl get pods -n usermgmt-02230125 --watch
```

Observe resource utilization:

```powershell
kubectl top pods -n usermgmt-02230125
```

Record the actual results reported by `hey`:

- Total requests
- Requests per second
- Average latency
- 95th-percentile latency
- Failed requests or non-successful responses
- Observed API replica count
- CPU and memory utilization

Do not invent test results. The measurements depend on the machine, cluster, application, and workload.

## Step 9: Demonstrate Frontend Independence

Record the initial state.

```powershell
kubectl get deployments -n usermgmt-02230125
kubectl get pods -n usermgmt-02230125
```

Delete the frontend Deployment.

```powershell
kubectl delete deployment frontend -n usermgmt-02230125
```

Check whether the API is still available.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

Check the frontend Deployment.

```powershell
kubectl get deployment frontend -n usermgmt-02230125
```

The API should continue to operate independently of the frontend, assuming its database and other dependencies remain healthy.

Restore the frontend.

```powershell
kubectl apply -f 30-frontend-deployment.yaml
kubectl rollout status deployment/frontend -n usermgmt-02230125 --timeout=180s
```

Reapply its Service if required.

```powershell
kubectl apply -f 31-frontend-service.yaml
```

Verify the frontend.

```powershell
curl.exe -i http://usermgmt-02230125.local/
```

## Step 10: Demonstrate Backend Independence

Record the initial state.

```powershell
kubectl get deployments -n usermgmt-02230125
kubectl get pods -n usermgmt-02230125
```

Delete the API Deployment.

```powershell
kubectl delete deployment api -n usermgmt-02230125
```

Check whether the frontend remains available.

```powershell
curl.exe -i http://usermgmt-02230125.local/
```

Check the API endpoint.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

The frontend static page may still load, but operations requiring the API may fail while the backend is unavailable.

Restore the API.

```powershell
kubectl apply -f 20-api-configmap.yaml
kubectl apply -f 21-api-deployment.yaml
kubectl apply -f 22-api-service.yaml
```

Wait for recovery.

```powershell
kubectl rollout status deployment/api -n usermgmt-02230125 --timeout=180s
```

Verify the API.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

**Note:** HPA may recreate the API Deployment or adjust its replicas during this test. Observe the live cluster rather than assuming a particular intermediate state.

## Step 11: Demonstrate Database Pod Recovery

Check PostgreSQL.

```powershell
kubectl get pods -n usermgmt-02230125
kubectl get statefulset postgres -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
```

Delete the PostgreSQL pod.

```powershell
kubectl delete pod postgres-0 -n usermgmt-02230125
```

Watch the StatefulSet recreate the pod.

```powershell
kubectl get pods -n usermgmt-02230125 --watch
```

In another terminal, check the PVC.

```powershell
kubectl get pvc -n usermgmt-02230125
```

Verify that the PostgreSQL pod becomes ready again.

```powershell
kubectl get pod postgres-0 -n usermgmt-02230125
```

Check the application endpoint.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

Deleting a pod is not the same as deleting its PVC. With the original claim and underlying storage preserved, a replacement PostgreSQL pod should reconnect to the persistent storage.

## Step 12: Demonstrate Database Persistence

**Purpose:** Verify that database records survive deletion and recreation of the PostgreSQL pod.

### 12.1 Create a Test Record

Create a record through the API using the CRUD procedure in Step 3.

Use a unique test value, such as:

```text
persistence-check-2026
```

Verify that the record appears in the users response.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

### 12.2 Delete the PostgreSQL Pod

```powershell
kubectl delete pod postgres-0 -n usermgmt-02230125
```

Wait for recovery.

```powershell
kubectl get pods -n usermgmt-02230125 --watch
```

### 12.3 Verify the Record

After PostgreSQL and the API are ready, retrieve the users collection again.

```powershell
curl.exe -i http://usermgmt-02230125.local/users
```

Confirm that the unique test record is still present.

Check the PVC.

```powershell
kubectl get pvc -n usermgmt-02230125
```

**Expected result:** If the PVC and underlying database storage remain intact, the record should survive PostgreSQL pod recreation.

A fresh or empty database is not proof of persistence. Confirm the same record before and after the recovery operation.

## Step 13: Demonstrate Service and Deployment Recovery

Check the Services.

```powershell
kubectl get services -n usermgmt-02230125
```

Check the Deployments.

```powershell
kubectl get deployments -n usermgmt-02230125
```

Check the Pods.

```powershell
kubectl get pods -n usermgmt-02230125 -o wide
```

Check recent events.

```powershell
kubectl get events -n usermgmt-02230125 --sort-by=.metadata.creationTimestamp
```

Inspect a Deployment if it does not become ready.

```powershell
kubectl describe deployment api -n usermgmt-02230125
kubectl describe deployment frontend -n usermgmt-02230125
```

Inspect pod logs.

```powershell
kubectl logs deployment/api -n usermgmt-02230125
kubectl logs deployment/frontend -n usermgmt-02230125
```

## Step 14: Final End-to-End Verification

Run the final checks.

```powershell
kubectl get nodes
kubectl get all -n usermgmt-02230125
kubectl get pvc -n usermgmt-02230125
kubectl get ingress -n usermgmt-02230125
kubectl get hpa -n usermgmt-02230125
kubectl get vpa -n usermgmt-02230125
kubectl top nodes
kubectl top pods -n usermgmt-02230125
```

Test all application endpoints.

```powershell
curl.exe -i http://usermgmt-02230125.local/
curl.exe -i http://usermgmt-02230125.local/users
curl.exe -i http://usermgmt-02230125.local/healthz
curl.exe -i http://usermgmt-02230125.local/ready
```

## Final Demonstration Checklist

- [ ] Minikube cluster is running.
- [ ] Namespace `usermgmt-02230125` exists.
- [ ] PostgreSQL StatefulSet is ready.
- [ ] PostgreSQL PVC is Bound.
- [ ] API Deployment is ready.
- [ ] Frontend Deployment is ready.
- [ ] API, frontend, and PostgreSQL Services exist.
- [ ] Ingress routes requests using the configured hostname.
- [ ] Frontend loads through the browser or HTTP request.
- [ ] API health and readiness endpoints respond correctly.
- [ ] CRUD operations work.
- [ ] Metrics Server provides metrics.
- [ ] HPA configuration and behavior are demonstrated.
- [ ] VPA configuration and recommendations are inspected.
- [ ] Resource requests and limits are verified.
- [ ] `hey` load-test measurements are recorded.
- [ ] Frontend and backend independence are demonstrated.
- [ ] PostgreSQL pod recovery is demonstrated.
- [ ] Database persistence is verified using the same record.
- [ ] Final Kubernetes resources are healthy.

## Conclusion

The project demonstrates how a three-tier User Management application can be deployed and operated using Kubernetes. The frontend, backend API, and PostgreSQL database run as separate workloads connected through Services and Ingress.

Kubernetes Deployments and StatefulSets provide workload management and recovery. Persistent storage supports database durability across pod recreation. HPA demonstrates horizontal scaling of the API, while VPA provides PostgreSQL resource recommendations. Metrics Server and `hey` help observe resource utilization and application performance under load.

All final conclusions should be supported by actual cluster output, HTTP responses, and load-test measurements.
