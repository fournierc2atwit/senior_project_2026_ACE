import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
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
  const [musicEnabled, setMusicEnabled] = useState(true);

  const audioContextRef = useRef(null);
  const masterGainRef = useRef(null);
  const activeNodesRef = useRef([]);
  const intervalRef = useRef(null);

  const defaultMusicPath = process.env.PUBLIC_URL + "/mfcc-jazz-music-casino-poker-roulette-las-vegas-background-intro-theme-287498.mp3";
  const soundUrl = defaultMusicPath;
  const customAudioRef = useRef(null);

  const navigate = useCallback((destination, game) => {
    if (destination === "game" && game) {
      setSelectedGame(game);
    }
    setScreen(destination);
  }, []);

  const stopAmbientMusic = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    activeNodesRef.current.forEach(({ osc, gain, filter, vibratoOsc, vibratoGain }) => {
      try { vibratoOsc?.stop(); } catch {}
      try { vibratoGain?.disconnect(); } catch {}
      try { osc?.stop(); } catch {}
      try { filter?.disconnect(); } catch {}
      try { gain?.disconnect(); } catch {}
    });
    activeNodesRef.current = [];
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch {}
      audioContextRef.current = null;
    }
    if (customAudioRef.current) {
      try { customAudioRef.current.pause(); } catch {}
      try { customAudioRef.current.src = ""; } catch {}
      customAudioRef.current = null;
    }
    masterGainRef.current = null;
  }, []);

  const startAmbientMusic = useCallback(async () => {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContextClass();
      masterGainRef.current = audioContextRef.current.createGain();
      masterGainRef.current.gain.value = 0.45;
      masterGainRef.current.connect(audioContextRef.current.destination);
    }

    const ctx = audioContextRef.current;
    if (ctx.state === "suspended") {
      await ctx.resume();
    }

    if (masterGainRef.current) {
      masterGainRef.current.gain.setValueAtTime(0.45, ctx.currentTime);
    }

    const master = masterGainRef.current;
    const notes = [261.63, 293.66, 329.63, 392, 349.23, 329.63, 293.66, 261.63];
    const harmonyNotes = [392, 493.88, 587.33, 523.25];
    let step = 0;

    // Use bundled audio file if available, otherwise fall back to the synth
    if (soundUrl) {
      try {
        if (!customAudioRef.current) {
          const audioEl = new Audio(soundUrl);
          audioEl.loop = true;
          audioEl.crossOrigin = "anonymous";
          customAudioRef.current = audioEl;
          try { await audioEl.play(); } catch {}
          try {
            const src = ctx.createMediaElementSource(audioEl);
            src.connect(master);
          } catch {}
        } else {
          try { await customAudioRef.current.play(); } catch {}
        }
        return;
      } catch (e) {
        console.warn("Bundled audio failed, falling back to synth:", e);
      }
    }

    const playStep = () => {
      const now = ctx.currentTime;
      const note = notes[step % notes.length];
      const harmony = harmonyNotes[(step + 1) % harmonyNotes.length];
      step += 1;

      const mainOsc = ctx.createOscillator();
      const mainGain = ctx.createGain();
      const mainFilter = ctx.createBiquadFilter();
      const vibratoOsc = ctx.createOscillator();
      const vibratoGain = ctx.createGain();

      mainOsc.type = "sawtooth";
      mainOsc.frequency.setValueAtTime(note, now);
      mainFilter.type = "lowpass";
      mainFilter.frequency.setValueAtTime(1500, now);
      mainFilter.Q.value = 0.65;

      vibratoOsc.type = "sine";
      vibratoOsc.frequency.setValueAtTime(4.5, now);
      vibratoGain.gain.setValueAtTime(5, now);
      vibratoOsc.connect(vibratoGain);
      vibratoGain.connect(mainOsc.frequency);

      mainGain.gain.setValueAtTime(0.0001, now);
      mainGain.gain.exponentialRampToValueAtTime(0.055, now + 0.02);
      mainGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.62);

      mainOsc.connect(mainFilter);
      mainFilter.connect(mainGain);
      mainGain.connect(master);

      mainOsc.start(now);
      vibratoOsc.start(now);
      mainOsc.stop(now + 0.62);
      vibratoOsc.stop(now + 0.62);
      activeNodesRef.current.push({ osc: mainOsc, gain: mainGain, filter: mainFilter, vibratoOsc, vibratoGain });

      const harmonyOsc = ctx.createOscillator();
      const harmonyGain = ctx.createGain();
      harmonyOsc.type = "triangle";
      harmonyOsc.frequency.setValueAtTime(harmony, now);
      harmonyGain.gain.setValueAtTime(0.0001, now);
      harmonyGain.gain.exponentialRampToValueAtTime(0.022, now + 0.02);
      harmonyGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.5);
      harmonyOsc.connect(harmonyGain);
      harmonyGain.connect(master);
      harmonyOsc.start(now);
      harmonyOsc.stop(now + 0.5);
      activeNodesRef.current.push({ osc: harmonyOsc, gain: harmonyGain });
    };

    activeNodesRef.current.forEach(({ osc, gain, filter, vibratoOsc, vibratoGain }) => {
      try { vibratoOsc?.stop(); } catch {}
      try { vibratoGain?.disconnect(); } catch {}
      try { osc?.stop(); } catch {}
      try { filter?.disconnect(); } catch {}
      try { gain?.disconnect(); } catch {}
    });
    activeNodesRef.current = [];

    playStep();
    intervalRef.current = window.setInterval(playStep, 850);
  }, [soundUrl]);

  useEffect(() => {
    const onNameEntryScreen = screen === "menu" && playerChips === null;
    if (onNameEntryScreen) {
      stopAmbientMusic();
      return;
    }

    if (musicEnabled) {
      startAmbientMusic().catch(() => {});
    }
  }, [screen, musicEnabled, playerChips, startAmbientMusic, stopAmbientMusic]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      activeNodesRef.current.forEach(({ osc, gain }) => {
        try { osc?.stop(); } catch {}
        try { gain?.disconnect(); } catch {}
      });
      activeNodesRef.current = [];
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      if (customAudioRef.current) {
        try { customAudioRef.current.pause(); } catch {}
        try { customAudioRef.current.src = ""; } catch {}
        customAudioRef.current = null;
      }
      masterGainRef.current = null;
    };
  }, []);

  const toggleMusic = async () => {
    if (musicEnabled) {
      stopAmbientMusic();
      setMusicEnabled(false);
      return;
    }

    // When on the menu/name entry screen, enable the flag but don't start playback yet.
    if (screen === "menu") {
      setMusicEnabled(true);
      return;
    }

    try {
      await startAmbientMusic();
      setMusicEnabled(true);
    } catch {
      setMusicEnabled(false);
    }
  };

  const showMusicButton = screen !== "menu" || playerChips !== null;

  return (
    <div className="app-shell">
      {showMusicButton && (
        <button className={`app-music-toggle ${musicEnabled ? "is-on" : ""}`} onClick={toggleMusic} type="button">
          <span className="music-icon">♫</span>
          <span>{musicEnabled ? "Mute" : "Unmute"}</span>
        </button>
      )}
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
  <SlotsTable
    onNavigate={navigate}
    playerName={playerName}
    initialChips={playerChips}
    onSetChips={setPlayerChips}
  />
)}
      {screen === "stats"    && <Stats    onNavigate={navigate} playerName={playerName} />}
      {screen === "tutorial" && <Tutorial onNavigate={navigate} />}
    </div>
  );
}