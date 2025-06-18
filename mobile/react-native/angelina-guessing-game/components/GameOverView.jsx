import { StyleSheet, View, Text } from "react-native";

function GameOverView({ isVisible, guessCount }) {
  return (
    <Modal visible={isVisible}>
      <View style={styles.viewContainer}>
        <Text>Game Over!</Text>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
});

export default GameOverView;
