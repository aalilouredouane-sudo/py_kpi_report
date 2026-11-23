# py_kpi_report

Python tool written for the convergence study of the Terrorism and Conflagration model.

The Terrorism / Conflagration tool simulates losses with a stochastic frequency / severity model. For a fixed seed, it runs 500,000 (or 1,000,000) simulations and summarises the resulting losses in catfiles, available in two versions: **fullsize** and **downsized**.

For each entity, the code reads these catfiles and computes, for every return period from 1 to 2,000 years, the following metrics:

- **AEP**: annual loss (sum of the events of the year) at the return period;
- **OEP**: largest event of the year at the return period;
- **TVaR_AEP**: average of the annual losses beyond the AEP;
- **TVaR_OEP**: average of the largest annual events beyond the OEP.

The results are summarised in an Excel workbook, with one sheet per entity and the catfiles side by side, so that runs can be compared to assess convergence.

---

## Folder structure

```
py_kpi_report/
├── main.py                  # entry point: run parameters and pipeline launch
├── merge_group.py           # separate step: builds the GROUP entity folder (run before main.py)
├── requirements.txt         # dependencies (numpy, pandas, openpyxl)
├── README.md
└── kpi_report/              # computation package
    ├── __init__.py          # classes exposed by the package
    ├── config.py            # constants (return periods, folder layout) and fullsize / downsized modes
    ├── pipeline.py          # orchestration: parameter checks, loop over entities, export
    ├── entity.py            # KPI tables of all the catfiles of one entity
    ├── reader.py            # reading and checking a catfile, building its AEP / OEP strips
    ├── metrics.py           # AEP / OEP / TVaR computation per return period
    ├── group.py             # GROUP catfiles: aggregation of the entities, seed by seed
    └── exporter.py          # Excel output
```

### Expected input layout

```
<root>/
├── FRA/                                          # entity folder (name = item of `entities`)
│   └── n1000000/                                 # simulation folder (name = item of `simus`)
│       └── YELT/
│           └── YELT_Central/
│               ├── YELT_full_size/               # fullsize mode
│               │   └── <...>YELT_full_size<...>.csv
│               └── YELT_downsized_final/         # downsized mode
│                   └── <subfolder>/              # `downsized_subdir`, or first subfolder in alphabetical order
│                       └── f2<...>pool_property<...>.csv
├── DEU/
│   └── ...
└── CHE/
    └── ...
```

- **Fullsize catfile**: any file matching `*YELT_full_size*.csv` in `YELT_full_size`. Columns `EVENTID`, `YEAR` and either `TOTAL_LOSS` or one or more LoB columns `LOSS_<LoB>` (e.g. `LOSS_LoB1`, `LOSS_LoB3`), which are summed. If `TOTAL_LOSS` is present, it is used and the LoB columns are ignored.
- **Downsized catfile**: any file matching `f2*pool_property*.csv` in a subfolder of `YELT_downsized_final`: the one given by `downsized_subdir`, or by default the first subfolder in alphabetical order. Columns `EVENTID`, `YEAR`, `Loss`.
- Column names are case-sensitive. Other columns are ignored and not loaded.
- Years must be between 1 and the number of simulated years (`nbsimu` in fullsize, 50,000 in downsized). A year without events counts as 0.

### Input checks

The run stops with an explicit error, rather than producing wrong figures, when:
- a catfile folder or the `downsized_subdir` folder does not exist, or `YELT_downsized_final` has no subfolder;
- a folder contains no catfile matching the mode pattern;
- a catfile lacks `EVENTID` or `YEAR`, or has no loss column (the message lists the expected and found columns);
- in `merge_group.py`: `entities` contains the group name, the entities do not have the same seeds in a simulation folder, or two catfiles of a folder map to the same seed;
- a catfile contains a year outside 1..`n_years`;
- two entities give the same sheet name, or an entity is named `Parameters`.

A warning is printed, and the run continues, when:
- `YELT_downsized_final` contains several subfolders and `downsized_subdir` is not set (the subfolders are listed, and the one used is named);
- the last year with an event in a catfile is at most half of `n_years`, which suggests a wrong `n_years`;
- in fullsize mode, `n_years` differs from `nbsimu`;
- a catfile contains no event.

---

## User guide

