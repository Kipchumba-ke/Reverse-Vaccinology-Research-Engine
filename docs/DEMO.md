# Recording the demo

A 2–3 minute screen recording is the best way to show ReverseVax without running a server for it. Record it on your own machine with everything running locally (see the README's Getting started).

## Before you record

- Start the API, the worker, Postgres, Redis and the frontend.
- Use a throwaway account and email address, not a personal one.
- Close terminals, editors and browser tabs that show `.env`, tokens or secrets, and turn off notifications.
- Pick a protein you can explain, ideally one with a UniProt accession so the 3-D structure and database evidence appear. Run it once beforehand so you know how long it takes and what the report shows.
- Switch on the predictors you actually have (for example IEDB and DeepTMHMM). Leave the others off: the Prediction Tools section shows them as not set up, which is honest and worth showing.
- Record at 1080p in the light theme or the dark one, but use the same one throughout.

## Shot list (about 2 minutes 45 seconds)

| Time | Show | Say |
| --- | --- | --- |
| 0:00 | Landing page | What it is: an evidence ledger for vaccine-target discovery, not a predictor of good targets |
| 0:15 | Register or sign in | Accounts and per-user history |
| 0:25 | New analysis: paste the sequence, choose the host, submit | What you are asking it to screen |
| 0:50 | Status moving to completed | Runs in a background worker. Cut or speed up the wait |
| 1:00 | Report: protein, composition, hydropathy chart, transmembrane map | Heuristic screens, with captions |
| 1:30 | Prediction Tools section | Which tools ran and which did not, and why |
| 1:50 | Host similarity, evidence, candidate assessment | Supporting evidence, concerns and missing evidence, with no score |
| 2:15 | Limitations | Say plainly what the report does not show |
| 2:30 | Download the PDF and scroll through it | Same sections and numbering as the screen |
| 2:45 | End card | Link to the repository |

## After you record

1. Upload it (for example to YouTube as **Unlisted**).
2. Put the link in the README's Demo section.
3. In Netlify, add the environment variable `VITE_DEMO_VIDEO_URL` with the same `https://` link and redeploy. The "Watch the demo" link then appears on the landing, sign-in and register pages.
