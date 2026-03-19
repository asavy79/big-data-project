# Frontend (JobMatch UI)

A single-page React application that provides Google sign-in, a profile editor, and a match results viewer. It communicates with the User Service and Job Discovery Service through a reverse proxy layer.

## Tech Stack

- **React 19** with TypeScript
- **Vite 6** for dev server and production builds
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin
- **Firebase SDK** (`firebase/auth`) for Google sign-in via popup
- **nginx** for production static serving and API reverse proxy (in Docker)

## Directory Structure

```
frontend/
├── index.html               # HTML shell — Vite injects the script tag
├── vite.config.ts           # Vite plugins (React + Tailwind) and dev proxy config
├── nginx.conf               # Production reverse proxy for Docker (routes /api/* to backends)
├── Dockerfile               # Multi-stage: node build → nginx serve
├── .env.local               # ** Firebase config goes here ** (not committed to git)
├── src/
│   ├── main.tsx             # React DOM entry point
│   ├── App.tsx              # Root component — renders Login or Dashboard based on auth state
│   ├── index.css            # Tailwind v4 import (@import "tailwindcss")
│   ├── firebase.ts          # Firebase app init + GoogleAuthProvider setup
│   ├── types.ts             # Shared TypeScript interfaces (UserProfile, JobDetail, etc.)
│   ├── contexts/
│   │   └── AuthContext.tsx   # React context providing user, loading, signInWithGoogle, logout
│   ├── api/
│   │   └── client.ts        # Typed fetch wrapper — injects X-Firebase-UID on every call
│   ├── pages/
│   │   ├── Login.tsx         # Full-page Google sign-in with gradient background
│   │   └── Dashboard.tsx     # Two-column layout: ProfileForm + MatchList
│   └── components/
│       ├── Header.tsx        # Top bar with user avatar, name, and sign-out button
│       ├── ProfileForm.tsx   # Editable profile card with skill tags, salary, remote toggle
│       └── MatchList.tsx     # Displays matched jobs with title, company, location, Apply link
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
└── package.json
```

## Authentication Flow

1. User clicks "Sign in with Google" on the Login page.
2. `firebase/auth.signInWithPopup()` opens a Google OAuth popup.
3. On success, `onAuthStateChanged` fires, `AuthContext` stores the `User` object.
4. `App.tsx` switches from `<Login />` to `<Dashboard />`.
5. Every API call includes the Firebase UID via the `X-Firebase-UID` header (extracted from `user.uid`).

The `AuthContext` (`contexts/AuthContext.tsx`) exposes:
- `user` — Firebase `User | null`
- `loading` — `true` while Firebase initializes
- `signInWithGoogle()` — triggers the popup
- `logout()` — signs out and returns to Login

## API Communication

`api/client.ts` provides two factory functions:

### `userApi(uid: string)`

Calls the User Service. Injects `X-Firebase-UID` on all requests.

| Method | Path              | Maps to User Service |
|--------|-------------------|----------------------|
| GET    | `/api/user/me`          | `GET /me`          |
| PATCH  | `/api/user/me`          | `PATCH /me`        |
| GET    | `/api/user/me/matches`  | `GET /me/matches`  |

### `jobsApi()`

Calls the Job Discovery Service for job detail lookups.

| Method | Path                    | Maps to Job Discovery Service |
|--------|-------------------------|-------------------------------|
| GET    | `/api/jobs/jobs/{id}`   | `GET /jobs/{id}`              |

### Proxy Configuration

**Development (Vite dev server, `vite.config.ts`):**
- `/api/user/*` → `http://localhost:8002/*` (User Service)
- `/api/jobs/*` → `http://localhost:8001/*` (Job Discovery Service)

**Production (nginx, `nginx.conf`):**
- `/api/user/*` → `http://user-service:8000/*` (Docker internal DNS)
- `/api/jobs/*` → `http://job-discovery-service:8000/*`

## Pages and Components

### Login (`pages/Login.tsx`)

Full-screen centered card with:
- App name and tagline
- "Sign in with Google" button with official Google "G" SVG icon
- Blue-to-indigo gradient background

### Dashboard (`pages/Dashboard.tsx`)

Responsive two-column grid (`lg:grid-cols-2`, stacks on mobile):
- Left column: `ProfileForm`
- Right column: `MatchList`
- Top: `Header` bar

### Header (`components/Header.tsx`)

Fixed top bar showing:
- App logo and name
- User's Google avatar (from `user.photoURL`)
- Display name
- Sign-out button

### ProfileForm (`components/ProfileForm.tsx`)

On mount, calls `GET /me` to load existing profile. Renders editable fields:

| Field              | Input Type       | Notes                                      |
|--------------------|------------------|--------------------------------------------|
| Name               | Text input       | Pre-filled from Firebase display name      |
| Bio                | Textarea         | Free-text description                      |
| Skills             | Tag input        | Type + Enter to add, click X to remove     |
| Location           | Text input       | e.g. "Denver, CO"                          |
| Open to remote     | Toggle switch    | Boolean                                    |
| Min/Max Salary     | Number inputs    | Side-by-side                               |

"Save & Find Matches" button calls `PATCH /me`, which triggers the full matching pipeline on the backend. A success message confirms the profile was saved and matching is running in the background.

### MatchList (`components/MatchList.tsx`)

On mount, calls `GET /me/matches` to get the latest match set. For each job ID in the most recent match, calls `GET /jobs/{id}` (via `Promise.allSettled`) to fetch full details.

Each job card shows:
- Title and company
- Location badge, Remote badge, Salary range badge
- "Apply" link button (opens `job_apply_link` in new tab)

Empty state shown when no matches exist yet. Manual "Refresh" button to re-fetch.

## TypeScript Interfaces (`types.ts`)

These match the backend Pydantic schemas exactly (snake_case field names):

- `UserProfile` — full user profile response from `GET /me`
- `UserUpdate` — partial update body for `PATCH /me`
- `JobMatch` — single match set: `matched_job_ids` + `calculated_at`
- `MatchesResponse` — paginated wrapper: `matches[]` + `total`
- `JobDetail` — full job record from `GET /jobs/{id}`

## Firebase Configuration

The Firebase SDK reads config from Vite environment variables (prefixed with `VITE_`). These must be set in `frontend/.env.local`:

```
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
```

Get these from [Firebase Console](https://console.firebase.google.com) → Project Settings → Your Apps → Web app config.

You must also enable Google sign-in: Firebase Console → Authentication → Sign-in method → Google → Enable.

## Running

### Local Development

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

Requires the User Service on port 8002 and Job Discovery Service on port 8001 (run via `docker compose up postgres user-service job-discovery-service`).

### Docker (Production Build)

```bash
docker compose up frontend    # → http://localhost:3000
```

The Dockerfile runs a multi-stage build: `npm ci && npm run build` in a Node image, then copies the `dist/` output into an nginx image with the reverse proxy config.

Note: `.env.local` must be present in the `frontend/` directory before building the Docker image, since Vite bakes `VITE_*` variables into the JavaScript bundle at build time.
