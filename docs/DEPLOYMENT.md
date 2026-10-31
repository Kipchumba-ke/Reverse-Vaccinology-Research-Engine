# Deploying ReverseVax: frontend on Netlify, API on your own server

```text
 Browser ──► Netlify (static React app)
    │
    └──────► https://api.example.com ──► Caddy (HTTPS) ──► API ──► Postgres
                                                           │  └──► Redis ──► Worker (BLAST, predictors)
                                                           └── reference data on the server's disk
```

**Why two places.** Netlify serves static files and short serverless functions. It cannot run the Flask API, Postgres, Redis, the Celery worker, BLAST or the reference databases, and its proxy gives up after 26 seconds. So Netlify hosts only the React app, and the browser talks to the API directly over HTTPS. This also means the API sees each visitor's real IP address, which the rate limits depend on.

You need:

- a GitHub repository with this code (you have this);
- a domain name you can add DNS records to (for example `example.com`, with the API at `api.example.com`);
- a Linux server (a VPS) for the backend. A sensible start is 4 GB of RAM and 40 GB of disk with Ubuntu 24.04; that is an estimate, not a measurement, so watch memory and disk after launch;
- a free Netlify account.

Replace `api.example.com`, `yoursite.netlify.app` and similar placeholders everywhere below.

---

## Part 1: The backend server

### 1. Prepare the server

Log in over SSH, then:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git ncbi-blast+ python3-venv
curl -fsSL https://get.docker.com | sudo sh        # installs Docker and Compose
sudo usermod -aG docker $USER                      # then log out and back in

sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

`ncbi-blast+` is needed on the host only to build the reference databases (step 4). Use SSH keys rather than passwords, and keep the server updated.

### 2. Point a DNS name at the server

At your domain registrar or DNS provider, add an **A record**: name `api`, value = the server's public IP address. Check it with `ping api.example.com` after a few minutes. Caddy cannot get a certificate until this works.

### 3. Get the code and write the server's `.env`

```bash
git clone https://github.com/Kipchumba-ke/reverse-vaccinology-research-engine.git
cd reverse-vaccinology-research-engine
```

Generate two secrets (run the command twice, once for each):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Create `.env` in the repository root (this file is git-ignored; never commit it):

```bash
POSTGRES_PASSWORD=<first secret, or a shorter token_urlsafe(24)>
JWT_SECRET_KEY=<second secret>
API_DOMAIN=api.example.com
CORS_ALLOWED_ORIGINS=https://yoursite.netlify.app

# Predictors you have access to (all optional)
IEDB_ENABLED=1
DEEPTMHMM_ENABLED=1
BIOLIB_TOKEN=<token from your BioLib account settings>
INSTALL_BIOLIB=1
```

Notes:

- Set `POSTGRES_PASSWORD` **before the first start**. Postgres keeps the password it was created with; changing the variable later does not change it. Use letters, digits, `-` and `_` only, so it is safe inside a database URL.
- `CORS_ALLOWED_ORIGINS` must be the exact address people use to open the site, with `https://` and no trailing slash. Add a custom domain later, comma-separated.
- Leave PSORTb and SignalP off. PSORTb's Docker mode cannot run inside the worker container, and SignalP is not set up (see the README).
- Do not write a space or quote after a value: `KEY=value`.

### 4. Build the reference data

The databases are not in the Docker image, and users never download them: the server reads them while analysing.

```bash
./scripts/download_host_proteomes.sh
./scripts/build_host_blast_databases.sh
```

This needs internet access to UniProt and takes a while for the human proteome. For the optional ePath (KO) essentiality data, copy your three source files over from your computer, then build the database:

```bash
# on your computer
scp a_Gene_sort.txt Combined_KOExpEG.txt Experimental_EG.txt you@api.example.com:~/reverse-vaccinology-research-engine/data/reference/essentiality/

# on the server
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
python -m app.integrations.build_epath_index
python -m app.integrations.import_epath_evidence
deactivate
```

Skip the ePath part if you do not have the data; analyses still work and say the lookup is not set up.

### 5. Start the backend

Name the services explicitly so the `web` container (which is for the all-in-Docker setup) does not start:

```bash
docker compose --profile app --profile public up -d --build postgres redis migrate api worker caddy
docker compose ps
```

The first build takes several minutes. Check it:

```bash
docker compose logs --tail 50 api
curl -i https://api.example.com/api/health      # should answer 200
```

If `curl` fails, see Troubleshooting. Compose restarts the services after a reboot.

### 6. Check the cross-site (CORS) setup

```bash
curl -i -X OPTIONS https://api.example.com/api/login \
  -H "Origin: https://yoursite.netlify.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```

The response should include `access-control-allow-origin: https://yoursite.netlify.app`. If not, fix `CORS_ALLOWED_ORIGINS` in `.env` and run:

```bash
docker compose --profile app --profile public up -d api worker
```

