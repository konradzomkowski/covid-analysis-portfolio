# covid_analysis_portfolio_fixed.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import os

# ============================
# Ustawienia globalne
# ============================
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)

population = {
    'POL': 38_000_000,
    'UKR': 41_000_000,
    'FRA': 67_000_000,
    'DEU': 83_000_000,
    'CZE': 10_700_000
}

countries = list(population.keys())

output_dir = "plots"
os.makedirs(output_dir, exist_ok=True)

date_start = pd.to_datetime('2020-03-12')
date_end = pd.to_datetime('2022-07-31')

# ============================
# Funkcje pomocnicze
# ============================
def millions(x, pos):
    """Formatuje liczby w milionach, np. 2_000_000 -> 2M"""
    return f'{int(x/1_000_000)}M'


def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """Wczytuje dane i filtruje wybrane kolumny i kraje"""
    df = pd.read_csv(
        filepath,
        usecols=['date', 'confirmed', 'deaths','people_vaccinated', 'key_gadm'],
        low_memory=False
    )
    df = df[df['key_gadm'].isin(countries)]
    df['date'] = pd.to_datetime(df['date'])
    return df.reset_index(drop=True)


def compute_rolling_avg(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """Liczy 7-dniowe średnie i zgony na milion mieszkańców"""
    df_c = df[df['key_gadm']==country].copy()
    df_c = df_c.groupby('date')[['deaths','people_vaccinated']].max().reset_index()
    df_c['deaths_avg7'] = df_c['deaths'].rolling(7, min_periods=1).mean()
    df_c['vaccinated_avg7'] = df_c['people_vaccinated'].rolling(7, min_periods=1).mean()
    df_c['deaths_per_million'] = df_c['deaths_avg7'] / population[country] * 1_000_000
    df_c['country'] = country
    # Filtracja jednolitego zakresu dat
    df_c = df_c[(df_c['date'] >= date_start) & (df_c['date'] <= date_end)]
    return df_c.dropna(subset=['deaths_per_million'])


def plot_country(df_country: pd.DataFrame, save_path: str = None):
    """Rysuje wykres zgonów i szczepień dla jednego kraju"""
    fig, ax1 = plt.subplots(figsize=(12,6))

    # Zgony
    ax1.plot(df_country['date'], df_country['deaths_avg7'], color='red', label='Zgony (7 dni avg)')
    ax1.set_ylabel('Zgony', color='red')
    ax1.tick_params(axis='y', labelcolor='red')

    # Szczepienia
    ax2 = ax1.twinx()
    ax2.plot(df_country['date'], df_country['vaccinated_avg7'], color='green', label='Zaszczepieni (7 dni avg)')
    ax2.set_ylabel('Zaszczepieni', color='green')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.yaxis.set_major_formatter(FuncFormatter(millions))

    # Tytuł i legenda
    plt.title(f'Zgony vs szczepienia ({df_country["country"].iloc[0]})')
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    ax1.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def plot_comparison(df_all: pd.DataFrame, save_path: str = None):
    """Wykres porównawczy zgony na milion mieszkańców dla wszystkich krajów"""
    plt.figure(figsize=(14,6))
    sns.lineplot(data=df_all, x='date', y='deaths_per_million', hue='country', linewidth=2)

    # Pionowa linia: start szczepień
    start_vaccination = pd.to_datetime('2020-12-27')
    plt.axvline(start_vaccination, color='black', linestyle='--', linewidth=2)
    plt.text(start_vaccination, df_all['deaths_per_million'].max(),
             'Start szczepień', rotation=90,
             verticalalignment='top', horizontalalignment='right', color='black')

    # Pozioma linia: moment działania szczepionek (~miesiąc później)
    effect_date = pd.to_datetime('2021-01-27')
    effect_value = df_all[df_all['date']==effect_date]['deaths_per_million'].mean()

    plt.title('Zgony COVID na milion mieszkańców (7-dniowa średnia)')
    plt.xlabel('Data')
    plt.ylabel('Zgony na milion mieszkańców')
    plt.legend(title='Kraj')
    plt.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


def compute_daily_deaths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Liczy dzienne zgony jako różnicę między dniami dla każdego kraju
    """

    df_daily_list = []

    for country in countries:
        df_c = df[df['key_gadm'] == country].copy()

        # grupowanie po dacie
        df_c = df_c.groupby('date')[['deaths']].max().reset_index()

        # obliczenie różnicy dzień do dnia
        df_c['daily_deaths'] = df_c['deaths'].diff()

        # dodanie kolumny kraju
        df_c['country'] = country

        # filtr zakresu dat
        df_c = df_c[(df_c['date'] >= date_start) & (df_c['date'] <= date_end)]
        df_daily_list.append(df_c)

    df_daily = pd.concat(df_daily_list)
    df_daily = df_daily.sort_values(['country', 'date'])

    return df_daily
# ============================
# Główny blok
# ============================
if __name__ == "__main__":
    df = load_and_clean_data("covid_data.csv")
    df_all_countries = []

    # Wykresy dla pojedynczych krajów
    for country in countries:
        df_c = compute_rolling_avg(df, country)
        df_all_countries.append(df_c)
        plot_country(df_c, save_path=f"{output_dir}/{country}_deaths_vs_vaccinations.png")

    # Wykres porównawczy wszystkich krajów
    df_all = pd.concat(df_all_countries)
    plot_comparison(df_all, save_path=f"{output_dir}/all_countries_comparison.png")

    df_daily_deaths = compute_daily_deaths(df)
    pd.set_option('display.max_rows', None)
    print(df_daily_deaths)

from db_connection import save_daily_deaths
df_daily_deaths = compute_daily_deaths(df)
save_daily_deaths(df_daily_deaths)

