public class Demo {
    public static void show() {
        var homePage = new HomePage();
        homePage.setGoal(new WeighLossPlanFactory());
        homePage.setGoal(new BuildMusclePlanFactory());
    }

    public static void main(String[] args) {
        show();
    }
}

interface MealPlan {
}

interface WorkoutPlan {
}

// Abstract Factory
interface PlannerFactory {
    public MealPlan createMealPlan();

    public WorkoutPlan createWorkoutPlan();
}

class WeighLossMealPlan implements MealPlan {
}

class WeightLossWorkout implements WorkoutPlan {
}

class BuildMuscleMealPlan implements MealPlan {
}

class BuildMuscleWorkout implements WorkoutPlan {
}

class WeighLossPlanFactory implements PlannerFactory {
    @Override
    public MealPlan createMealPlan() {
        System.out.println("Creating meal plan for weight loss");
        return new WeighLossMealPlan();
    }

    @Override
    public WorkoutPlan createWorkoutPlan() {
        System.out.println("Creating workout plan for weight loss");
        return new WeightLossWorkout();
    }
}

class BuildMusclePlanFactory implements PlannerFactory {
    @Override
    public MealPlan createMealPlan() {
        System.out.println("Creating meal plan for muscle building");
        return new BuildMuscleMealPlan();
    }

    @Override
    public WorkoutPlan createWorkoutPlan() {
        System.out.println("Creating workout plan for muscle building");
        return new BuildMuscleWorkout();
    }
}

class HomePage {
    private WorkoutPlan workoutPlan;
    private MealPlan mealPlan;

    public void setGoal(PlannerFactory factory) {
        workoutPlan = factory.createWorkoutPlan();
        mealPlan = factory.createMealPlan();
    }
}