1. **Install the dependencies.** Run `pip install -r requirements.txt`. `main.py` also installs any missing packages automatically at startup.
2. **Set the parameters** in [main.py](main.py):

   | Parameter | Purpose |
   |---|---|
   | `root` | Root folder of the runs (contains one folder per entity). |
   | `output_dir` | Output folder of the Excel file. |
   | `entities` | Entities to process, e.g. `["CHE", "DEU", "FRA"]`. One sheet is created per entity. |
   | `nbsimu` | Number of simulations of the run, set at the top of the `__main__` block. It gives the simulation folder read (`simus = [f"n{nbsimu}"]`, e.g. `n1000000`), the number of years in fullsize (`n_years = nbsimu`) and the `_1m` suffix of the output file name when it is `1000000`. |
   | `mode` | `"fullsize"` or `"downsized"`, set at the top of the `__main__` block: which catfiles are read (see [config.py](kpi_report/config.py)). |
   | `report_name` | Prefix of the output file name, e.g. `summary_CFHZ`. |
   | `n_years` | Number of simulated years used to build the strips. In `main.py`: `nbsimu` in fullsize, `None` in downsized, which uses the value of [config.py](kpi_report/config.py) (50,000). |
   | `downsized_subdir` | Optional, downsized mode only. Name of the subfolder of `YELT_downsized_final` to read. If `None`, the first subfolder in alphabetical order is used. |

3. **Run the computation**: `python main.py`.
4. **Collect the output** in `output_dir`:

   | File | Content |
   |---|---|
   | `<report_name>[_1m][_downsized].xlsx` | One sheet per entity (name truncated to 31 characters). For each catfile, a block of 5 columns: row 1 holds the label `<simu> \| <catfile name>`, row 2 the headers `RP`, `AEP`, `OEP`, `TVaR_AEP`, `TVaR_OEP`, then one row per return period from 1 to 2,000. Blocks are separated by an empty column. A last sheet, `Parameters`, records the run parameters (date, folders, mode, `n_years`, `nbsimu`, entities, simus, `downsized_subdir`) and, for each catfile read, its entity, simulation, name, number of events, last year with an event and full path. |

   Example: `summary_CFHZ_1m_downsized.xlsx` for `report_name="summary_CFHZ"`, `nbsimu=1000000`, `mode="downsized"`.

5. **Order of the blocks.** Blocks appear in the order of `simus`, then in alphabetical order of the catfile names within each simulation folder. Two catfiles with the same name in different simulation folders give two separate blocks.

### GROUP folder (`merge_group.py`)

`merge_group.py` is a separate step, independent of the report. It writes a `GROUP` entity folder in `root`, with the same layout as the other entities:

```
<root>/GROUP/<simu>/YELT/YELT_Central/YELT_full_size/GROUP_<...>.csv              # fullsize
<root>/GROUP/<simu>/YELT/YELT_Central/YELT_downsized_final/<subfolder>/<...>.csv  # downsized
```

1. Set its parameters at the bottom of [merge_group.py](merge_group.py):

   | Parameter | Purpose |
   |---|---|
   | `root` | Root folder of the runs (same as in `main.py`). |
   | `entities` | Entities to aggregate. |
   | `nbsimu` | Number of simulations: the folder aggregated is `n<nbsimu>` (`simus = [f"n{nbsimu}"]`). |
   | `modes` | Catfiles to aggregate: `["fullsize", "downsized"]` by default. |
   | `group_name` | Name of the folder created, `"GROUP"` by default. Must not be in `entities`. |
   | `downsized_subdir` | Same as in `main.py`. |

2. Run `python merge_group.py`.
3. To get a `GROUP` sheet in the report, add `"GROUP"` to `entities` in `main.py` and run `python main.py`. `GROUP` is then read like any other entity.

How the group catfiles are built:
- **Seeds.** In each catfile folder, the catfile without suffix is seed 0 and the catfile with suffix `_x` is seed x. A name counts as suffixed only if the same name without `_x` exists in the folder. All entities must have the same seeds.
- **Aggregation.** For each seed, the catfiles of all entities are read. The loss columns of each row are summed (all LoBs of the entity in fullsize; `Loss` in downsized, other columns ignored). The rows are then stacked and summed by `(YEAR, EVENTID)`. The annual losses (AEP) are the same as with a plain concatenation. An event that hits several entities counts as one event for the OEP.
- **Group catfile.** Columns `YEAR`, `EVENTID`, then `LOSS_LoB1` and `TOTAL_LOSS` in fullsize (a single LoB, equal to the total), or `Loss` in downsized. The file name is the one of the first entity's catfile for that seed, with the entity name replaced by the group name. In downsized mode, the subfolder has the name of the first entity's subfolder.
- **Rerun.** Each run deletes the group catfiles matching the mode pattern in the output folder before writing new ones, so old seeds are not mixed in.

---

## Code description

### `main.py`
Entry point. It checks that `numpy`, `pandas` and `openpyxl` are installed and installs any that are missing. `nbsimu` and `mode` are set at the top of the `__main__` block; the simulation folder and, in fullsize, `n_years` are derived from `nbsimu`. It then builds a `KpiReportPipeline` with the run parameters and calls `.run()`. Warnings are printed through Python's `logging` module.

