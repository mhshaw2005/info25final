import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- File Configuration ---
JSON_FILE_PATH = 'USNP_data.json'

# --- Analysis Configuration ---
TARGET_YEARS = ['2010', '2018', '2019', '2020']
PRIMARY_FILTER_YEAR = '2018'

# --- General Plotting Configuration ---
FIGURE_SIZE = (12, 8)
PLOT_PALETTE = "viridis"
BASE_SUBTITLE = "Analysis excludes parks with incomplete data for the specified years."

# --- Plot-Specific Settings ---
# 1. Line Plot (Average)
LINEPLOT_FILENAME = 'Plot_line_average.png'
LINEPLOT_TITLE = "Average National Park Visitors (2010-2020)"

# 2. Violin Plot
VIOLINPLOT_FILENAME = 'Plot_violin.png'
VIOLINPLOT_TITLE = "Distribution of National Park Visitors (Violin Plot)"

# 3. Box Plot
BOXPLOT_FILENAME = 'Plot_box.png'
BOXPLOT_TITLE = "Distribution of National Park Visitors (Box Plot)"

# 4. Combined Box & Strip Plot
COMBOPLOT_FILENAME = 'Plot_combo_box_strip.png'
COMBOPLOT_TITLE = "Distribution of National Park Visitors (Box + Strip Plot)"
STRIPPLOT_DOT_COLOR = '#003049'
STRIPPLOT_DOT_SIZE = 5
STRIPPLOT_DOT_ALPHA = 0.6

# --- Output Configuration ---
OUTPUT_DPI = 300


def load_park_data(filepath):
    """Loads park data from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded data from '{filepath}'.")
        return data['parks']
    except FileNotFoundError:
        print(f"ERROR: The file '{filepath}' was not found.")
        return None
    except (json.JSONDecodeError, KeyError):
        print(f"ERROR: The file '{filepath}' is not a valid JSON or is missing the 'parks' key.")
        return None

def apply_common_plot_formatting(fig, ax, title, subtitle):
    """Applies common formatting to a plot axis."""
    ax.set_title(title, fontsize=16, weight='bold', pad=20)
    fig.suptitle(subtitle, fontsize=10, y=0.92)
    ax.set_ylabel("Number of Visitors", fontsize=12)
    ax.set_xlabel("Year", fontsize=12)
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.tight_layout(rect=[0, 0, 1, 0.9])

def create_line_plot(dataframe, title, subtitle, filename):
    """Creates and saves a line plot of the average."""
    print(f"Generating Line Plot (Linear Scale)...")
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    # Calculate mean for plotting
    mean_data = dataframe.groupby('Year')['Visitors'].mean().reset_index()
    
    sns.lineplot(x='Year', y='Visitors', data=mean_data, ax=ax,
                 marker='o', markersize=8, markeredgecolor='black')
    
    ax.set_ylim(bottom=0)
    ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    full_subtitle = f"{subtitle} (Linear Scale)"
    apply_common_plot_formatting(fig, ax, title, full_subtitle)
    fig.savefig(filename, dpi=OUTPUT_DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved to '{filename}'")

def create_violin_plot(dataframe, title, subtitle, filename):
    """Creates and saves a violin plot on a linear scale."""
    print(f"Generating Violin Plot (Linear Scale)...")
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    sns.violinplot(x='Year', y='Visitors', data=dataframe, ax=ax,
                   inner='quartile', palette=PLOT_PALETTE, cut=0,
                   hue='Year', legend=False)
                   
    ax.set_ylim(bottom=0)
    ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    full_subtitle = f"{subtitle} (Linear Scale)"
    apply_common_plot_formatting(fig, ax, title, full_subtitle)
    fig.savefig(filename, dpi=OUTPUT_DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved to '{filename}'")

def create_box_plot(dataframe, title, subtitle, filename):
    """Creates and saves a box plot on a log scale."""
    print(f"Generating Box Plot (Log Scale)...")
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    sns.boxplot(x='Year', y='Visitors', data=dataframe, ax=ax,
                palette=PLOT_PALETTE, hue='Year', legend=False)
                
    ax.set_yscale('log')
    ax.get_yaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    full_subtitle = f"{subtitle} (Log Scale)"
    apply_common_plot_formatting(fig, ax, title, full_subtitle)
    fig.savefig(filename, dpi=OUTPUT_DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved to '{filename}'")

def create_combo_plot(dataframe, title, subtitle, filename):
    """Creates and saves a combined box and strip plot on a log scale."""
    print(f"Generating Combined Box & Strip Plot (Log Scale)...")
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    
    sns.boxplot(x='Year', y='Visitors', data=dataframe, ax=ax,
                palette=PLOT_PALETTE, showfliers=False,
                hue='Year', legend=False)
    sns.stripplot(x='Year', y='Visitors', data=dataframe, ax=ax,
                  jitter=True, color=STRIPPLOT_DOT_COLOR,
                  size=STRIPPLOT_DOT_SIZE, alpha=STRIPPLOT_DOT_ALPHA)
                  
    ax.set_yscale('log')
    ax.get_yaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    full_subtitle = f"{subtitle} (Log Scale)"
    apply_common_plot_formatting(fig, ax, title, full_subtitle)
    fig.savefig(filename, dpi=OUTPUT_DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"-> Saved to '{filename}'")

def main():
    """Main function to load, process, and generate all plots."""
    parks_data = load_park_data(JSON_FILE_PATH)
    if not parks_data: return

    parks_to_exclude = {p['name'] for p in parks_data if PRIMARY_FILTER_YEAR not in {vh['year'] for vh in p['visitor_history']}}
    print("-" * 50)
    print(f"Identified {len(parks_to_exclude)} parks to exclude.")
    filtered_parks = [p for p in parks_data if p['name'] not in parks_to_exclude]
    print(f"Proceeding with analysis for {len(filtered_parks)} parks.")

    if any(not set(TARGET_YEARS).issubset({vh['year'] for vh in p['visitor_history']}) for p in filtered_parks):
        print("\nFATAL ERROR: DATA INCONSISTENCY DETECTED!\n")
        return

    print("Data integrity check passed.")
    print("-" * 50)

    long_form_data = []
    for park in filtered_parks:
        park_visitor_map = {entry['year']: entry['visitors'] for entry in park['visitor_history']}
        for year in TARGET_YEARS:
            long_form_data.append({'Park': park['name'], 'Year': year, 'Visitors': park_visitor_map[year]})
    df = pd.DataFrame(long_form_data).sort_values('Year')

    # Generate all four plots
    create_line_plot(df, LINEPLOT_TITLE, BASE_SUBTITLE, LINEPLOT_FILENAME)
    create_violin_plot(df, VIOLINPLOT_TITLE, BASE_SUBTITLE, VIOLINPLOT_FILENAME)
    create_box_plot(df, BOXPLOT_TITLE, BASE_SUBTITLE, BOXPLOT_FILENAME)
    create_combo_plot(df, COMBOPLOT_TITLE, BASE_SUBTITLE, COMBOPLOT_FILENAME)
    
    print("-" * 50)
    print("All plots generated successfully.")

if __name__ == "__main__":
    main()
