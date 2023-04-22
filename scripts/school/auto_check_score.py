from rich import print

CORRECT_ANSWERS = """
1. C
2. D
3. C
4. D
5. C
6. B
7. A
8. C
9. B
10. B
11. D
12. B
13. A
14. A
15. C
16. C
17. B
18. C
19. C
20. A
21. C
22. A
23. A
24. A
25. C
26. B
27. C
28. bonus
29. C
30. B
"""
MY_ANSWERS = """
1. C
2. D
3. C
4. D
5. D
6. A
7. A
8. C
9. B
10. B
11. D
12. C
13. A
14. A
15. A
16. C
17. C
18. C
19. B
20. A
21. A
22. C
23. C
24. C
25. C
26. C
27. A
28. A
29. D
30. A
"""


def main():
    score = 0
    my_answers, correct_answers = convert(MY_ANSWERS), convert(CORRECT_ANSWERS)

    for i in range(len(correct_answers)):
        correct = get_answer(correct_answers[i])
        if correct == "bonus":
            score += 1
            continue
        if get_answer(my_answers[i]) == correct:
            score += 1
        else:
            print(f"{i}: {correct}")

    print(f"{score}/{len(correct_answers)}")


def convert(value: str):
    return value.strip().split("\n")


def get_answer(value: str):
    return value.split(".")[1].strip()


if __name__ == '__main__':
    main()