### `kpi_report/config.py`
Global constants:
- `RETURN_PERIODS = range(1, 2001)`: return periods for which the metrics are computed.
- `YELT_ROOT = "YELT/YELT_Central"`: path of the YELT folders inside a simulation folder.
- `NBSIMU_1M = 1000000`: value of `nbsimu` that adds the `_1m` suffix to the report name.
- `ModeConfig` and `MODES`: description of each mode.

  | Mode | `folder` | `pattern` | `loss_col` | `n_years` | `descend_first_dir` | `suffix` | `lob_prefix` |
  |---|---|---|---|---|---|---|---|
  | `fullsize` | `YELT_full_size` | `*YELT_full_size*.csv` | `TOTAL_LOSS` | `None` (= `nbsimu`) | `False` | none | `LOSS_` |
  | `downsized` | `YELT_downsized_final` | `f2*pool_property*.csv` | `Loss` | 50,000 | `True` | `_downsized` | none |

### `kpi_report/pipeline.py` — `KpiReportPipeline`
Orchestrates the full run:
- `n_years` is the value passed, otherwise the mode value, otherwise `nbsimu` (fullsize).
- `_check_parameters` runs at construction: sheet names must be unique and must not be `Parameters`; in fullsize mode, a warning is printed if `n_years` differs from `nbsimu`.
- `output_path` builds the output file name: `<report_name>`, then `_1m` if `nbsimu = 1000000`, then the mode suffix.
- `run()`:
  1. for each entity, runs `EntityReport.build()` and stores its list of `CatfileKpi` under the entity code;
  2. builds the parameters table (`_parameters_table`) and the table of catfiles read (`_files_table`);
  3. writes everything to the Excel workbook with `ExcelExporter`.

### `kpi_report/entity.py` — `EntityReport`, `CatfileKpi`
- `CatfileKpi` holds the result for one catfile: simulation, path, KPI table, number of events and last year with an event. Its `label` (`<simu> | <catfile name>`) is written above the block in the Excel sheet.
- `EntityReport` computes the KPI tables of one entity:
  - `code` is the entity name without `/`. It is used as the sheet name.
  - `_catfile_dir` returns `<root>/<entity>/<simu>/YELT/YELT_Central/<mode folder>` and raises an error if it does not exist. In downsized mode, it goes down into a subfolder (`_subdir`): `downsized_subdir` if given, otherwise the first subfolder in alphabetical order, with a warning if there are several. Files are not taken into account when looking for subfolders.
  - `_catfiles` lists the catfiles of the folder matching the mode pattern, in alphabetical order, and raises an error if there are none.
  - `build` reads each catfile of each simulation, computes its KPI table with `exceedance_table` and returns the list of `CatfileKpi`, in the order of `simus` then of file names.

### `kpi_report/reader.py` — `CatfileReader`
Reads one catfile and builds its strips over years 1 to `n_years`.
- `loss_columns` checks the header and returns the loss columns: `loss_col` if present, otherwise the columns starting with `lob_prefix` (fullsize LoBs). It is shared with `GroupBuilder`.
- `event_losses` reads only the `EVENTID`, `YEAR` and loss columns, and builds `eventid`, `year` and `total` (sum of the loss columns). The file is read only once. `_check_years` then raises an error if a year is outside 1..`n_years`, and prints a warning if the last year with an event is at most half of `n_years`.
- `n_events` and `last_year` describe the catfile for the `Parameters` sheet.
- `annual_losses` returns the **AEP strip**: for each year, the sum of the event losses.
- `max_event_losses` returns the **OEP strip**: for each year, the largest event loss.
- In both strips, a year without events is 0.

### `kpi_report/metrics.py`
- `exceedance_table` sorts the AEP and OEP strips. For each return period RP, with `k = ceil(n_years / RP)`:
  - `AEP` and `OEP` are the k-th largest values of their strip;
  - `TVaR_AEP` and `TVaR_OEP` are the averages of the k largest values.

  Example with 50,000 years: for RP = 200, k = 250, so the AEP200 is the 250th largest annual loss and the TVaR200 is the average of the 250 largest. For RP = 1, k = n_years: the AEP is the smallest annual loss and the TVaR is the mean (AAL).

### `kpi_report/group.py` — `GroupBuilder`
- `seed_catfiles` maps each catfile of a folder to its seed (0 without suffix, x for the suffix `_x`), and raises an error if two files map to the same seed.
- `GroupBuilder.build` reuses `EntityReport` to list the catfiles of each entity, checks that all entities have the same seeds, and for each seed writes the aggregated catfile into the `GROUP` folder.

### `kpi_report/exporter.py` — `ExcelExporter`
Writes a workbook with one sheet per entity, then the `Parameters` sheet. Sheet names are truncated to 31 characters (Excel limit), and the index is not written. In an entity sheet, each catfile occupies a block of `BLOCK_WIDTH = 6` columns (5 KPI columns and 1 empty column): the label in bold on row 1, the KPI table from row 2.
