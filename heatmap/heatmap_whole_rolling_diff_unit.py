"""
Input a TXT file to display a heatmap and a heatmap of a specified region.
Also displays 3x3 and 6x6 rolling average versions of both heatmaps.
Heatmaps use adaptive color units.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.ndimage import uniform_filter
import json
import os


def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        raise


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


def create_heatmap(ax, data, title, cmap,
                   fontsize=10, show_values=True, mark_area=None):
    """
    Create heatmap (auto-adjusted color range)
    :param ax: Axis object
    :param data: 2D data array
    :param title: Title
    :param cmap: Colormap
    :param fontsize: Font size
    :param show_values: Whether to show values
    :param mark_area: Region to mark (x_start, y_start, width, height)
    """
    # Create heatmap (auto-determine vmin/vmax)
    im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(r'Co loading (μg cm$^{-2}$)', rotation=270, labelpad=20, fontsize=fontsize)

    # Mark specified area
    if mark_area:
        x, y, w, h = mark_area
        rect = Rectangle((x - 0.5, y - 0.5), w, h,
                         linewidth=2, edgecolor='yellow', facecolor='none')
        ax.add_patch(rect)

    # Add value labels
    if show_values and data.size <= 400:  # Show values for up to 20x20
        median_val = np.median(data)
        for (j, i), val in np.ndenumerate(data):
            ax.text(i, j, f"{val:.1f}",
                    ha="center", va="center",
                    color="white" if val > median_val else "black",
                    fontsize=fontsize - 1, fontweight='bold')

    # Set title and labels
    ax.set_title(title, pad=15, fontsize=fontsize + 2)
    ax.set_xlabel('Columns', fontsize=fontsize)
    ax.set_ylabel('Rows', fontsize=fontsize)
    ax.tick_params(axis='both', which='major', labelsize=fontsize - 1)


def plot_all_heatmaps(data, region_coords, output_path=None):
    """Plot all 6 heatmaps (each with independent color scales)"""
    # Create unified colormap
    colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
              "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
    cmap = LinearSegmentedColormap.from_list("multi_phase", colors, N=256)

    # Calculate rolling averages
    data_3x3 = apply_rolling_average(data, 3)
    data_6x6 = apply_rolling_average(data, 6)

    # Extract region data
    x, y, w, h = region_coords
    region_data = data[y:y + h, x:x + w]
    region_3x3 = data_3x3[y:y + h, x:x + w]
    region_6x6 = data_6x6[y:y + h, x:x + w]

    # Create figure (2 rows, 3 columns)
    plt.rcParams['figure.dpi'] = 100
    fig, axs = plt.subplots(2, 3, figsize=(18, 12))

    # First row: full heatmaps
    create_heatmap(axs[0, 0], data, "Original Data", cmap,
                   mark_area=region_coords)
    create_heatmap(axs[0, 1], data_3x3, "3×3 Rolling Average", cmap,
                   mark_area=region_coords)
    create_heatmap(axs[0, 2], data_6x6, "6×6 Rolling Average", cmap,
                   mark_area=region_coords)

    # Second row: region zoom heatmaps
    create_heatmap(axs[1, 0], region_data,
                   f"Original Region ({w}×{h})", cmap,
                   show_values=True)
    create_heatmap(axs[1, 1], region_3x3,
                   f"3×3 Region ({w}×{h})", cmap,
                   show_values=True)
    create_heatmap(axs[1, 2], region_6x6,
                   f"6×6 Region ({w}×{h})", cmap,
                   show_values=True)

    plt.suptitle("Cobalt Loading Analysis with Independent Color Scales", y=1.02, fontsize=16)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    plt.show()


if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config()
        sep = config.get('sep', '\t')  # Default to tab if not specified
        filepath = config['filepath']
        custom_region = tuple(config['region'])  # Convert list to tuple

        # Read data
        data = read_data(filepath, sep)
        print(f"Data loaded: {data.shape} matrix")
        print(f"Original range: {np.min(data):.2f} to {np.max(data):.2f} μg/cm²")

        # Calculate and print ranges
        data_3x3 = apply_rolling_average(data, 3)
        data_6x6 = apply_rolling_average(data, 6)
        print(f"3x3 range: {np.min(data_3x3):.2f} to {np.max(data_3x3):.2f} μg/cm²")
        print(f"6x6 range: {np.min(data_6x6):.2f} to {np.max(data_6x6):.2f} μg/cm²")

        # Generate output filename based on input filename
        base_name = os.path.splitext(config["filepath"])[0]
        output_path = f"{base_name}-heatmap-wdu.png"

        # Plot all heatmaps
        plot_all_heatmaps(data, custom_region, output_path)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Processing error: {str(e)}")
