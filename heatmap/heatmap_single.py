"""
Display original heatmap from a TXT file.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
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

def create_heatmap(data, title="Original Data", fontsize=10,output_path=None):
    """Create standardized heatmap"""
    # Create multi-color gradient colormap
    colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
              "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
    cmap = LinearSegmentedColormap.from_list("multi_phase", colors, N=256)

    # Create figure
    plt.rcParams['figure.dpi'] = 100
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create heatmap
    im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper')
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label(r'Co loading (μg cm$^{-2}$)', rotation=270, labelpad=20, fontsize=fontsize)

    # Set title and labels
    ax.set_title(title, pad=15, fontsize=fontsize + 2)
    ax.set_xlabel('Columns', fontsize=fontsize)
    ax.set_ylabel('Rows', fontsize=fontsize)
    ax.tick_params(axis='both', which='major', labelsize=fontsize - 1)

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

        # Read data
        data = read_data(filepath, sep)
        print(f"Data loaded successfully. Shape: {data.shape}")
        print(f"Data range: {np.min(data):.2f} to {np.max(data):.2f}")

        # Generate output filename based on input filename
        base_name = os.path.splitext(config["filepath"])[0]
        output_path = f"{base_name}-heatmap-s.png"

        # Plot original heatmap
        create_heatmap(data,output_path=output_path)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Processing error: {str(e)}")