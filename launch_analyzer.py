import csv

DATA_FILE = "space_missions.csv"

COL_COMPANY = "Company"
COL_LOCATION = "Location"
COL_DATE = "Date"
COL_ROCKET = "Rocket"
COL_MISSION = "Mission"
COL_STATUS = "MissionStatus"

REQUIRED_COLUMNS = [COL_COMPANY, COL_LOCATION, COL_DATE, COL_ROCKET, COL_MISSION, COL_STATUS]

COUNTRY_FIXES = {
    "New Mexico": "USA",
    "Pacific Missile Range Facility": "USA",
    "Gran Canaria": "USA",
    "Yellow Sea": "China",
    "Barents Sea": "Russia",
    "Shahrud Missile Test Site": "Iran",
}


def read_lines(filename):
    """The file is mostly UTF-8 but has a few older Latin-1 lines (like "Armée de l'Air"), so decode line by line."""
    lines = []
    with open(filename, "rb") as file:
        for raw_line in file:
            try:
                lines.append(raw_line.decode("utf-8"))
            except UnicodeDecodeError:
                lines.append(raw_line.decode("latin-1"))
    if len(lines) > 0:
        lines[0] = lines[0].lstrip("\ufeff")
    return lines


def load_launches(filename):
    """Uses csv.DictReader because some locations have commas inside quotes."""
    launches = []
    for row in csv.DictReader(read_lines(filename)):
        launch = {}
        for key, value in row.items():
            if key is None:
                continue
            if value is None:
                value = ""
            launch[key.strip()] = value.strip()
        launches.append(launch)
    return launches


def get_company(launch):
    return launch[COL_COMPANY]


def get_rocket(launch):
    return launch[COL_ROCKET]


def get_country(launch):
    last_part = launch[COL_LOCATION].split(",")[-1].strip()
    if last_part == "":
        return "Unknown"
    return COUNTRY_FIXES.get(last_part, last_part)


def get_date_parts(launch):
    date_text = launch[COL_DATE].strip()
    if date_text == "":
        return (9999, 0, 0)
    date_text = date_text.split()[0]
    parts = date_text.replace("/", "-").split("-")
    try:
        if len(parts[0]) == 4:
            year, month, day = parts
        else:
            month, day, year = parts
        return (int(year), int(month), int(day))
    except ValueError:
        return (9999, 0, 0)


def get_year(launch):
    return get_date_parts(launch)[0]


def get_decade(launch):
    return get_year(launch) // 10 * 10


def is_success(launch):
    """Only 'Success' counts. Partial and prelaunch failures count as not successful."""
    return launch[COL_STATUS].lower() == "success"


def launches_with_dates(launches):
    good = []
    for launch in launches:
        if get_year(launch) != 9999:
            good.append(launch)
    return good


def count_by(launches, key_function):
    """One counting function for any category: year, country, company, rocket, or decade."""
    counts = {}
    for launch in launches:
        key = key_function(launch)
        counts[key] = counts.get(key, 0) + 1
    return counts


def success_rates_by(launches, key_function):
    totals = count_by(launches, key_function)

    successful = []
    for launch in launches:
        if is_success(launch):
            successful.append(launch)
    wins = count_by(successful, key_function)

    rates = {}
    for key in totals:
        rates[key] = percent(wins.get(key, 0), totals[key])
    return rates


def top_n(counts, n):
    pairs = []
    for name, count in counts.items():
        pairs.append((count, name))
    pairs.sort(key=get_name)
    pairs.sort(key=get_count, reverse=True)
    return pairs[:n]


def get_count(pair):
    return pair[0]


def get_name(pair):
    return str(pair[1])


def percent(part, whole):
    if whole == 0:
        return 0.0
    return 100 * part / whole


def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def describe(launch):
    return f"{launch[COL_DATE]}  {launch[COL_MISSION]} ({launch[COL_COMPANY]}, {launch[COL_ROCKET]})"


def show_overview(launches):
    print_header("OVERVIEW")
    total = len(launches)
    successes = 0
    for launch in launches:
        if is_success(launch):
            successes += 1

    print(f"Total launches:      {total:,}")
    print(f"Successful launches: {successes:,} ({percent(successes, total):.1f}%)")
    print(f"Countries:           {len(count_by(launches, get_country))}")
    print(f"Companies:           {len(count_by(launches, get_company))}")
    print(f"Rocket types:        {len(count_by(launches, get_rocket))}")

    dated = launches_with_dates(launches)
    if len(dated) > 0:
        first = min(dated, key=get_date_parts)
        last = max(dated, key=get_date_parts)
        print()
        print(f"First launch: {describe(first)}")
        print(f"Last launch:  {describe(last)}")


