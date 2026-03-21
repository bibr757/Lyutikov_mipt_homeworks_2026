#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

AMOUNT_KEY = "amount"
DATE_KEY = "date"
CAT_KEY = "category"

FEBRUARY = 2
MONTHS_IN_YEAR = 12
DATE_PARTS_COUNT = 3
INCOME_CMD_LEN = 3
COST_CMD_LEN = 4
STATS_CMD_LEN = 2

CAT_PARTS_LEN = 2
MAX_FLOAT_PARTS = 2
COST_CAT_CMD_LEN = 2

financial_transactions_storage: list[dict[str, Any]] = []


DateTuple = tuple[int, int, int]
StatsDict = dict[str, float]


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    is_fourth = year % 4 == 0
    is_not_hundredth = year % 100 != 0
    is_four_hundredth = year % 400 == 0
    return (is_fourth and is_not_hundredth) or is_four_hundredth


def get_days_in_month(month: int, year: int) -> int:
    if month == FEBRUARY:
        return 29 if is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def parse_valid_date(parts: list[str]) -> DateTuple | None:
    year = int(parts[2])
    month = int(parts[1])
    day = int(parts[0])

    if not (year >= 1 and 1 <= month <= MONTHS_IN_YEAR):
        return None
    if 1 <= day <= get_days_in_month(month, year):
        return day, month, year

    return None


def extract_date(maybe_dt: str) -> DateTuple | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parsed = maybe_dt.split("-")
    if len(parsed) != DATE_PARTS_COUNT:
        return None
    for part in parsed:
        if not part.isdigit():
            return None

    return parse_valid_date(parsed)


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append(
        {
            AMOUNT_KEY: amount,
            DATE_KEY: date_tuple,
        }
    )
    return OP_SUCCESS_MSG


def is_valid_category(category_name: str) -> bool:
    parts = category_name.split("::")
    if len(parts) != CAT_PARTS_LEN:
        return False
    common = parts[0]
    if common not in EXPENSE_CATEGORIES:
        return False
    return parts[1] in EXPENSE_CATEGORIES[common]


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG
    date_tuple = extract_date(income_date)
    if date_tuple is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG
    if not is_valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(
        {
            CAT_KEY: category_name,
            AMOUNT_KEY: amount,
            DATE_KEY: date_tuple,
        }
    )
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for cat, subcats in EXPENSE_CATEGORIES.items():
        lines.extend(f"{cat}::{sub}" for sub in subcats)
    return "\n".join(lines)


def _add_expense(cat_stats: StatsDict, cat: str, amt: float) -> None:
    cat_stats[cat] = cat_stats.get(cat, 0) + amt


def process_expense(
    amt: float,
    cat: str,
    stats: StatsDict,
    cat_stats: StatsDict,
    *,
    is_same_month: bool,
) -> None:
    stats["total_cap"] -= amt
    if is_same_month:
        stats["month_exp"] += amt
        _add_expense(cat_stats, cat, amt)


def process_income(
    amt: float,
    stats: StatsDict,
    *,
    is_same_month: bool,
) -> None:
    stats["total_cap"] += amt
    if is_same_month:
        stats["month_inc"] += amt


def get_cmp_date(dt: DateTuple) -> DateTuple:
    return dt[2], dt[1], dt[0]


def is_same_month(dt: DateTuple, target_cmp: DateTuple) -> bool:
    cmp_dt = get_cmp_date(dt)
    if cmp_dt[0] != target_cmp[0]:
        return False
    return cmp_dt[1] == target_cmp[1]


def apply_expense(
    record: dict[str, Any],
    stats: StatsDict,
    cat_stats: StatsDict,
    *,
    is_same: bool,
) -> None:
    cat_str = str(record[CAT_KEY]).split("::")[1]
    process_expense(
        float(record[AMOUNT_KEY]),
        cat_str,
        stats,
        cat_stats,
        is_same_month=is_same,
    )


def apply_income(
    record: dict[str, Any],
    stats: StatsDict,
    *,
    is_same: bool,
) -> None:
    process_income(float(record[AMOUNT_KEY]), stats, is_same_month=is_same)


