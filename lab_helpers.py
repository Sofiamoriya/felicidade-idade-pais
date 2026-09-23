import requests
import numpy as np
import pandas as pd

OWID_AGE_URL = "https://ourworldindata.org/grapher/cantril-ladder-age-groups.csv?v=1&csvType=full&useColumnShortNames=false"

AGE_MID = {
    "Up to 29 years": 22.0,
    "30-44 years": 37.0,
    "45-59 years": 52.0,
    "60+ years": 70.0
}

def load_owid_age(filepath="owid_data/cantril-ladder-age-groups.csv"):
    try:
        df_raw = pd.read_csv(filepath)
    except Exception:
        df_raw = pd.read_csv(OWID_AGE_URL)
        
    age_long = pd.melt(
        df_raw,
        id_vars=["Entity", "Code", "Year"],
        value_vars=["Up to 29 years", "30-44 years", "45-59 years", "60+ years"],
        var_name="age_group",
        value_name="ladder_mean"
    ).rename(columns={"Entity": "country", "Code": "iso3", "Year": "year"})
    
    return age_long.dropna(subset=["iso3"]).reset_index(drop=True)

def build_country_table():
    # Código oficial do PIB per capita PPC do Banco Mundial
    indicators = {
        "NY.GDP.PCAP.PP.KD": "gdp_pc",
        "SP.POP.TOTL": "pop",
        "AG.LND.TOTL.K2": "area_km2"
    }
    dfs = []
    for ind_code, col_name in indicators.items():
        url = f"http://api.worldbank.org/v2/country/all/indicator/{ind_code}?date=2019:2023&format=json&per_page=2000"
        try:
            res = requests.get(url, timeout=10).json()
            if len(res) > 1 and res[1] is not None:
                records = []
                for entry in res[1]:
                    if entry.get("value") is not None:
                        records.append({
                            "iso3": entry["countryiso3code"],
                            "year": int(entry["date"]),
                            col_name: entry["value"]
                        })
                if records:
                    df_ind = pd.DataFrame(records)
                    df_ind = df_ind.sort_values("year").groupby("iso3").last().reset_index().drop(columns=["year"])
                    dfs.append(df_ind)
        except Exception:
            pass
            
    wb_df = dfs[0]
    for d in dfs[1:]:
        wb_df = wb_df.merge(d, on="iso3", how="outer")
    return wb_df

def to_iso3(series_names):
    mapping = {"Brazil": "BRA", "Finland": "FIN", "United States": "USA"}
    return series_names.map(lambda x: mapping.get(x, None))
