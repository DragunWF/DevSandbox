import { useState } from "react";
import { StyleSheet, Text, View, Button, Image } from "react-native";
import { StatusBar } from "expo-status-bar";

import GameView from "./components/GameView";

export default function App() {
  const [sessionsPlayed, setSessionsPlayed] = useState(0);
  const [wonGames, setWonGames] = useState(0);
  const [lostGames, setLostGames] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  function handleWonGame() {
    setWonGames((current) => current + 1);
  }

  function handleLostGame() {
    setLostGames((current) => current + 1);
  }

  function handleCancelGame() {
    setIsModalOpen(false);
  }

  function playGame() {
    setSessionsPlayed((current) => current + 1);
    setIsModalOpen(true);
  }

  return (
    <View style={styles.appContainer}>
      <StatusBar style="auto" />
      <Text style={styles.textHeader}>Angelina's Roulette Game</Text>
      <Image
        style={styles.welcomeImage}
        source={require("./assets/images/playful-mage.png")}
      />

      <View style={styles.mainMenu}>
        <Button title="Play Game" onPress={playGame} />
        <GameView
          isVisible={isModalOpen}
          onCancelGame={handleCancelGame}
          onGameWon={handleWonGame}
          onGameLost={handleLostGame}
        />
        <View style={styles.stats}>
          <Text style={styles.statText}>Sessions Played: {sessionsPlayed}</Text>
          <Text style={styles.statText}>Won Games: {wonGames}</Text>
          <Text style={styles.statText}>Lost Games: {lostGames}</Text>
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
  welcomeImage: {
    width: 200,
    height: 200,
    marginTop: 20,
    marginBottom: 5,
    borderRadius: 15,
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