def apply_record(
    record: dict[str, Any],
    target_cmp: DateTuple,
    stats: StatsDict,
    cat_stats: StatsDict,
) -> None:
    if get_cmp_date(record[DATE_KEY]) > target_cmp:
        return
    is_same = is_same_month(record[DATE_KEY], target_cmp)
    if record.get(CAT_KEY) is None:
        apply_income(record, stats, is_same=is_same)
    else:
        apply_expense(record, stats, cat_stats, is_same=is_same)


def calculate_stats(target_cmp: DateTuple) -> tuple[StatsDict, StatsDict]:
    stats: StatsDict = {}
    stats["total_cap"] = 0
    stats["month_inc"] = 0
    stats["month_exp"] = 0
    cat_stats: StatsDict = {}
    for record in financial_transactions_storage:
        if record:
            apply_record(record, target_cmp, stats, cat_stats)

    return stats, cat_stats


def format_amount(amt: float) -> str:
    if amt == int(amt):
        return str(int(amt))
    return str(amt)


def format_cat_line(idx: int, cat: str, amt: float) -> str:
    return f"{idx}. {cat}: {format_amount(amt)}"


def build_stats(
    report_date: str,
    stats: StatsDict,
    res_val: float,
) -> list[str]:
    res_type = "profit" if res_val >= 0 else "loss"
    return [
        f"Your statistics as of {report_date}:",
        f"Total capital: {stats['total_cap']:.2f} rubles",
        f"This month, the {res_type} amounted to {abs(res_val):.2f} rubles.",
        f"Income: {stats['month_inc']:.2f} rubles",
        f"Expenses: {stats['month_exp']:.2f} rubles",
        "\nDetails (category: amount):",
    ]


def append_categories(lines: list[str], cat_stats: StatsDict) -> None:
    for index, item in enumerate(sorted(cat_stats.items()), 1):
        lines.append(format_cat_line(index, item[0], item[1]))


def format_stats(
    report_date: str,
    stats: StatsDict,
    cat_stats: StatsDict,
) -> str:
    res_val = stats["month_inc"] - stats["month_exp"]
    lines = build_stats(report_date, stats, res_val)
    append_categories(lines, cat_stats)
    return "\n".join(lines)


def stats_handler(report_date: str) -> str:
    target_tuple = extract_date(report_date)
    if not target_tuple:
        return INCORRECT_DATE_MSG

    stats, cat_stats = calculate_stats(get_cmp_date(target_tuple))
    return format_stats(report_date, stats, cat_stats)


def parse_float(val_str: str) -> float | None:
    v_str = val_str.replace(",", ".")
    check_v = v_str.removeprefix("-")

    parts = check_v.split(".")
    if len(parts) > MAX_FLOAT_PARTS:
        return None
    for part in parts:
        if not part.isdigit() and part != "":
            return None
    if not check_v or check_v == ".":
        return None

    return float(v_str)


def income_cmd(parts: list[str]) -> None:
    if len(parts) != INCOME_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    amt = parse_float(parts[1])
    if amt is None:
        print(NONPOSITIVE_VALUE_MSG)
        return

    print(income_handler(amt, parts[2]))


def cost_cmd(parts: list[str]) -> None:
    if len(parts) == COST_CAT_CMD_LEN and parts[1] == "categories":
        print(cost_categories_handler())
        return
    if len(parts) != COST_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    amt = parse_float(parts[2])
    if amt is None:
        print(NONPOSITIVE_VALUE_MSG)
        return
    res = cost_handler(parts[1], amt, parts[3])
    print(res)
    if res == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def stats_cmd(parts: list[str]) -> None:
    if len(parts) != STATS_CMD_LEN:
        print(UNKNOWN_COMMAND_MSG)
        return
    print(stats_handler(parts[1]))


def process_command(cmd_str: str) -> None:
    parts = cmd_str.replace(",", ".").split()
    if not parts:
        return
    cmd = parts[0]
    if cmd == "income":
        income_cmd(parts)
    elif cmd == "cost":
        cost_cmd(parts)
    elif cmd == "stats":
        stats_cmd(parts)
    else:
        print(UNKNOWN_COMMAND_MSG)


def main() -> None:
    is_running = True
    while is_running:
        cmd_str = input()
        process_command(cmd_str)


if __name__ == "__main__":
    main()
