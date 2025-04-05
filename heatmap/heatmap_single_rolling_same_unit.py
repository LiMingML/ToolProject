"""
Display three heatmaps from a TXT file with unified color scaling:
1. Original heatmap
2. 3x3 rolling average heatmap
3. 6x6 rolling average heatmap
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import uniform_filter
import json
import os


def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    defaults = {
        "sep": "\t",
        "filepath": "data/XRF_data_2.txt.txt"
    }
    try:
        with open(config_path) as f:
            config = json.load(f)
        return {**defaults, **config}
    except FileNotFoundError:
        print(f"Using default configuration (config file not found)")
        return defaults


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


def create_heatmap(ax, data, title, cmap, vmin, vmax, fontsize=10):
    """Create standardized heatmap with unified color scale"""
    im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper',
                   vmin=vmin, vmax=vmax)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Intensity', rotation=270, labelpad=20, fontsize=fontsize)

    ax.set_title(title, pad=15, fontsize=fontsize + 2)
    ax.set_xlabel('Columns', fontsize=fontsize)
    ax.set_ylabel('Rows', fontsize=fontsize)
    ax.tick_params(axis='both', which='major', labelsize=fontsize - 1)


def plot_unified_scale_heatmaps(data,output_path=None):
    """Display three heatmaps side-by-side with unified color scaling"""
    # Create unified colormap
    colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
              "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
    cmap = LinearSegmentedColormap.from_list("multi_phase", colors, N=256)

    # Calculate global min/max for consistent scaling
    global_min = np.min(data)
    global_max = np.max(data)

    # Calculate rolling averages
    data_3x3 = apply_rolling_average(data, 3)
    data_6x6 = apply_rolling_average(data, 6)

    # Create figure
    plt.rcParams['figure.dpi'] = 120  # Slightly higher DPI
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

    # Plot heatmaps
    create_heatmap(ax1, data, "Original Data", cmap, global_min, global_max)
    create_heatmap(ax2, data_3x3, "3×3 Rolling Average", cmap, global_min, global_max)
    create_heatmap(ax3, data_6x6, "6×6 Rolling Average", cmap, global_min, global_max)

    plt.suptitle("Cobalt Loading Analysis - Unified Color Scale", y=1.05, fontsize=16)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    plt.show()


if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config()

        # Read and process data
        data = read_data(config["filepath"], config["sep"])
        print(f"Data loaded successfully. Shape: {data.shape}")
        print(f"Global range: {np.min(data):.2f} to {np.max(data):.2f}")

        # Generate output filename based on input filename
        base_name = os.path.splitext(config["filepath"])[0]
        output_path = f"{base_name}-heatmap-ssu.png"

        # Generate visualizations
        plot_unified_scale_heatmaps(data,output_path=output_path)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Processing error: {str(e)}")