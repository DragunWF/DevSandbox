from rich import print

# Removing the spaces from those pasted numbers takes too much time so I decided to just
# make a function that removes those spaces and converts it to a number just in case if anyone
# is wondering why I made this function.
def convert(value):
    return int("".join(value.split(" ")))


def calculate(accounts, year, financial_position):
    factors = {
        "2012": {
            "total_assets": convert("17 229 224"),
            "net_sales": convert("42 174 283")
        },
        "2013": {
            "total_assets": convert("20 628 128"),
            "net_sales": convert("47 345 223")
        }}
    divisor = "total_assets" if financial_position else "net_sales"
    return f"{round((accounts / factors[year][divisor]) * 100)}%"


def get_account_sets():
    # accounts_2012 = (
    #     {"net_sales": "42 174 283", "is_financial_position": False},
    #     {"cost_of_sales": "33 980 174", "is_financial_position": False},
    #     {"gross_profit": "8 194 109", "is_financial_position": False},
    #     {"operating_expenses": "5 393 621", "is_financial_position": False},
    #     {"operating_income": "2 800 488", "is_financial_position": False},
    #     {"interest_expense": "250 000", "is_financial_position": False},
    #     {"income_before_taxes": "2 550 488", "is_financial_position": False},
    #     {"taxes": "765 146", "is_financial_position": False},
    #     {"net_income": "1 785 342", "is_financial_position": False},
    # )
    # accounts_2013 = (
    #     {"net_sales": "47 345 223", "is_financial_position": False},
    #     {"cost_of_sales": "37 988 628", "is_financial_position": False},
    #     {"gross_profit": "9 356 595", "is_financial_position": False},
    #     {"operating_expenses": "6 196 804", "is_financial_position": False},
    #     {"operating_income": "3 159 791", "is_financial_position": False},
    #     {"interest_expense": "250 000", "is_financial_position": False},
    #     {"income_before_taxes": "2 909 791", "is_financial_position": False},
    #     {"taxes": "872 937", "is_financial_position": False},
    #     {"net_income": "2 036 854", "is_financial_position": False},
    # )
    accounts_2012 = (
        {"cash": "777 415", "is_financial_position": True},
        {"trade_receivables": "1 722 513", "is_financial_position": True},
        {"inventories": "8 194 109", "is_financial_position": True},
        {"other_current_assets": "984 786", "is_financial_position": True},
        {"total_current_assets": "7 282 382", "is_financial_position": True},
        {"other_non_current_assets": "896 842", "is_financial_position": True},
        {"total_non_current_assets": "9 946 842", "is_financial_position": True},
        {"total_assets": "17 229 224", "is_financial_position": True},
        {"trade_payables": "4 137 815", "is_financial_position": True},
        {"income_tax_payables": "267 801", "is_financial_position": True},
        {"current_portion_or_long_term_debt": "1 000 000",
            "is_financial_position": True},
        {"total_liabilities": "5 446 606", "is_financial_position": True},
        {"stockholder's_equity": "0", "is_financial_position": True},
        {"capital_stock": "8 000 000", "is_financial_position": True},
        {"retained_earnings": "3 782 618", "is_financial_position": True},
        {"total_stockholder's_equity": "11 782 618", "is_financial_position": True},
        {"total_liabilities_and_stockholder's_equity": "17 229 224",
            "is_financial_position": True},
    )
    accounts_2013 = (
        {"cash": "996 904", "is_financial_position": True},
        {"trade_receivables": "1 921 799", "is_financial_position": True},
        {"inventories": "4 499 998", "is_financial_position": True},
        {"other_current_assets": "983 746", "is_financial_position": True},
        {"total_current_assets": "8 402 447", "is_financial_position": True},
        {"other_non_current_assets": "925 681", "is_financial_position": True},
        {"total_non_current_assets": "12 225 681", "is_financial_position": True},
        {"total_assets": "20 628 128", "is_financial_position": True},
        {"trade_payables": "4 746 252", "is_financial_position": True},
        {"income_tax_payables": "283 705", "is_financial_position": True},
        {"current_portion_or_long_term_debt": "2 500 000",
            "is_financial_position": True},
        {"total_liabilities": "8 808 657", "is_financial_position": True},
        {"stockholder's_equity": "0", "is_financial_position": True},
        {"capital_stock": "8 000 000", "is_financial_position": True},
        {"retained_earnings": "3 819 472", "is_financial_position": True},
        {"total_stockholder's_equity": "11 819 472", "is_financial_position": True},
        {"total_liabilities_and_stockholder's_equity": "20 628 128",
            "is_financial_position": True},
    )
    return accounts_2012, accounts_2013


def automate_calculations():
    account_sets = get_account_sets()
    string_2012, string_2013 = "2012:\n", "2013:\n"
    for i in range(len(account_sets)):
        year = "2012" if i == 1 else "2013"
        for account in account_sets[i - 1]:
            account_name = [x for x in account][0]
            displayed_name = " ".join([a.capitalize()
                                      for a in account_name.split("_")])
            accounts_value = convert(account[account_name])
            result = f'{calculate(accounts_value, year, account["is_financial_position"])}'
            if year == "2012":
                string_2012 += f"{displayed_name}: {result}\n"
            else:
                string_2013 += f"{displayed_name}: {result}\n"
    return f"{string_2012}\n{string_2013}"


print(automate_calculations())
