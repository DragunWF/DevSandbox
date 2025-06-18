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
import { StatusBar } from "expo-status-bar";
import GoalItem from "./components/GoalItem";
import GoalInput from "./components/GoalInput";

export default function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [courseGoals, setCourseGoals] = useState([]);

  function startAddGoalHandler() {
    setIsModalOpen(true);
  }

  function endAddGoalHandler() {
    setIsModalOpen(false);
  }

  function addGoalHandler(enteredGoalText) {
    setCourseGoals((currentCourseGoals) => [
      ...currentCourseGoals,
      { text: enteredGoalText, id: Math.random().toString() },
    ]);
    endAddGoalHandler();
  }

  function deleteGoalHandler(id) {
    setCourseGoals((currentCourseGoals) => {
      return currentCourseGoals.filter((goal) => goal.id !== id);
    });
  }

  return (
    <>
      <StatusBar style="light" />
      <View style={styles.appContainer}>
        <Text style={styles.textHeader}>Goals App</Text>
        <View style={styles.addGoalButton}>
          <Button
            title="Add New Goal"
            color="#bfd4f5"
            onPress={startAddGoalHandler}
          />
        </View>
        <GoalInput
          onAddGoal={addGoalHandler}
          isVisible={isModalOpen}
          onCancel={endAddGoalHandler}
        />
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
    </>
  );
}

const styles = StyleSheet.create({
  appContainer: {
    flex: 1,
    paddingTop: 50,
    paddingHorizontal: 16,
    backgroundColor: "#1e085a",
  },
  textHeader: {
    color: "#fff",
    marginTop: 20,
    textAlign: "center",
    fontSize: 28,
    borderBottomColor: "black",
    border: 1,
  },
  goalsContainer: {
    flex: 5,
  },
  addGoalButton: {
    marginTop: 5,
  },
});
