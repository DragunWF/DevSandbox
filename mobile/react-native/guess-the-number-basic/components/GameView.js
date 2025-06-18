import { useState } from "react";
import { Modal, StyleSheet, View, Button, Text } from "react-native";

function GameView({ isVisible, onCancelGame, onGameWon, onGameLost }) {
  const [opponentGuesses, setOpponentGuesses] = useState([]);

  return (
    <Modal visible={isVisible} animationType="slide">
      <View style={styles.gameContainer}>
        <Text style={styles.textHeader}>Opponent's Guess</Text>
        <View style={styles.opponentGuessContainer}>
          <Text style={styles.opponentGuessText}>38</Text>
        </View>
        <View style={styles.gameButtonsContainer}>
          <Button title="Higher" />
          <Button title="Lower" />
        </View>
        <Button title="Cancel Game" onPress={onCancelGame} />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  gameContainer: {
    flex: 1,
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#090040",
  },
  opponentGuessContainer: {
    backgroundColor: "#471396",
    padding: 30,
    margin: 20,
    width: "80%",
    alignItems: "center",
    borderRadius: 100,
  },
  opponentGuessText: {
    color: "#fff",
    fontSize: 50,
  },
  textHeader: {
    color: "#fff",
    fontSize: 24,
  },
  gameButtonsContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
  },
});

export default GameView;
