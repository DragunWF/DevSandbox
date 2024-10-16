from rich import print

# Just prediction, grades not complete yet
# I just needed to find out what the bare minimum grade is to not drop below 1.30
# Below 1.30 is not Magna Cum Laude anymore


def current_term() -> float:
    # Prediction of final GWA
    app_dev = 1.25
    event_driv = 1
    sia = 1.25
    prof_issues = 1.5
    enterprise = 1.5
    db = 1.5
    data_digital_com = 1.25
    return average([app_dev, event_driv, sia, prof_issues, enterprise, db, data_digital_com])


def overall() -> list[float]:
    first = 1.32
    second = 1.12
    third = 1.16
    fourth = 1.34
    return [first, second, third, fourth]


def average(grades: list[float]) -> float:
    return round(sum(grades) / len(grades), 2)


def main():
    current = current_term()
    all_sems = overall()
    print(f"Current Term: {current}")
    print(f"Overall: {average(overall())}")
    all_sems.append(current)
    print(f"Overall with current term: {average(all_sems)}")

    # Bare minimum if you don't want to drop below Magna Cum Laude
    all_sems.append(1.44)
    all_sems.append(1.43)
    print(f"Graduation prediction: {average(all_sems)}")


if __name__ == "__main__":
    main()
