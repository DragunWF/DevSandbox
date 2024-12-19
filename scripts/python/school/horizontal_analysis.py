from rich import print


def convert(value: str) -> int:
    return int("".join(value.split(" ")))


def format_percentage(value: int) -> str:
    return f"{round(value)}%" if value > 0 else f"({abs(value)}%)"


def format_peso_change(value: int) -> str:
    return f"{value:,}" if value > 0 else f"({abs(value):,})"


def calculate(accounts_previous: int, accounts_current: int) -> tuple:
    peso_change = accounts_current - accounts_previous
    percentage_change = round((peso_change / accounts_previous) * 100)
    return format_peso_change(peso_change), format_percentage(percentage_change)


def get_accounts() -> tuple:
    accounts_2012 = {"financial_position": {
        "cash": "777 415",
        "trade_receivables": "1 722 513",
        "inventories": "8 194 109",
        "other_current_assets": "984 786",
        "total_current_assets": "7 282 382",
        "other_non_current_assets": "896 842",
        "total_non_current_assets": "9 946 842",
        "property_plant_and_equipment_net": "9 050 000",
        "total_assets": "17 229 224",
        "trade_payables": "4 137 815",
        "income_tax_payables": "267 801",
        "current_portion_of_long_term_debt": "1 000 000",
        "total_liabilities": "5 446 606",
        "capital_stock": "8 000 000",
        "retained_earnings": "3 782 618",
        "total_stockholder's_equity": "11 782 618",
        "total_liabilities_and_stockholder's_equity": "17 229 224"},
        "profit_or_loss": {
        "net_sales": "42 174 283",
        "cost_of_sales": "33 980 174",
        "gross_profit": "8 194 109",
        "operating_expenses": "5 393 621",
        "operating_income": "2 800 488",
        "interest_expense": "250 000",
        "income_before_taxes": "2 550 488",
        "taxes": "765 146",
        "net_income": "1 785 342"}}
    accounts_2011 = {"financial_position": {
        "cash": "766 805",
        "trade_receivables": "1 454 426",
        "inventories": "3 293 030",
        "other_current_assets": "735 608",
        "total_current_assets": "6 249 869",
        "other_non_current_assets": "876 235",
        "total_non_current_assets": "10 226 235",
        "property_plant_and_equipment_net": "9 350 000",
        "total_assets": "16 476 104",
        "trade_payables": "3 298 699",
        "income_tax_payables": "149 441",
        "current_portion_of_long_term_debt": "2 000 000",
        "total_liabilities": "6 478 828",
        "capital_stock": "8 000 000",
        "retained_earnings": "1 997 276",
        "total_stockholder's_equity": "9 997 276",
        "total_liabilities_and_stockholder's_equity": "16 476 104",
    }, "profit_or_loss": {
        "net_sales": "38 340 257",
        "cost_of_sales": "31 439 011",
        "gross_profit": "6 901 246",
        "operating_expenses": "4 926 723",
        "operating_income": "1 974 523",
        "interest_expense": "450 000",
        "income_before_taxes": "1 524 523",
        "taxes": "457 357",
        "net_income": "1 067 166",
    }}
    return accounts_2011, accounts_2012


def to_title_case(text: str) -> str:
    return " ".join(text.split("_")).title()


def automate_calculations() -> str:
    accounts_2011, accounts_2012 = get_accounts()
    statements = tuple([i for i in accounts_2012])
    output = "\n"
    for statement in statements:
        output += f'{to_title_case(statement)}\n'
        for account, amount in accounts_2012[statement].items():
            result = calculate(convert(accounts_2011[statement][account]),
                               convert(amount))
            output += f"\n{to_title_case(account)}:" + \
                f"\nPeso Change: {result[0]}\nPercentage Change: {result[1]}\n"
    return output


print(automate_calculations())
