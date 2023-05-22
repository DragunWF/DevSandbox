from rich import print

CORRECT_ANSWERS = """
1. D
2. C
3. C
4. C
5. D
6. C
7. B
8. C
9. A
10. D
11. A
12. B
13. C
14. A
15. D
16. C
17. B
18. C
19. D
20. C
21. A
22. B
23. B
24. B
25. C
26. A
27. C
28. B
29. C
30. C
"""
MY_ANSWERS = """
1. D
2. C
3. B
4. B
5. D
6. C
7. B
8. C
9. A
10. D
11. B
12. B
13. C
14. A
15. D
16. B
17. C
18. C
19. D
20. C
21. D
22. B
23. C
24. C
25. C
26. C
27. C
28. C
29. C
30. B
"""


def main():
    print()
    score = 0
    my_answers, correct_answers = convert(MY_ANSWERS), convert(CORRECT_ANSWERS)

    for i in range(len(correct_answers)):
        correct = get_answer(correct_answers[i])
        answer = get_answer(my_answers[i])
        is_correct = answer == correct or correct == "bonus"

        print(f"{i + 1}. {answer} - {is_correct}", end="")
        if is_correct:
            score += 1
        else:
            print(f" = {correct}", end="")
        print()

    print(f"\nScore: {score}/{len(correct_answers)}")


def convert(value: str) -> str:
    return value.strip().split("\n")


def get_answer(value: str) -> str:
    return value.split(".")[1].strip()


if __name__ == '__main__':
    main()
