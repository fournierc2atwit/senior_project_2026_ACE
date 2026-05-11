# senior_project_2026_ACE

# A.C.E. — AI Casino Education

A.C.E is an AI-assisted Blackjack training game that helps users learn Blackjack strategy,  probability, and decision-making in a low-risk interactive environment. Players will engage in fully playable games of Blackjack while receiving real-time AI-driven strategies that change depending on the user’s current hand and the dealer’s cards. The core educational feature is the AI-driven strategy engine, which suggests the most statistically optimal move for every possible hand combination. After each move, if a less than optimal one is made by the user, the AI will explain why the move was not optimal, which promotes learning through feedback. Player statistics, such as a win/loss record, and session history will be stored in a local database, which can then be accessed by users to track their progress.

# Team Members

Colby Fournier - Game Logic Developer and UI Designer
Cisco Harbeck - Game Logic Developer and Backend/Database Lead
Reymond Sanchez - Game Logic Developer and AI Systems Lead

# Requirements
    - Python 3.8 or higher
    - pip 

# Installation

1. Clone the repository
    - git clone https://github.com/fournierc2atwit/senior_project_2026_ACE

2. Create a virtual environment
    - python -m venv venv

    # Activate on Windows
    - venv\Scripts\activate

    # Activate on Mac/Linux
    - source venv/bin/activate

3. Install dependencies
    - pip install -r requirements.txt

4. Run the game
    - python main.py

# Features
    - Full Blackjack gameplay loop (deal, hit, stand, double down)
    - Dealer AI following standard casino rules
    - Virtual chip and bankroll system
    - Real-time basic strategy hint engine
    - Post-round recap with optimal play explanation
    - SQLite stat tracking (hands played, win rate, net chip balance)
    - Guided tutorial mode
    - Help and glossary screen
