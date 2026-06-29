# A.C.E. — AI Casino Education

A.C.E. is an interactive casino-learning application that combines a Flask backend with a React frontend to teach and practice casino games in a guided environment. The current experience includes a main menu, player name setup, a game-selection flow, and playable interfaces for blackjack, roulette, and slots.

## Overview

This repository contains the full application stack for the A.C.E. project:
- A Python/Flask backend for game logic, API routes, session handling, and stats persistence
- A React frontend for the menu, tutorial, stats, and game screens
- Supporting assets and documentation for the project

## Current Behavior

The app currently provides:
- A start screen that asks for the player's name and initializes a new session
- A post-login menu with buttons for Play, Tutorial, Stats, and Quit
- A game-selection submenu that lets players choose Blackjack, Roulette, or Slots
- A blackjack table with deal/hit/stand/double actions and chip tracking
- A roulette table with betting controls, wheel spin animation, and result feedback
- A slots table screen for the current slots experience
- Persistent player stats through the backend database layer

## Team

- Colby Fournier — Frontend UI and experience design
- Cisco Harbeck — Backend and database work
- Reymond Sanchez — Game logic and AI systems

## Requirements

- Python 3.9 or newer
- Node.js 18+ and npm
- pip

## Setup

1. Clone the repository
   ```bash
   git clone https://github.com/fournierc2atwit/senior_project_2026_ACE
   cd senior_project_2026_ACE
   ```

2. Create and activate a Python virtual environment
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

3. Install backend dependencies
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Install frontend dependencies
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Running the App

Start the backend from the project root:
```bash
python backend/app.py
```

In a second terminal, start the frontend:
```bash
cd frontend
npm start
```

The frontend is typically served at http://localhost:3000, and the Flask API runs on http://127.0.0.1:5000.

## Project Structure

```text
senior_project_2026_ACE/
├── assets/
│   └── cards/
│       └── fonts/
│           └── sounds/
│               └── images/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── test_app.py
│   ├── ai/
│   │   ├── advise.py
│   │   ├── counting.py
│   │   ├── count_advise.py
│   │   └── strategy.py
│   ├── database/
│   │   ├── db.py
│   │   ├── stats.py
│   │   ├── test_db.py
│   │   └── test_stats.py
│   └── game/
│       ├── blackjack/
│       ├── roulette/
│       └── slots/
├── docs/
├── frontend/
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js
│       └── components/
│           ├── blackjack/
│           ├── roulette/
│           ├── slots/
│           ├── Menu.jsx
│           ├── Stats.jsx
│           ├── Tutorial.jsx
│           └── related CSS files
└── README.md
```

## Features

### Gameplay
- Blackjack round flow with deal, hit, stand, and double-down actions
- Roulette wheel spins with bet placement and result feedback
- Slots experience screen with current game flow and stats hooks
- Player chip/bankroll handling across sessions

### Learning Support
- Tutorial and stats navigation from the main menu
- Session-based and saved player statistics through the backend database
- Educational UI flow for moving between menu, game, and reference screens

### User Experience
- Menu-driven navigation for game selection and screen transitions
- Responsive React-based interface for the current casino experience

## Technology Stack

| Area | Technology |
|------|------------|
| Backend | Python, Flask |
| API | Flask-CORS, JSON endpoints |
| Database | SQLite-based persistence |
| Frontend | React, Create React App-style React app |
| Package Management | pip, npm |

## Testing

The backend includes tests for app and database behavior. To run the suite:

```bash
cd backend
python -m pytest
```

## Contributing

Contributions are welcome. Please keep the backend/frontend separation intact and coordinate with the team before changing game logic or navigation behavior.

## License

License details are still being finalized for this project.
