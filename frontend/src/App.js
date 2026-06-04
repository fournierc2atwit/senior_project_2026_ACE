import { useState } from "react";
import Menu from "./components/Menu";
import Table from "./components/Table";
import Stats from "./components/Stats";
import Tutorial from "./components/Tutorial";

export default function App() {
  const [screen, setScreen] = useState("menu");

  const navigate = (destination) => setScreen(destination);

  return (
    <div>
      {screen === "menu"     && <Menu     onNavigate={navigate} />}
      {screen === "game"     && <Table    onNavigate={navigate} />}
      {screen === "stats"    && <Stats    onNavigate={navigate} />}
      {screen === "tutorial" && <Tutorial onNavigate={navigate} />}
    </div>
  );
}