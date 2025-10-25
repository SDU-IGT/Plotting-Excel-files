def plot_world_maps_minimal(excel_path, sheet_name, value_cols, out_dir, mainRegion=True, year=None, main_col=None, sub_col=None):
    """
    Minimal inputs. Creates one PDF per value column (and per year if a list is given):
      <out_dir>/<value_col>_<year>.pdf   or   <out_dir>/<value_col>.pdf
    Style: Cartopy Robinson, RdBu_r, horizontal colorbar.

    Requires globals in your environment:
      - REGION_TO_MAIN_MAP
      - _SUBREGION_TO_COUNTRIES
    """
    import os
    from pathlib import Path
    import warnings
    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    # ---- sanity: mappings must exist ----
    REGION_TO_MAIN_MAP = {'Canada': 'CAZ',
    'Oceania': 'CAZ',
    'China': 'CHA',
    'C.Europe': 'EUR',
    'W.Europe': 'EUR',
    'India': 'IND',
    'Japan': 'JPN',
    'Brazil': 'LAM',
    'Mexico': 'LAM',
    'Rest C.Am.': 'LAM',
    'Rest S.Am.': 'LAM',
    'M.East': 'MEA',
    'N.Africa': 'MEA',
    'Turkey': 'NEU',
    'Ukraine': 'NEU',
    'Indonesia': 'OAS',
    'Korea': 'OAS',
    'Rest S Asia': 'OAS',
    'SE.Asia': 'OAS',
    'Russia': 'REF',
    'Stan': 'REF',
    'E.Africa': 'SSA',
    'Rest S Africa': 'SSA',
    'S.Africa': 'SSA',
    'W.Africa': 'SSA',
    'USA': 'USA'}

    _SUBREGION_TO_COUNTRIES = {
    "Canada":["Canada"],
    "USA":["United States of America"],
    "Mexico":["Mexico"],
    "Rest C.Am.":[
        "Belize","Guatemala","Honduras","El Salvador","Nicaragua","Costa Rica","Panama",
        "Cuba","Jamaica","Haiti","Dominican Republic","The Bahamas","Trinidad and Tobago",
        "Barbados","Grenada","Saint Lucia","Saint Vincent and the Grenadines",
        "Antigua and Barbuda","Dominica","Saint Kitts and Nevis"
    ],
    "Brazil":["Brazil"],
    "Rest S.Am.":[
        "Argentina","Chile","Uruguay","Paraguay","Bolivia","Peru","Ecuador","Colombia",
        "Venezuela","Guyana","Suriname"
    ],
    "N.Africa":["Morocco","Algeria","Tunisia","Libya","Egypt","Western Sahara"],
    "W.Africa":[
        "Benin","Burkina Faso","Cabo Verde","Cote d'Ivoire","Gambia","Ghana","Guinea",
        "Guinea-Bissau","Liberia","Mali","Mauritania","Niger","Nigeria","Senegal",
        "Sierra Leone","Togo"
    ],
    "E.Africa":[
        "Burundi","Comoros","Djibouti","Eritrea","Ethiopia","Kenya","Madagascar","Malawi",
        "Mauritius","Mozambique","Rwanda","Seychelles","Somalia","South Sudan","Sudan",
        "Tanzania","Uganda"
    ],
    "S.Africa":["South Africa"],
    "Rest S Africa":["Angola","Botswana","Eswatini","Lesotho","Namibia","Zambia","Zimbabwe"],
    "W.Europe":[
        "France","Germany","Netherlands","Belgium","Luxembourg","Austria","Switzerland",
        "Italy","Spain","Portugal","Greece","Malta","Andorra","San Marino","Monaco","Liechtenstein"
    ],
    "C.Europe":[
        "Poland","Czechia","Slovakia","Hungary","Slovenia","Croatia","Romania","Bulgaria",
        "Bosnia and Herzegovina","Serbia","Montenegro","North Macedonia","Albania","Kosovo"
    ],
    "Turkey":["Turkey"],
    "Ukraine":["Ukraine"],
    "Russia":["Russia"],
    "Stan":["Kazakhstan","Kyrgyzstan","Tajikistan","Turkmenistan","Uzbekistan"],
    "M.East":[
        "Saudi Arabia","United Arab Emirates","Qatar","Bahrain","Kuwait","Oman","Yemen",
        "Iraq","Iran","Jordan","Lebanon","Israel","Syria"
    ],
    "India":["India"],
    "Korea":["Korea, Republic of","Korea, Democratic People's Republic of"],
    "China":["China"],
    "SE.Asia":["Thailand","Viet Nam","Cambodia","Lao PDR","Myanmar","Malaysia","Singapore",
               "Philippines","Brunei","Timor-Leste"],
    "Indonesia":["Indonesia"],
    "Japan":["Japan"],
    "Rest S Asia":["Pakistan","Bangladesh","Sri Lanka","Nepal","Bhutan","Afghanistan","Maldives"],
    "Oceania":[
        "Papua New Guinea","Solomon Islands","Vanuatu","Fiji","Samoa","Tonga","Kiribati",
        "Micronesia","Marshall Islands","Palau","Nauru","Tuvalu"
    ],
}

    # ---------- helpers ----------
    def _set_white_outline(ax, lw=0.8):
        if hasattr(ax, "outline_patch") and ax.outline_patch is not None:
            ax.outline_patch.set_edgecolor("white"); ax.outline_patch.set_linewidth(lw)
        elif hasattr(ax, "spines") and "geo" in ax.spines:
            ax.spines["geo"].set_edgecolor("white"); ax.spines["geo"].set_linewidth(lw)

    def _normalize_name_column(gdf):
        for cand in ["ADMIN","NAME_LONG","FORMAL_EN","NAME","name","name_long","BRK_NAME"]:
            if cand in gdf.columns:
                gdf = gdf.rename(columns={cand: "NAME_STD"})
                break
        if "NAME_STD" not in gdf.columns:
            raise ValueError("Basemap has no recognizable name column.")
        # harmonize to the names used in your mapping dict
        gdf["NAME_STD"] = gdf["NAME_STD"].replace({
            "Côte d'Ivoire": "Cote d'Ivoire",
            "Bahamas": "The Bahamas",
            "Cape Verde": "Cabo Verde",
            "Laos": "Lao PDR",
            "Vietnam": "Viet Nam",
            "W. Sahara": "Western Sahara",
            "Federated States of Micronesia": "Micronesia",
            "South Korea": "Korea, Republic of",
            "North Korea": "Korea, Democratic People's Republic of",
            "Czech Republic": "Czechia",
            "Swaziland": "Eswatini",
            "East Timor": "Timor-Leste",
        })
        return gdf

    def _load_world():
        env_path = os.getenv("LCA_WORLD_GEOJSON")
        if env_path and Path(env_path).exists():
            return _normalize_name_column(gpd.read_file(env_path))
        try:
            import geodatasets as gd
            for key in (
                "naturalearth.cultural.admin_0_countries",
                "naturalearth.cultural.v10.admin_0_countries",
                "naturalearth.cultural.countries.admin_0",
            ):
                try:
                    return _normalize_name_column(gpd.read_file(gd.get_path(key)))
                except Exception:
                    pass
        except Exception:
            pass
        try:
            import cartopy.io.shapereader as shpreader
            shp = shpreader.natural_earth("110m", "cultural", "admin_0_countries")
            return _normalize_name_column(gpd.read_file(shp))
        except Exception:
            pass
        for url in (
            "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
            "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
        ):
            try:
                return _normalize_name_column(gpd.read_file(url))
            except Exception:
                pass
        raise RuntimeError("Could not load a Natural Earth basemap. Set LCA_WORLD_GEOJSON or install `geodatasets`/`cartopy`.")

    # def _detect_region_cols(df):
        # return (main_col_or_None, sub_col_or_None)
        # main_cands = ["Main regions","Main Regions","Main region","Main Region"]
        # sub_cands  = ["Regions (t)","Regions","Region","Subregions","Subregion","Regions(t)"]
        # main_col = next((c for c in main_cands if c in df.columns), None)
        # sub_col  = next((c for c in sub_cands  if c in df.columns), None)
        # if not (main_col or sub_col):
        #     # fallback: look for any column containing 'region'
        #     guess = next((c for c in df.columns if "region" in str(c).lower()), None)
        #     if guess:
        #         sub_col = guess
        # return main_col, sub_col

    def _detect_year_col_min(df):
        for c in ["t","Year","year"]:
            if c in df.columns: return c
        return None

    def _invert_region_to_main():
        m = {}
        for sub, main in REGION_TO_MAIN_MAP.items():
            m.setdefault(main, []).append(sub)
        return m

    def _build_main_region_polygons():
        world = _load_world()
        main_to_sub = _invert_region_to_main()
        pieces = []
        for main, subs in main_to_sub.items():
            countries = []
            for sub in subs:
                countries += _SUBREGION_TO_COUNTRIES.get(sub, [])
            if not countries:
                continue
            part = world[world["NAME_STD"].isin(set(countries))].copy()
            if part.empty:
                continue
            part["__JOIN__"] = main
            pieces.append(part)
        if not pieces:
            raise ValueError("No main-region polygons could be built; check mappings.")
        g = gpd.GeoDataFrame(pd.concat(pieces, ignore_index=True), crs=world.crs)
        g = g.dissolve(by="__JOIN__", as_index=False)
        return g.rename(columns={"__JOIN__": "MAIN"})

    def _build_subregion_polygons():
        world = _load_world()
        pieces = []
        for sub, countries in _SUBREGION_TO_COUNTRIES.items():
            if not countries:
                continue
            part = world[world["NAME_STD"].isin(set(countries))].copy()
            if part.empty:
                continue
            part["__JOIN__"] = sub
            pieces.append(part)
        if not pieces:
            raise ValueError("No subregion polygons could be built; check _SUBREGION_TO_COUNTRIES.")
        g = gpd.GeoDataFrame(pd.concat(pieces, ignore_index=True), crs=world.crs)
        g = g.dissolve(by="__JOIN__", as_index=False)
        return g.rename(columns={"__JOIN__": "REGION"})

    def _years_list(y, ycol_found: bool):
        if y is None:
            return [None]
        if isinstance(y, (list, tuple, set, np.ndarray)):
            ylist = [int(v) for v in y]
        else:
            ylist = [int(y)]
        if not ycol_found:
            raise ValueError("You provided year(s), but no year column ('t'/'Year') was found in the sheet.")
        return ylist

    # ---------- read + prep ----------
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

    # main_col, sub_col = _detect_region_cols(df)
    if not (main_col or sub_col):
        raise KeyError("Could not detect region columns (looked for 'Main regions' / 'Regions (t)' / 'Region').")

    ycol = _detect_year_col_min(df)
    year_values = _years_list(year, ycol is not None) if year is not None else [None]

    # normalize region strings
    if main_col: df[main_col] = df[main_col].astype(str).str.strip()
    if sub_col:  df[sub_col]  = df[sub_col].astype(str).str.strip()

    # choose output geometry based on mainRegion flag
    if mainRegion:
        g_poly = _build_main_region_polygons()
        want_key = "MAIN"
    else:
        g_poly = _build_subregion_polygons()
        want_key = "REGION"

    # ---------- plots ----------
    for yr in year_values:
        df_y = df.copy()
        if yr is not None:
            df_y[ycol] = pd.to_numeric(df_y[ycol], errors="coerce")
            df_y = df_y[df_y[ycol] == int(yr)]
            if df_y.empty:
                warnings.warn(f"[plot] No rows for {ycol} == {yr} in '{sheet_name}'. Skipping this year.")
                continue

        for col in value_cols:
            if col not in df_y.columns:
                warnings.warn(f"[plot] Skipping '{col}' — column not found.")
                continue

            vals = pd.to_numeric(df_y[col], errors="coerce")

            # ---- harmonize data level → desired plotting level ----
            if mainRegion:
                # want MAIN values
                if main_col:
                    tbl = df_y[[main_col]].copy()
                    tbl["__val__"] = vals
                    tbl = tbl.groupby(main_col, as_index=False)["__val__"].sum()
                    tbl = tbl.rename(columns={main_col: "MAIN"})
                elif sub_col:
                    # map sub → main, then sum
                    tbl = df_y[[sub_col]].copy()
                    tbl["__MAIN__"] = tbl[sub_col].map(REGION_TO_MAIN_MAP)
                    if tbl["__MAIN__"].isna().any():
                        miss = sorted(set(tbl.loc[tbl["__MAIN__"].isna(), sub_col]))
                        warnings.warn(f"Unknown subregions (no main mapping): {miss}")
                        tbl = tbl.dropna(subset=["__MAIN__"])
                    tbl["__val__"] = vals.loc[tbl.index]
                    tbl = tbl.groupby("__MAIN__", as_index=False)["__val__"].sum()
                    tbl = tbl.rename(columns={"__MAIN__": "MAIN"})
                else:
                    raise KeyError("No region column available to build MAIN table.")
            else:
                # want REGION (subregion) values
                if sub_col:
                    tbl = df_y[[sub_col]].copy()
                    tbl["__val__"] = vals
                    tbl = tbl.groupby(sub_col, as_index=False)["__val__"].sum()
                    tbl = tbl.rename(columns={sub_col: "REGION"})
                elif main_col:
                    # replicate each MAIN value to all its subregions
                    inv = _invert_region_to_main()
                    grouped = df_y.groupby(main_col, as_index=True)[col].sum()
                    rows = []
                    for main_code, v in grouped.items():
                        for sub in inv.get(str(main_code), []):
                            rows.append({"REGION": sub, "__val__": float(v)})
                    tbl = pd.DataFrame(rows)
                else:
                    raise KeyError("No region column available to build REGION table.")

            # ---- join to polygons & color limits ----
            g = g_poly.merge(tbl, left_on=want_key, right_on=want_key, how="left")

            arr = pd.to_numeric(g["__val__"], errors="coerce").to_numpy(dtype=float)
            finite = arr[np.isfinite(arr)]
            if finite.size == 0:
                warnings.warn(f"[plot] '{col}' has no finite values; skipping.")
                continue
            lo = float(np.nanpercentile(finite, 2))
            hi = float(np.nanpercentile(finite, 98))
            if lo == hi:
                lo, hi = float(np.nanmin(finite)), float(np.nanmax(finite))
            norm = mpl.colors.Normalize(vmin=lo, vmax=hi)
            cmap = plt.get_cmap("RdBu_r")

            # ---- figure ----
            proj = ccrs.Robinson()
            fig = plt.figure(figsize=(22, 12), dpi=240)
            ax = plt.axes(projection=proj)
            _set_white_outline(ax)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.35)
            ax.add_feature(cfeature.BORDERS, linewidth=0.25)
            ax.set_global()

            for _, row in g.iterrows():
                v = row["__val__"]
                face = cmap(norm(v)) if np.isfinite(v) else "#e5e7eb"
                ax.add_geometries(
                    [row.geometry],
                    crs=ccrs.PlateCarree(),
                    facecolor=face,
                    edgecolor="white",
                    linewidth=0.35,
                    zorder=1,
                )

            mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cmap); mappable.set_array([])
            cbar = plt.colorbar(mappable, ax=ax, orientation="horizontal", pad=0.03, shrink=0.7)
            label = f"{col}" + (f", year: {yr}" if yr is not None else "")
            cbar.set_label(label, fontsize=20, labelpad=8, weight="bold")
            cbar.ax.tick_params(labelsize=18, pad=6)
            for lbl in cbar.ax.get_xticklabels():
                try: lbl.set_fontweight("bold")
                except Exception: pass
            off = cbar.ax.xaxis.get_offset_text()
            off.set_size(18)
            try: off.set_weight("bold")
            except Exception: pass

            plt.subplots_adjust(bottom=0.03, top=0.99, left=0.02, right=0.98)

            safe_col = str(col).replace("/", "-").replace("\\", "-").replace(" ", "_")
            fname = f"{safe_col}_{yr}.pdf" if yr is not None else f"{safe_col}.pdf"
            out_path = Path(out_dir) / fname
            plt.savefig(out_path, bbox_inches="tight", dpi=240)
            plt.close(fig)


plot_world_maps_minimal(
    "animal_number_df.xlsx", "Sheet1",
    ["Number of~Animals SSP5"],
    out_dir="o2", mainRegion=False, year=[2050], sub_col="Regions (t)"
)
