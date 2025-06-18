import { useState } from "react";
import { Modal, StyleSheet, View, Button, Text } from "react-native";

function GameView({ isVisible, onCancelGame, onGameWon, onGameLost }) {
  const [opponentGuesses, setOpponentGuesses] = useState([]);

  return (
    <Modal visible={isVisible} animationType="slide">
      <View style={styles.gameContainer}>
        <Text>Opponent's Guess</Text>
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
  },
  gameButtonsContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
  },
});

export default GameView;
