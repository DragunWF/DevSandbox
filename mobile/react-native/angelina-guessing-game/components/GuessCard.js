import { Modal, StyleSheet, View, Button, Text } from "react-native";

function GuessCard({ order, guess }) {
  return (
    <View style={styles.cardContainer}>
      <Text>
        {order}. {guess}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: "#fff",
    padding: 15,
    margin: 10,
    width: 150,
    borderRadius: 15,
  },
});

export default GuessCard;
