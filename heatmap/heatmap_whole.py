"""
Display a heatmap from a TXT file along with a heatmap of a specified region.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import json
import os

def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file) as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_file}")
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

def create_heatmap(ax, data, title, fontsize=10,
                   show_values=True, mark_area=None):
    """
    Create heatmap and mark specified region
    :param ax: Axis object
    :param data: 2D data array
    :param title: Title
    :param fontsize: Font size
    :param show_values: Whether to show values
    :param mark_area: Region to mark (x_start, y_start, width, height)
    """
    # Multi-color gradient colormap
    colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
              "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
    cmap = LinearSegmentedColormap.from_list("multi_colormap", colors, N=256)

    # Create heatmap (origin='upper' ensures y-axis points downward)
    im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(r'Co loading (μg cm$^{-2}$)', rotation=270, labelpad=20, fontsize=fontsize)

    # Mark specified region (using pixel coordinates)
    if mark_area:
        x, y, w, h = mark_area
        rect = Rectangle((x - 0.5, y - 0.5), w, h,  # -0.5 aligns with pixel center
                         linewidth=2, edgecolor='yellow', facecolor='none')
        ax.add_patch(rect)

    # Add value labels
    if show_values and data.size <= 400:  # Show values for up to 20x20 grids
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

def plot_marked_region_heatmaps(data, region_coords=None, title="Data Analysis",output_path=None):
    """
    Display heatmaps vertically - top shows full heatmap with marked region,
    bottom shows zoomed region.
    :param data: 2D data array
    :param region_coords: Region coordinates (x_start, y_start, width, height)
    :param title: Chart title
    """
    # Set default region (bottom-right quarter)
    if region_coords is None:
        h, w = data.shape
        region_h, region_w = max(3, h // 4), max(3, w // 4)
        region_coords = (w - region_w, h - region_h, region_w, region_h)

    # Extract region data
    x, y, w, h = region_coords
    region_data = data[y:y + h, x:x + w]

    # Create figure
    fig = plt.figure(figsize=(10, 12))

    # ========== Top: Full heatmap with marked region ==========
    ax1 = fig.add_subplot(2, 1, 1)
    create_heatmap(ax1, data, "Full Heatmap with Marked Region",
                   show_values=False, mark_area=region_coords)

    # ========== Bottom: Zoomed region heatmap ==========
    ax2 = fig.add_subplot(2, 1, 2)
    create_heatmap(ax2, region_data,
                   f"Zoomed Region: {w}×{h} at ({x},{y})",
                   show_values=True)

    # Adjust layout
    plt.suptitle(title, y=1.0, fontsize=14)
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

        # Generate output filename based on input filename
        base_name = os.path.splitext(config["filepath"])[0]
        output_path = f"{base_name}-heatmap-w.png"

        # Display custom region
        plot_marked_region_heatmaps(data, custom_region,
                                    title="Custom Region Analysis",output_path=output_path)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Processing error: {str(e)}")