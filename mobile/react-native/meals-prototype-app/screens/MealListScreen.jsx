import { StyleSheet, View, Text, FlatList } from "react-native";

import { MEALS, CATEGORIES } from "../data/dummy-data";
import Title from "../components/Title";

function MealListScreen({ categoryId }) {
  const category = CATEGORIES.filter((item) => item.id === categoryId)[0];
  const meals = MEALS.filter((item) => item.categoryIds.includes(categoryId));

  return (
    <View>
      <Title>{category.title}</Title>
      <FlatList
        data={meals}
        renderItem={(itemData) => {
          return <Text>{itemData.item.title}</Text>;
        }}
        keyExtractor={(item) => item.id}
        alwaysBounceVertical={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({});

export default MealListScreen;
