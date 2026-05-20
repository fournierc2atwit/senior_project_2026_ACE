# senior_project_2026_ACE

# A.C.E. — AI Casino Education

A.C.E is an AI-assisted Blackjack training game that helps users learn Blackjack strategy,  probability, and decision-making in a low-risk interactive environment. Players will engage in fully playable games of Blackjack while receiving real-time AI-driven strategies that change depending on the user’s current hand and the dealer’s cards. The core educational feature is the AI-driven strategy engine, which suggests the most statistically optimal move for every possible hand combination. After each move, if a less than optimal one is made by the user, the AI will explain why the move was not optimal, which promotes learning through feedback. Player statistics, such as a win/loss record, and session history will be stored in a local database, which can then be accessed by users to track their progress.

# Team Members

- Colby Fournier - Game Logic Developer and UI Designer
- Cisco Harbeck - Game Logic Developer and Backend/Database Lead
- Reymond Sanchez - Game Logic Developer and AI Systems Lead

# Requirements
- Python 3.8 or higher
- Node.js 14+ and npm (for frontend)
- pip

# Installation

1. Clone the repository
   ```bash
   git clone https://github.com/fournierc2atwit/senior_project_2026_ACE
   cd senior_project_2026_ACE
   ```

2. Set up backend (Python/Flask)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on Mac/Linux
   source venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   ```

3. Set up frontend (React)
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. Run the application
   ```bash
   # Start backend (from project root)
   python backend/app.py
   
   # In another terminal, start frontend
   cd frontend
   npm start
   ```

The application will be available at `http://localhost:3000`

# Project Structure

```
senior_project_2026_ACE/
├── backend/
│   ├── app.py                    # Flask API server and routes
│   ├── requirements.txt          # Python dependencies
│   ├── game/                     # Core game logic
│   │   ├── __init__.py
│   │   ├── card.py              # Card class and operations
│   │   ├── deck.py              # Deck management and card dealing
│   │   ├── hand.py              # Hand evaluation and game logic
│   │   ├── player.py            # Player state and chip management
│   │   └── rules.py             # Casino rules (dealer logic, win determination)
│   ├── ai/                       # AI Strategy Engine
│   │   ├── __init__.py
│   │   ├── strategy.py          # Basic strategy lookup table and recommendations
│   │   └── advise.py            # AI reasoning and explanation generation
│   └── database/                # Data persistence layer
│       ├── __init__.py
│       ├── db.py                # SQLite database initialization and connection
│       └── stats.py             # Player statistics and session tracking
│
├── frontend/
│   ├── public/                  # Static assets
│   ├── src/
│   │   ├── index.js            # React entry point
│   │   ├── App.jsx             # Main application component and routing
│   │   ├── components/         # Reusable React components
│   │   │   ├── Table.jsx       # Game table visualization
│   │   │   ├── Hand.jsx        # Hand display (player and dealer)
│   │   │   ├── Card.jsx        # Individual card component
│   │   │   ├── Menu.jsx        # Main menu and game mode selection
│   │   │   ├── Hud.jsx         # Heads-up display (chips, bet, stats)
│   │   │   └── Tutorial.jsx    # Interactive tutorial mode
│   │   └── [styling TBD]       # CSS/CSS-in-JS (to be finalized)
│   ├── package.json            # npm dependencies
│   └── .gitignore
│
├── assets/
│   ├── cards/                  # Card images and sprites
│   └── ui/                     # UI graphics and icons
│
├── docs/
│   ├── Project Proposal.pdf
│   └── Project Plan.pdf
│
├── README.md
└── .gitignore

```

# Features

## Core Gameplay
- Full Blackjack gameplay loop (deal, hit, stand, double down)
- Dealer AI following standard casino rules
- Virtual chip and bankroll system
- Hand management with bust/blackjack detection

## AI & Learning
- Real-time basic strategy hint engine
- Post-round recap with optimal play explanation
- Educational feedback when suboptimal moves are made
- Statistically optimal move recommendations for every hand scenario

## Player Experience
- Web-based React UI (currently in development)
- Guided tutorial mode for new players
- Help and glossary screen
- Responsive game table visualization

## Data & Statistics
- SQLite stat tracking (hands played, win rate, net chip balance)
- Session history storage and retrieval
- Player progress tracking across multiple sessions

# Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python | 3.8+ |
| API Server | Flask | 3.0.3 |
| CORS Support | Flask-CORS | 4.0.1 |
| Database | SQLite | Built-in |
| Frontend | React | Latest |
| Build Tool | Create React App or Vite | TBD |

# Development Status

- ✅ Game Logic: Complete (core blackjack rules, dealer AI, hand evaluation)
- ✅ AI Strategy: Complete (basic strategy lookup table)
- ✅ Database: Schema designed, stats tracking ready
- ⚠️ Flask API: Partial (endpoints in progress)
- ⚠️ React Frontend: Scaffolded (components exist, integration ongoing)
- 🚧 Post-Move Feedback UI: In progress
- 🚧 Statistics Dashboard: In progress

# Project Timeline

**MVP Deadline:** June 10, 2026
- Phase 1 (May 20 - June 10): Core functionality and playable game
- Phase 2 (June 10 - June 30): Features and polish
- Phase 3 (June 30 - July 15): Testing and documentation

For detailed design information, see [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md)

# Contributing

See team members section above. For development guidelines, refer to code comments and the design document.

# License

[To be determined]
