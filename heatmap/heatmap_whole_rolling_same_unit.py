"""
Input a TXT file to display a heatmap and a heatmap of a specified region.
Also displays 3x3 and 6x6 rolling average versions of both heatmaps.
The first three and last three plots use consistent color scales.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.ndimage import uniform_filter
import json
import os


def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    default_config = {
        "sep": "\t",
        "filepath": "data/Co_loading_calculated-after HNO3.txt",
        "region": [140, 120, 85, 100]
    }

    try:
        with open(config_file) as f:
            config = json.load(f)
        # Merge with defaults
        return {**default_config, **config}
    except FileNotFoundError:
        print(f"Config file {config_file} not found, using defaults")
        return default_config


def read_data(filepath, sep):
    """Read text data"""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(("#", "Original", "Columns")):
                row = [float(x.strip()) for x in line.split(sep) if x.strip()]
                if row:
                    data.append(row)
    return np.array(data)


def apply_rolling_average(data, window_size):
    """Apply rolling average filter"""
    return uniform_filter(data, size=window_size, mode='nearest')


def create_heatmap(ax, data, title, cmap, vmin=None, vmax=None,
                   fontsize=10, show_values=True, mark_area=None):
    """
    Create heatmap (with customizable color range)
    :param ax: Axis object
    :param data: 2D data array
    :param title: Title
    :param cmap: Colormap
    :param vmin: Minimum color value
    :param vmax: Maximum color value
    :param fontsize: Font size
    :param show_values: Whether to display values
    :param mark_area: Region to mark (x_start, y_start, width, height)
    """
    im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper',
                   vmin=vmin, vmax=vmax)

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(r'Co loading (μg cm$^{-2}$)', rotation=270, labelpad=20, fontsize=fontsize)

    if mark_area:
        x, y, w, h = mark_area
        rect = Rectangle((x - 0.5, y - 0.5), w, h,
                         linewidth=2, edgecolor='yellow', facecolor='none')
        ax.add_patch(rect)

    if show_values and data.size <= 400:  # Show values for up to 20x20 grids
        median_val = np.median(data)
        for (j, i), val in np.ndenumerate(data):
            ax.text(i, j, f"{val:.1f}",
                    ha="center", va="center",
                    color="white" if val > median_val else "black",
                    fontsize=fontsize - 1, fontweight='bold')

    ax.set_title(title, pad=15, fontsize=fontsize + 2)
    ax.set_xlabel('Columns', fontsize=fontsize)
    ax.set_ylabel('Rows', fontsize=fontsize)
    ax.tick_params(axis='both', which='major', labelsize=fontsize - 1)


def plot_grouped_heatmaps(data, region_coords, output_path=None):
    """Plot grouped heatmaps (consistent scales for first three and last three plots)"""
    colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
              "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
    cmap = LinearSegmentedColormap.from_list("multi_phase", colors, N=256)

    data_3x3 = apply_rolling_average(data, 3)
    data_6x6 = apply_rolling_average(data, 6)

    global_min = np.min(data)
    global_max = np.max(data)

    x, y, w, h = region_coords
    region_data = data[y:y + h, x:x + w]
    region_3x3 = data_3x3[y:y + h, x:x + w]
    region_6x6 = data_6x6[y:y + h, x:x + w]

    region_min = min(np.min(region_data), np.min(region_3x3), np.min(region_6x6))
    region_max = max(np.max(region_data), np.max(region_3x3), np.max(region_6x6))

    plt.rcParams['figure.dpi'] = 100
    fig, axs = plt.subplots(2, 3, figsize=(18, 12))

    create_heatmap(axs[0, 0], data, "Original Data", cmap,
                   global_min, global_max, mark_area=region_coords)
    create_heatmap(axs[0, 1], data_3x3, "3×3 Rolling Average", cmap,
                   global_min, global_max, mark_area=region_coords)
    create_heatmap(axs[0, 2], data_6x6, "6×6 Rolling Average", cmap,
                   global_min, global_max, mark_area=region_coords)

    create_heatmap(axs[1, 0], region_data,
                   f"Original Region ({w}×{h})", cmap,
                   region_min, region_max, show_values=True)
    create_heatmap(axs[1, 1], region_3x3,
                   f"3×3 Region ({w}×{h})", cmap,
                   region_min, region_max, show_values=True)
    create_heatmap(axs[1, 2], region_6x6,
                   f"6×6 Region ({w}×{h})", cmap,
                   region_min, region_max, show_values=True)

    plt.suptitle("Cobalt Loading Analysis with Grouped Color Scales", y=1.02, fontsize=16)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path)
    plt.show()


if __name__ == "__main__":
    config = load_config()

    try:
        data = read_data(config["filepath"], config["sep"])
        print(f"Data loaded: {data.shape} matrix")
        print(f"Global range: {np.min(data):.2f} to {np.max(data):.2f} μg/cm²")

        # Generate output filename based on input filename
        base_name = os.path.splitext(config["filepath"])[0]
        output_path = f"{base_name}-heatmap-wsu.png"

        plot_grouped_heatmaps(data, config["region"], output_path)

    except FileNotFoundError:
        print(f"Error: File not found at {config['filepath']}")
    except Exception as e:
        print(f"Processing error: {str(e)}")