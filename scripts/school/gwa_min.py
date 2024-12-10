from rich import print

class Subject:
    def __init__(self, name: str, grades: list[int], target_key: str):
        self.name = name
        self.grades = grades
        self.target_key = target_key


gwa_standings = {
    "1.00": 97.5,
    "1.25": 94.5,
    "1.50": 91.5,
    "1.75": 88.5
}


def print_min_required(subject: str, grades: list[int], target_key: str) -> None:
    if any([grade > 100 or grade < 0 for grade in grades]) or len(grades) != 3:
        print(f"Invalid grade input for {subject}")
        return
    if not target_key in gwa_standings:
        print(f"Invalid target key for {subject}")
        return

    min_grade = 100 # Base value (Will get subtracted)
    get_avg = lambda finals_grade: (sum(grades) + finals_grade * 2) / 5
    threshold_grade = gwa_standings[target_key]
    average = get_avg(min_grade)

    if average < threshold_grade:
        print(f"{subject} (Target GWA: {target_key}): Can't be reached")
        return
    
    while average > threshold_grade:
        min_grade -= 0.1
        average = get_avg(min_grade)
    min_grade += 0.1
    
    print(f"{subject}:")
    print(f"Target GWA: {target_key}")
    print(f"Min Grade Required: {round(min_grade, 2)}\n")


def print_avg_gwa(subjects: list[Subject]) -> None:
    total = sum(float(subject.target_key) for subject in subjects)
    print(f"Average GWA: {round(total / len(subjects), 2)}\n")


def print_wall(is_start: bool) -> None:
    wall = "=" * 50
    if is_start:
        print(f"\n{wall}\n\n")
    else:
        print(f"\n{wall}\n")


def main() -> None:
    subjects: Subject = [
        Subject("Data & Digital Communications", [99, 91, 99], "1.25"),
        Subject("Event-Driven Programming", [100, 100, 100], "1.00"),
        Subject("Advanced Database Systems", [91.37, 89.2, 97.41], "1.50"),
        Subject("Application Development & Emerging Technologies", [97.5, 98.5, 100], "1.00"),
        Subject("Advanced Systems Integration & Maintenance", [98, 94.5, 93], "1.25"),
        Subject("Enterprise Architecture", [88.95, 97.5, 98.2], "1.25"),
        Subject("Professional Issues in Information Systems and Technology", [93.79, 94.25, 97], "1.25")
    ]
    print_wall(True)

    print("Don't drop below these grades to get your desired GWA:\n")
    for subject in subjects:
        print_min_required(subject.name, subject.grades, subject.target_key)
    print_avg_gwa(subjects)

    print_wall(False)


if __name__ == "__main__":
    main()
