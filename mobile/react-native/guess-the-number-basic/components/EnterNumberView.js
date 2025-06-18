import { useState } from "react";
import { StyleSheet, View, Modal, TextInput } from "react-native";
import GameView from "./GameView";

function EnterNumberView({ isVisible, onGameWon, onCancelGame }) {
  const [enteredNumber, setEnteredNumber] = useState(null);
  const [isGameOpen, setIsGameOpen] = useState(false);

  function numberInputHandler() {}

  return (
    <Modal visible={isVisible} animationType="fade">
      <View styles={styles.viewContainer}>
        <TextInput
          style={styles.textInput}
          placeholder="Your secret number!"
          onChangeText={numberInputHandler}
          value={enteredNumber}
        />
        <GameView
          isVisible={isGameOpen}
          onGameWon={onGameWon}
          onCancelGame={onCancelGame}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    flex: 1,
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#393E46",
  },
  textInput: {},
});

export default EnterNumberView;
