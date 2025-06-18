import { useState } from "react";
import { StyleSheet, Text, View, Button, Image } from "react-native";
import { StatusBar } from "expo-status-bar";

import EnterNumberView from "./components/EnterNumberView";
import GameImage from "./components/GameImage";

export default function App() {
  const [sessionsPlayed, setSessionsPlayed] = useState(0);
  const [wonGames, setWonGames] = useState(0);
  const [cancelledGames, setCancelledGames] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  function handleWonGame() {
    setWonGames((current) => current + 1);
  }

  function handleCancelGame() {
    setCancelledGames((current) => current + 1);
    setIsModalOpen(false);
  }

  function playGame() {
    setSessionsPlayed((current) => current + 1);
    setIsModalOpen(true);
  }

  return (
    <View style={styles.appContainer}>
      <StatusBar style="light" />
      <Text style={styles.textHeader}>Angelina's Guessing Game</Text>
      <GameImage source={require("./assets/images/playful-mage.png")} />

      <View style={styles.mainMenu}>
        <Button title="Play Game" onPress={playGame} />
        <EnterNumberView
          isVisible={isModalOpen}
          onCancelGame={handleCancelGame}
          onGameWon={handleWonGame}
        />
        <View style={styles.stats}>
          <Text style={styles.statText}>Sessions Played: {sessionsPlayed}</Text>
          <Text style={styles.statText}>Won Games: {wonGames}</Text>
          <Text style={styles.statText}>Cancelled Games: {cancelledGames}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  appContainer: {
    flex: 1,
    backgroundColor: "#121212",
    alignItems: "center",
    justifyContent: "center",
  },
  mainMenu: {
    marginTop: 10,
  },
  textHeader: {
    fontSize: 26,
    color: "#fff",
  },
  stats: {
    marginTop: 10,
    gap: 10,
    alignItems: "center",
  },
  statText: {
    color: "#fff",
  },
});
