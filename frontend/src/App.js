import { useState } from "react";
import Menu from "./components/Menu";
import Table from "./components/blackjack/Table";
import Stats from "./components/Stats";
import Tutorial from "./components/Tutorial";

export default function App() {
  const [screen, setScreen]           = useState("menu");
  const [playerName, setPlayerName]   = useState("Player");
  const [playerChips, setPlayerChips] = useState(1000);

  const navigate = (destination) => setScreen(destination);

  return (
    <div>
      {screen === "menu"     && <Menu     onNavigate={navigate} onSetName={setPlayerName} onSetChips={setPlayerChips} />}
      {screen === "game"     && <Table    onNavigate={navigate} playerName={playerName} initialChips={playerChips} />}
      {screen === "stats"    && <Stats    onNavigate={navigate} playerName={playerName} />}
      {screen === "tutorial" && <Tutorial onNavigate={navigate} />}
    </div>
  );
}