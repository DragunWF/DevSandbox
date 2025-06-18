import { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  Button,
  TextInput,
  ScrollView,
  FlatList,
} from "react-native";
import GoalItem from "./components/GoalItem";
import GoalInput from "./components/GoalInput";

export default function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [courseGoals, setCourseGoals] = useState([]);

  function startAddGoalHanlder() {
    setIsModalOpen(true);
  }

  function addGoalHandler(enteredGoalText) {
    setCourseGoals((currentCourseGoals) => [
      ...currentCourseGoals,
      { text: enteredGoalText, id: Math.random().toString() },
    ]);
  }

  function deleteGoalHandler(id) {
    setCourseGoals((currentCourseGoals) => {
      return currentCourseGoals.filter((goal) => goal.id !== id);
    });
  }

  return (
    <View style={styles.appContainer}>
      <Text style={styles.textHeader}>Goals App</Text>
      <Button
        title="Add New Goal"
        color="#bfd4f5"
        onPress={startAddGoalHanlder}
      />
      <GoalInput onAddGoal={addGoalHandler} isVisible={isModalOpen} />
      <View style={styles.goalsContainer}>
        <FlatList
          data={courseGoals}
          renderItem={(itemData) => {
            return (
              <GoalItem
                itemData={itemData}
                id={itemData.item.id}
                onDeleteItem={deleteGoalHandler}
              />
            );
          }}
          keyExtractor={(item, index) => {
            return item.id;
          }}
          alwaysBounceVertical={false}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  appContainer: {
    backgroundColor: "#fff",
    flex: 1,
    paddingTop: 50,
    paddingHorizontal: 16,
  },
  textHeader: {
    marginTop: 20,
    textAlign: "center",
    fontSize: 28,
    borderBottomColor: "black",
    border: 1,
  },
  goalsContainer: {
    flex: 5,
  },
});
