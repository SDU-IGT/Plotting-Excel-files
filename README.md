# 🌍 World Map Plotting Tool

Create **publication-quality world maps** from Excel data using **Cartopy**, **GeoPandas**, and **Matplotlib**.  
This repo contains a minimal-but-powerful plotting function that reads a worksheet, aggregates values to **main regions** or **subregions**, and exports **PDF maps** in a Robinson projection with a horizontal colorbar.

> ℹ️ **About the project document (PDF):**  
> This README is built from the code (`plotting.py`) and the dependencies (`requirements.txt`).  

---

## ✅ TL;DR

```bash
# 1) Install deps
pip install -r requirements.txt

# 2) Adjust the call at the bottom of plotting.py to your file/sheet/columns
python plotting.py

# 3) Get PDFs under your chosen output folder (e.g., ./o2)
```

---

## 📦 Requirements

From `requirements.txt`:

```
numpy
pandas
openpyxl
matplotlib
geopandas
shapely>=2.0
pyproj>=3.5
cartopy
geodatasets
```

> 💡 Tip: On Windows and macOS, `cartopy`/`geopandas` install more reliably via **conda** (because PROJ/GEOS/GDAL are native libs).  
> Example:
> ```bash
> conda create -n maps python=3.11 -y
> conda activate maps
> conda install -c conda-forge geopandas cartopy shapely pyproj pandas openpyxl matplotlib -y
> ```

---

## 🗺️ What the script does

`plotting.py` exposes one function:

```python
plot_world_maps_minimal(
    excel_path,          # path to .xlsx
    sheet_name,          # sheet name to read
    value_cols,          # list of numeric columns to plot
    out_dir,             # directory to save PDFs
    mainRegion=True,     # True → aggregate/plot at main-region level; False → subregion level
    year=None,           # int or list of ints; filters the 't'/'Year' column if present
    main_col=None,       # name of main-region column in your sheet (optional)
    sub_col=None         # name of subregion column in your sheet (optional)
)
```

**Key details implemented in code:**

- Basemap from **Natural Earth** via `geodatasets` or `cartopy` (with fallbacks).
- Country names are normalized (e.g., *"Côte d'Ivoire"* → *"Cote d'Ivoire"*, *"Czech Republic"* → *"Czechia"*).
- Values are clipped to the **2nd–98th percentiles** for color range stability.
- Uses **Robinson** projection, **RdBu_r** colormap, **horizontal colorbar**.
- Exports **one PDF per value column** (and per year, if `year` provided).
- Built-in **regional taxonomy** mapping (no external globals needed).

---

## 🔢 Expected input data (Excel)

Your worksheet should include:
- A **region column** (choose one):
  - `main_col` (e.g., “Main Region”, codes like **EUR**, **OAS**, **USA**, …), **or**
  - `sub_col` (e.g., “Regions (t)”, names like “W.Europe”, “India”, “China”, …)
- **Optional year column**: one of `t`, `Year`, or `year`
- One or more **numeric columns** to visualize (these make the maps).

**Example (subregion-based):**

| Regions (t) | Year | Number of~Animals SSP5 |
|-------------|------|------------------------|
| W.Europe    | 2050 | 120                    |
| China       | 2050 | 560                    |
| India       | 2050 | 470                    |

> If you pass `mainRegion=True` and only have `sub_col`, the function will **map subregions → main regions** and **sum** values.  
> If you pass `mainRegion=False` and only have `main_col`, it **replicates** main values to all its subregions for plotting.

---

## ▶️ How to run

Edit the example call at the bottom of `plotting.py` to your paths and columns:
```python
plot_world_maps_minimal(
    excel_path="animal_number_df.xlsx",
    sheet_name="Sheet1",
    value_cols=["Number of~Animals SSP5"],
    out_dir="o2",
    mainRegion=False,
    year=[2050],
    sub_col="Regions (t)"
)
```

Then run:
```bash
python plotting.py
```

**Output:** PDFs under `./o2/`, named like:
```
<value_col>.pdf                 # when year=None
<value_col>_<year>.pdf          # when year is provided
```

---



## 🧭 Regions & aggregation

The script includes built-in mappings for:
- **Main regions** (e.g., `EUR`, `OAS`, `USA`, `LAM`, `MEA`, `NEU`, `REF`, `SSA`, `IND`, `JPN`, `CHA`, `CAZ`)
- **Subregions** → **lists of countries** (e.g., *“W.Europe”*, *“SE.Asia”*, *“Rest S.Am.”*, …)

You can work either at the **main** or **subregion** level by toggling `mainRegion` and providing `main_col` / `sub_col` accordingly.

---

## 🧩 Color scaling

- The colormap range is set from the **2nd** to **98th** percentiles of finite values.
- If everything is identical, min–max is used.
- Missing values are shown in a light gray fill.

---

## 🛠️ Troubleshooting

- **“Could not detect region columns”**  
  Pass the column names explicitly via `main_col="..."` or `sub_col="..."`.

- **“Unknown subregions (no main mapping): [...]”**  
  Your sheet contains subregions not in the built-in mapping. Fix the names or extend the mapping in `plotting.py`.

- **No rows for the chosen year**  
  Ensure your worksheet has a column named `t`, `Year`, or `year` with numeric values matching the requested `year`.

- **Cartopy/GeoPandas install issues**  
  Prefer **conda** on Windows/macOS; verify that **GEOS**, **PROJ**, and **GDAL** are installed.

---

