import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_rows', None)

# Połączenie z bazą
conn = sqlite3.connect("covid_analysis.db")

# ============================
# 1️⃣ Średnie dzienne zgony przed i po szczepieniach
# ============================
query_before = """
SELECT country,
       AVG(daily_deaths) as avg_before_vaccine
FROM daily_deaths
WHERE date >= '2020-12-27' AND date <= '2021-04-30'
GROUP BY country;
"""

query_after = """
SELECT country,
       AVG(daily_deaths) as avg_after_vaccine
FROM daily_deaths
WHERE date >= '2021-05-01' AND date <= '2021-08-31'
GROUP BY country;
"""

df_before = pd.read_sql_query(query_before, conn)
df_after = pd.read_sql_query(query_after, conn)

df_comparison = df_before.merge(df_after, on='country')
print("Średnie dzienne zgony przed i po szczepieniach:")
print(df_comparison)

# Wykres
df_comparison.plot(
    kind='bar',
    x='country',
    y=['avg_before_vaccine', 'avg_after_vaccine'],
    title='Średnie dzienne zgony przed i po szczepieniach',
    figsize=(10,6)
)
plt.ylabel('Zgony dzienne')
plt.xticks(rotation=0)
plt.savefig("plots/avg_deaths_before_after_vaccine.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================
# 2️⃣ Największa liczba zgonów jednego dnia w każdym kraju
# ============================
query_max_daily = """
SELECT country,
       MAX(daily_deaths) as max_daily_deaths
FROM daily_deaths
GROUP BY country;
"""

df_max_daily = pd.read_sql_query(query_max_daily, conn)
print("\nNajwiększa liczba zgonów jednego dnia:")
print(df_max_daily)

# Wykres
df_max_daily.plot(
    kind='bar',
    x='country',
    y='max_daily_deaths',
    title='Największa liczba zgonów jednego dnia',
    color='red',
    figsize=(10,6)
)
plt.ylabel('Zgony dzienne')
plt.xticks(rotation=0)
plt.savefig("plots/max_daily_deaths.png", dpi=300, bbox_inches="tight")
plt.show()


# ============================
# 3️⃣ Najgorszy miesiąc pandemii dla każdego kraju
# ============================
query_worst_month = """
SELECT country, month, monthly_deaths
FROM (
    SELECT country,
           strftime('%Y-%m', date) as month,
           SUM(daily_deaths) as monthly_deaths,
           RANK() OVER (PARTITION BY country ORDER BY SUM(daily_deaths) DESC) as rank_month
    FROM daily_deaths
    GROUP BY country, month
)
WHERE rank_month = 1
ORDER BY country;
"""

df_worst_month = pd.read_sql_query(query_worst_month, conn)
print("\nNajgorszy miesiąc pandemii dla każdego kraju:")
print(df_worst_month)

# Wykres
# Tworzymy nową kolumnę łącząc kraj i miesiąc
df_worst_month['country_month'] = df_worst_month['country'] + ' (' + df_worst_month['month'] + ')'

plt.figure(figsize=(10,6))
plt.bar(df_worst_month['country_month'], df_worst_month['monthly_deaths'], color='orange')
plt.title('Najgorszy miesiąc pandemii dla każdego kraju')
plt.ylabel('Liczba zgonów w miesiącu')
plt.xticks(rotation=30, ha='right')  # obrót dla lepszej czytelności
plt.tight_layout()
plt.savefig("plots/worst_month_pandemic.png", dpi=300, bbox_inches="tight")
plt.show()