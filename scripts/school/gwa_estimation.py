from rich import print

# Just prediction, grades not complete yet
# I just needed to find out what the bare minimum grade is to not drop below 1.30
# Below 1.30 (Cumulative GWA - All Semesters) is not Magna Cum Laude anymore


def current_term() -> float:
    # Prediction of final GWA
    app_dev = 1
    event_driv = 1
    sia = 1.25
    prof_issues = 1.5
    enterprise = 1.5
    db = 1.75
    data_digital_com = 1.25
    return average([app_dev, event_driv, sia, prof_issues, enterprise, db, data_digital_com])


def overall() -> list[float]:
    first_semester = 1.32
    second_semester = 1.12
    third_semester = 1.16
    fourth_semester = 1.34
    return [first_semester, second_semester, third_semester, fourth_semester]


def average(grades: list[float]) -> float:
    return round(sum(grades) / len(grades), 2)


def main():
    # Current Term Predictions
    current_semester = current_term()
    all_semesters = overall()
    print(f"Current Term GWA: {current_semester}")
    print(f"Current Cumulative GWA: {average(all_semesters)}")
    all_semesters.append(current_semester)
    print(f"Cumulative GWA with Current Term: {average(all_semesters)}")

    # Future Term Predictions
    # Bare minimum if you don't want to drop below Magna Cum Laude
    all_semesters.append(1.44)  # Don't drop below 1.44 in 3rd Year 2nd Sem
    all_semesters.append(1.43)  # Don't drop below 1.43 in 4th Year 1st Sem
    print(f"Graduation Prediction: {average(all_semesters)}")


if __name__ == "__main__":
    main()
