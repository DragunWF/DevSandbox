import { StyleSheet, Text, View, Pressable } from "react-native";

function GoalItem({ itemData, onDeleteItem }) {
  return (
    <Pressable onPress={onDeleteItem}>
      <View style={styles.goalItem}>
        <Text style={styles.goalText}>
          {itemData.index + 1}. {itemData.item.text}
        </Text>
      </View>
    </Pressable>
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
