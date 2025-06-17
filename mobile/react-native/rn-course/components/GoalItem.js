import { StyleSheet } from "react-native";
import { StyleSheet, Text, View } from "react-native";

function GoalItem({ goalItem: itemData }) {
  return (
    <View style={styles.goalItem}>
      <Text style={styles.goalText}>
        {itemData.index + 1}. {itemData.item.text}
      </Text>
    </View>
  );
}

export default GoalItem;

const styles = StyleSheet.create({
  goalItem: {
    borderRadius: 10,
    backgroundColor: "#bfd4f5",
    padding: 15,
    margin: 3,
  },
  goalText: {
    color: "black",
  },
});
