import {
  StyleSheet,
  Text,
  View,
  Pressable,
  TouchableWithoutFeedbackBase,
} from "react-native";

function GoalItem({ itemData, onDeleteItem, id }) {
  return (
    <Pressable
      style={({ pressed }) => pressed && styles.pressedItem}
      onPress={onDeleteItem.bind(this, id)}
    >
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
    margin: 3,
  },
  pressedItem: {
    opacity: 0.5,
  },
  goalText: {
    color: "black",
    padding: 15,
  },
});