---

## Part 2: The frontend on Netlify

### 7. Create the site

1. In Netlify choose **Add new site → Import an existing project → GitHub** and pick the repository and the `main` branch.
2. The build settings come from `netlify.toml` in the repository (base `frontend`, command `npm run build`, publish `dist`). Leave them as they are.
3. Open **Site configuration → Environment variables** and add `VITE_API_BASE_URL` = `https://api.example.com` (no trailing slash). The value is baked in at build time, so add it before the first deploy, or redeploy with **Clear cache and deploy site** afterwards.

### 8. Tell the browser it may call your API

Open `netlify.toml` and replace `https://api.example.com` inside `connect-src` with your real API address. Without this the browser blocks every API call and the console shows a Content-Security-Policy error. Commit and push:

```bash
git checkout -b netlify-config
# edit netlify.toml
git commit -am "Set the API address in the Netlify headers"
git push -u origin netlify-config      # open a pull request and merge it
```

Netlify deploys each time `main` changes.

### 9. Optional: your own domain

In Netlify, **Domain management → Add a domain**, and follow the DNS instructions; Netlify issues the HTTPS certificate. Then add the new address to `CORS_ALLOWED_ORIGINS` on the server (comma-separated) and recreate the API: `docker compose --profile app --profile public up -d api worker`.

Deploy previews (the `deploy-preview-…netlify.app` addresses) are different origins, so they cannot reach the API unless you add them to `CORS_ALLOWED_ORIGINS` too.

---

## Part 3: Test it

Open the Netlify site with the browser's developer tools console open.

- [ ] The page loads in the dark theme with no red errors.
- [ ] Register an account and sign in.
- [ ] Run an analysis with a short protein; it moves from pending to completed.
- [ ] The report shows **Prediction Tools** with the states you expect, and a host similarity result if you chose Human, Mouse or Pig.
- [ ] Download the PDF.
- [ ] No Content-Security-Policy or CORS messages appear in the console.

Then close sign-up if the site is for a known group of users: set `REGISTRATION_ENABLED=0` in `.env` and run `docker compose --profile app --profile public up -d api`.

---

## Part 4: Keeping it running

**Back up the database** daily. Add this with `crontab -e` (as your user, from the repository folder):

```bash
0 2 * * * cd ~/reverse-vaccinology-research-engine && docker compose exec -T postgres pg_dump -U vaccinology reverse_vaccinology | gzip > ~/backups/rv-$(date +\%F).sql.gz
```

Create `~/backups` first, copy backups off the server, and test a restore once:

```bash
gunzip -c ~/backups/rv-2026-11-01.sql.gz | docker compose exec -T postgres psql -U vaccinology reverse_vaccinology
```

**Update** after merging changes to `main`:

```bash
cd ~/reverse-vaccinology-research-engine
git pull
docker compose --profile app --profile public up -d --build postgres redis migrate api worker caddy
```

The frontend updates itself on Netlify.

**Watch** `docker compose ps`, `docker compose logs --tail 100 worker`, and `df -h` (disk) and `free -h` (memory). Merge the Dependabot pull requests, and run `pip-audit -r requirements.txt` and `npm audit` now and then.

---

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `curl https://api…` times out or the certificate fails | The DNS A record is missing or not yet live, or ports 80 and 443 are closed. Check `ping api.example.com`, `sudo ufw status`, and `docker compose logs caddy` |
| Browser console: *blocked by CORS policy* | `CORS_ALLOWED_ORIGINS` does not exactly match the site's address (scheme, no trailing slash). Fix it and recreate `api` |
| Browser console: *violates Content-Security-Policy … connect-src* | `netlify.toml` still has `https://api.example.com`, or `VITE_API_BASE_URL` was missing at build time. Fix, push, and redeploy |
| The site calls `/api/...` on its own address and gets 404 | `VITE_API_BASE_URL` was not set before the build. Add it and clear cache and deploy |
| Analysis stays pending | The worker is not running or crashed. `docker compose logs worker` |
| Login rate limit hits everyone at once | The API is not seeing real client IPs. The API must be reached through Caddy only, with `TRUSTED_PROXY_COUNT` at 1 (the Compose default) |
| Report says no BLAST database is configured | Step 4 was skipped, or the files are not in `data/reference/<host>/` |
| A predictor shows "Not set up" or "Failed" | The Prediction Tools section gives the reason; for BioLib, check `BIOLIB_TOKEN` and that the image was built with `INSTALL_BIOLIB=1` |
| `docker compose up` says a password is wrong for the database | `POSTGRES_PASSWORD` was changed after the first start. Restore the old value, or reset the database volume if it holds nothing you need |

## What this setup does not give you

No monitoring or alerting, no automatic off-server backups, a single server with no failover, and no staging environment. For a portfolio or small research group that is a reasonable start; add them if real users depend on it.
