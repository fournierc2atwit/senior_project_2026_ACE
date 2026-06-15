# A.C.E. — AI Casino Education

A.C.E. is an AI-assisted Blackjack training project designed to help players learn strategy, understand odds, and improve decision-making in a low-risk, interactive environment. The project currently combines a Flask backend for gameplay and stats, a React frontend for the user interface, and supporting assets for the card-based experience.

## Overview

This repository contains the full application stack for the A.C.E. project:
- Python/Flask backend for the game engine, API routes, and player statistics
- React frontend for the visual Blackjack table, controls, HUD, and tutorial views
- Local assets and documentation for the game experience and project planning

## Team

- Colby Fournier — Game Logic Developer and UI Designer
- Cisco Harbeck — Game Logic Developer and Backend/Database Lead
- Reymond Sanchez — Game Logic Developer and AI Systems Lead

## Current Status

The project is under active development. The backend provides the core game loop and API endpoints, while the frontend is being used to present the game experience to the player.

## Requirements

- Python 3.9 or newer
- Node.js 18+ and npm
- pip

## Setup

1. Clone the project
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

The frontend is typically available at http://localhost:3000, while the Flask API runs on the backend server.

## Project Structure

```text
senior_project_2026_ACE/
├── .git/                          # Git metadata
├── .gitignore
├── .vscode/                       # VS Code workspace settings
├── assets/
│   └── cards/
│       └── fonts/
│           └── sounds/
│               └── images/        # Empty asset folder for future art/audio files
├── backend/
│   ├── .env                       # Local environment variables
│   ├── __init__.py
│   ├── app.py                     # Flask app and API routes
│   ├── requirements.txt           # Python dependencies
│   ├── test_app.py                # Backend API tests
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── advise.py
│   │   ├── counting.py
│   │   ├── count_advise.py
│   │   └── strategy.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── stats.py
│   │   ├── test_db.py
│   │   └── test_stats.py
│   └── game/
│       ├── __init__.py
│       ├── card.py
│       ├── deck.py
│       ├── hand.py
│       ├── player.py
│       └── rules.py
├── docs/
│   ├── 5_10 Project Proposal.pdf
│   ├── Design Doc.pdf
│   └── Project Plan.pdf
├── frontend/
│   ├── .gitignore
│   ├── package-lock.json
│   ├── package.json               # React app dependencies and scripts
│   ├── README.md
│   ├── public/
│   │   ├── index.html
│   │   ├── manifest.json
│   │   ├── robots.txt
│   │   └── ...
│   └── src/
│       ├── App.css
│       ├── App.js
│       ├── index.css
│       ├── index.js
│       └── components/
│           ├── Card.jsx
│           ├── Hand.css
│           ├── Hand.jsx
│           ├── Hud.css
│           ├── Hud.jsx
│           ├── Menu.css
│           ├── Menu.jsx
│           ├── Stats.css
│           ├── Stats.jsx
│           ├── Table.css
│           ├── Table.jsx
│           └── Tutorial.css
│           └── Tutorial.jsx
├── venv/                           # Python virtual environment
└── README.md
```

## Features

### Gameplay
- Blackjack round flow with deal, hit, stand, and double-down actions
- Dealer logic and winner determination
- Player chip/bankroll management

### Learning Support
- Strategy hints and educational feedback during play
- Session-based and saved player statistics

### User Experience
- Web-based interface for gameplay and interaction
- Menu, tutorial, and HUD components for player guidance

## Technology Stack

| Area | Technology |
|------|------------|
| Backend | Python, Flask |
| API | Flask-CORS, JSON endpoints |
| Database | SQLite-based persistence |
| Frontend | React, Create React App |
| Package Management | pip, npm |

## Testing

The backend includes test files for application and database behavior. To run the test suite:

```bash
python -m pytest
```

## Contributing

Contributions are welcome. Please coordinate with the team members listed above and keep the backend/frontend separation consistent while making changes.

## License

License details are still being finalized for this project.
