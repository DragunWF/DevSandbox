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
  },
});

export default GuessCard;
