import { useState } from "react";
import Menu from "./components/Menu";
import Table from "./components/blackjack/Table";
import RouletteTable from "./components/roulette/RouletteTable";
import SlotsTable from "./components/slots/SlotsTable";
import Stats from "./components/Stats";
import Tutorial from "./components/Tutorial";

export default function App() {
  const [screen, setScreen]             = useState("menu");
  const [playerName, setPlayerName]     = useState("");
  const [playerChips, setPlayerChips]   = useState(null);
  const [selectedGame, setSelectedGame] = useState("blackjack");

  const navigate = (destination, game) => {
    if (destination === "game" && game) {
      setSelectedGame(game);
    }
    setScreen(destination);
  };

  return (
    <div>
      {screen === "menu" && (
        <Menu
          onNavigate={navigate}
          onSetName={setPlayerName}
          onSetChips={setPlayerChips}
          onSetGame={setSelectedGame}
          selectedGame={selectedGame}
          playerName={playerName}
          playerChips={playerChips}
        />
      )}
      {screen === "game" && selectedGame === "blackjack" && (
        <Table
          onNavigate={navigate}
          onSetChips={setPlayerChips}
          playerName={playerName}
          initialChips={playerChips}
        />
      )}
      {screen === "game" && selectedGame === "roulette" && (
        <RouletteTable
          onNavigate={navigate}
          playerName={playerName}
          initialChips={playerChips}
          onSetChips={setPlayerChips}
        />
      )}
      {screen === "game" && selectedGame === "slots" && (
        <SlotsTable onNavigate={navigate} playerName={playerName} initialChips={playerChips} />
      )}
      {screen === "stats"    && <Stats    onNavigate={navigate} playerName={playerName} />}
      {screen === "tutorial" && <Tutorial onNavigate={navigate} />}
    </div>
  );
}