def show_launches_per_year(launches):
    print_header("LAUNCHES PER YEAR")
    counts = count_by(launches_with_dates(launches), get_year)
    if len(counts) == 0:
        print("No launches with readable dates.")
        return
    biggest = max(counts.values())
    for year in sorted(counts):
        bar_length = max(1, counts[year] * 40 // biggest)
        print(f"{year}  {counts[year]:>4}  {'*' * bar_length}")

    busiest_count, busiest_year = top_n(counts, 1)[0]
    print(f"\nBusiest year: {busiest_year} with {busiest_count} launches")


def show_success_by_country(launches):
    print_header("SUCCESS RATE BY COUNTRY (top 10 by number of launches)")
    print("Country = where the launch site is located.\n")
    counts = count_by(launches, get_country)
    rates = success_rates_by(launches, get_country)
    print(f"{'Country':<30}{'Launches':>10}{'Success':>10}")
    for count, country in top_n(counts, 10):
        print(f"{country[:28]:<30}{count:>10}{rates[country]:>9.1f}%")


def print_ranked(counts, n, label):
    print(f"{'Rank':<6}{label:<34}{'Launches':>10}")
    rank = 1
    for count, name in top_n(counts, n):
        print(f"{rank:<6}{name[:32]:<34}{count:>10}")
        rank += 1


def show_top_companies_and_rockets(launches):
    print_header("TOP 10 COMPANIES")
    print_ranked(count_by(launches, get_company), 10, "Company")
    print_header("TOP 10 ROCKETS")
    print_ranked(count_by(launches, get_rocket), 10, "Rocket")


def show_success_by_decade(launches):
    print_header("SUCCESS RATE BY DECADE")
    dated = launches_with_dates(launches)
    counts = count_by(dated, get_decade)
    rates = success_rates_by(dated, get_decade)
    print(f"{'Decade':<10}{'Launches':>10}{'Success':>10}")
    for decade in sorted(counts):
        print(f"{str(decade) + 's':<10}{counts[decade]:>10}{rates[decade]:>9.1f}%")


def search_launches(launches):
    print_header("SEARCH LAUNCHES")
    text = input("Search by company, rocket, mission, or year (e.g. SpaceX, Falcon 9, 1969): ")
    text = text.strip().lower()
    if text == "":
        print("You didn't type anything.")
        return

    matches = []
    for launch in launches:
        searchable = (launch[COL_COMPANY] + " " + launch[COL_ROCKET] + " " + launch[COL_MISSION]).lower()
        if text in searchable or text == str(get_year(launch)):
            matches.append(launch)

    if len(matches) == 0:
        print(f'No launches found for "{text}".')
        return

    matches.sort(key=get_date_parts)
    successes = 0
    for launch in matches:
        if is_success(launch):
            successes += 1

    print(f"\nFound {len(matches)} launches ({percent(successes, len(matches)):.1f}% successful).")
    print("Showing up to 25:\n")
    print(f"{'Date':<12}{'Company':<18}{'Rocket':<22}{'Mission':<24}Result")
    for launch in matches[:25]:
        print(f"{launch[COL_DATE]:<12}"
              f"{launch[COL_COMPANY][:16]:<18}"
              f"{launch[COL_ROCKET][:20]:<22}"
              f"{launch[COL_MISSION][:22]:<24}"
              f"{launch[COL_STATUS]}")
    if len(matches) > 25:
        print(f"\n...and {len(matches) - 25} more. Try a more specific search.")


def show_chart(launches):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nThe chart needs matplotlib. Install it with:  pip install matplotlib")
        return

    counts = count_by(launches_with_dates(launches), get_year)
    if len(counts) == 0:
        print("No launches with readable dates.")
        return
    years = sorted(counts)
    totals = []
    for year in years:
        totals.append(counts[year])

    plt.figure(figsize=(12, 5))
    plt.bar(years, totals, color="steelblue")
    plt.title(f"Space Launches per Year ({years[0]}-{years[-1]})")
    plt.xlabel("Year")
    plt.ylabel("Number of launches")
    plt.tight_layout()
    plt.savefig("launches_per_year.png")
    print("\nChart saved as launches_per_year.png")
    plt.show()


MENU = """
=== APOGEE: SPACE LAUNCH ANALYZER ===
1. Overview
2. Launches per year
3. Success rate by country
4. Top companies and rockets
5. Success rate by decade
6. Search launches
7. Chart: launches per year
8. Quit"""


def main():
    try:
        launches = load_launches(DATA_FILE)
    except FileNotFoundError:
        print(f"Couldn't find {DATA_FILE}.")
        print("Download it (see README.md) and put it in the same folder as this program.")
        return

    if len(launches) == 0:
        print("The data file is empty.")
        return

    missing = []
    for column in REQUIRED_COLUMNS:
        if column not in launches[0]:
            missing.append(column)
    if len(missing) > 0:
        print("These columns weren't found in the CSV:", ", ".join(missing))
        print("Columns in your file:", ", ".join(launches[0].keys()))
        print("Update the COL_ names at the top of launch_analyzer.py to match.")
        return

    dated = launches_with_dates(launches)
    if len(dated) > 0:
        first_year = get_year(min(dated, key=get_date_parts))
        last_year = get_year(max(dated, key=get_date_parts))
        print(f"\nLoaded {len(launches):,} launches ({first_year}-{last_year})")
    else:
        print(f"\nLoaded {len(launches):,} launches")

    while True:
        try:
            print(MENU)
            choice = input("Choose an option (1-8): ").strip()
            if choice == "1":
                show_overview(launches)
            elif choice == "2":
                show_launches_per_year(launches)
            elif choice == "3":
                show_success_by_country(launches)
            elif choice == "4":
                show_top_companies_and_rockets(launches)
            elif choice == "5":
                show_success_by_decade(launches)
            elif choice == "6":
                search_launches(launches)
            elif choice == "7":
                show_chart(launches)
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Please type a number from 1 to 8.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
