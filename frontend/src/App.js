import { useState } from "react";
import Menu from "./components/Menu";
import Table from "./components/Table";
import Stats from "./components/Stats";
import Tutorial from "./components/Tutorial";

export default function App() {
  const [screen, setScreen]         = useState("menu");
  const [playerName, setPlayerName] = useState("Player");

  const navigate = (destination) => setScreen(destination);

  return (
    <div>
      {screen === "menu"     && <Menu     onNavigate={navigate} onSetName={setPlayerName} />}
      {screen === "game"     && <Table    onNavigate={navigate} playerName={playerName} />}
      {screen === "stats"    && <Stats    onNavigate={navigate} />}
      {screen === "tutorial" && <Tutorial onNavigate={navigate} />}
    </div>
  );
}