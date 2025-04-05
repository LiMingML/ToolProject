"""
Combined Heatmap Visualization Tool with Interactive GUI

Features:
1. Six buttons to generate different heatmap visualizations
2. Display and edit configuration file
3. File browser for selecting data file
4. JSON validation and saving
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.ndimage import uniform_filter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt


class HeatmapVisualizer:
    """Core heatmap visualization functions combining all six original scripts"""

    @staticmethod
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

    @staticmethod
    def apply_rolling_average(data, window_size):
        """Apply rolling average filter"""
        return uniform_filter(data, size=window_size, mode='nearest')

    @staticmethod
    def create_colormap():
        """Create unified colormap"""
        colors = ["#00008B", "#0000FF", "#0080FF", "#00FFFF",
                  "#80FF80", "#FFFF00", "#FF8000", "#FF0000", "#800000"]
        return LinearSegmentedColormap.from_list("multi_phase", colors, N=256)

    @staticmethod
    def create_heatmap(ax, data, title, cmap, vmin=None, vmax=None,
                       fontsize=10, show_values=True, mark_area=None, unit='Co loading'):
        """
        Create standardized heatmap
        """
        im = ax.imshow(data, cmap=cmap, interpolation='nearest', origin='upper',
                       vmin=vmin, vmax=vmax)

        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        unit_label = r'Intensity' if unit == 'Intensity' else r'Co loading (μg cm$^{-2}$)'
        cbar.set_label(unit_label, rotation=270, labelpad=20, fontsize=fontsize)

        if mark_area:
            x, y, w, h = mark_area
            rect = Rectangle((x - 0.5, y - 0.5), w, h,
                             linewidth=2, edgecolor='yellow', facecolor='none')
            ax.add_patch(rect)

        if show_values and data.size <= 400:
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

    # Visualization functions for each of the six original scripts
    def visualize_single(self, config, output_path=None):
        """Single heatmap visualization"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        cmap = self.create_colormap()

        plt.rcParams['figure.dpi'] = 100
        fig, ax = plt.subplots(figsize=(8, 6))
        self.create_heatmap(ax, data, "Original Data", cmap)

        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def visualize_single_rolling_diff_unit(self, config, output_path=None):
        """Side-by-side heatmaps with different color units"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        cmap = self.create_colormap()

        data_3x3 = self.apply_rolling_average(data, 3)
        data_6x6 = self.apply_rolling_average(data, 6)

        plt.rcParams['figure.dpi'] = 100
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

        self.create_heatmap(ax1, data, "Original Data", cmap)
        self.create_heatmap(ax2, data_3x3, "3×3 Rolling Average", cmap)
        self.create_heatmap(ax3, data_6x6, "6×6 Rolling Average", cmap)

        plt.suptitle("Cobalt Loading Analysis - Side by Side Comparison",
                     y=1.05, fontsize=16)
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def visualize_single_rolling_same_unit(self, config, output_path=None):
        """Side-by-side heatmaps with same color units"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        cmap = self.create_colormap()

        global_min = np.min(data)
        global_max = np.max(data)

        data_3x3 = self.apply_rolling_average(data, 3)
        data_6x6 = self.apply_rolling_average(data, 6)

        plt.rcParams['figure.dpi'] = 120
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

        self.create_heatmap(ax1, data, "Original Data", cmap, global_min, global_max)
        self.create_heatmap(ax2, data_3x3, "3×3 Rolling Average", cmap, global_min, global_max)
        self.create_heatmap(ax3, data_6x6, "6×6 Rolling Average", cmap, global_min, global_max)

        plt.suptitle("Cobalt Loading Analysis - Unified Color Scale", y=1.05, fontsize=16)
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def visualize_whole(self, config, output_path=None):
        """Full heatmap with marked region"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        region_coords = tuple(config.get('region', self._get_default_region(data)))
        cmap = self.create_colormap()

        x, y, w, h = region_coords
        region_data = data[y:y + h, x:x + w]

        fig = plt.figure(figsize=(10, 12))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        self.create_heatmap(ax1, data, "Full Heatmap with Marked Region",
                            cmap, show_values=False, mark_area=region_coords)
        self.create_heatmap(ax2, region_data,
                            f"Zoomed Region: {w}×{h} at ({x},{y})",
                            cmap, show_values=True)

        plt.suptitle("Custom Region Analysis", y=1.0, fontsize=14)
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def visualize_whole_rolling_diff_unit(self, config, output_path=None):
        """All six heatmaps with independent color scales"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        region_coords = tuple(config.get('region', self._get_default_region(data)))
        cmap = self.create_colormap()

        data_3x3 = self.apply_rolling_average(data, 3)
        data_6x6 = self.apply_rolling_average(data, 6)

        x, y, w, h = region_coords
        region_data = data[y:y + h, x:x + w]
        region_3x3 = data_3x3[y:y + h, x:x + w]
        region_6x6 = data_6x6[y:y + h, x:x + w]

        plt.rcParams['figure.dpi'] = 100
        fig, axs = plt.subplots(2, 3, figsize=(18, 12))

        self.create_heatmap(axs[0, 0], data, "Original Data", cmap,
                            mark_area=region_coords)
        self.create_heatmap(axs[0, 1], data_3x3, "3×3 Rolling Average", cmap,
                            mark_area=region_coords)
        self.create_heatmap(axs[0, 2], data_6x6, "6×6 Rolling Average", cmap,
                            mark_area=region_coords)

        self.create_heatmap(axs[1, 0], region_data,
                            f"Original Region ({w}×{h})", cmap,
                            show_values=True)
        self.create_heatmap(axs[1, 1], region_3x3,
                            f"3×3 Region ({w}×{h})", cmap,
                            show_values=True)
        self.create_heatmap(axs[1, 2], region_6x6,
                            f"6×6 Region ({w}×{h})", cmap,
                            show_values=True)

        plt.suptitle("Cobalt Loading Analysis with Independent Color Scales",
                     y=1.02, fontsize=16)
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def visualize_whole_rolling_same_unit(self, config, output_path=None):
        """All six heatmaps with grouped color scales"""
        data = self.read_data(config['filepath'], config.get('sep', '\t'))
        region_coords = tuple(config.get('region', self._get_default_region(data)))
        cmap = self.create_colormap()

        data_3x3 = self.apply_rolling_average(data, 3)
        data_6x6 = self.apply_rolling_average(data, 6)

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

        self.create_heatmap(axs[0, 0], data, "Original Data", cmap,
                            global_min, global_max, mark_area=region_coords)
        self.create_heatmap(axs[0, 1], data_3x3, "3×3 Rolling Average", cmap,
                            global_min, global_max, mark_area=region_coords)
        self.create_heatmap(axs[0, 2], data_6x6, "6×6 Rolling Average", cmap,
                            global_min, global_max, mark_area=region_coords)

        self.create_heatmap(axs[1, 0], region_data,
                            f"Original Region ({w}×{h})", cmap,
                            region_min, region_max, show_values=True)
        self.create_heatmap(axs[1, 1], region_3x3,
                            f"3×3 Region ({w}×{h})", cmap,
                            region_min, region_max, show_values=True)
        self.create_heatmap(axs[1, 2], region_6x6,
                            f"6×6 Region ({w}×{h})", cmap,
                            region_min, region_max, show_values=True)

        plt.suptitle("Cobalt Loading Analysis with Grouped Color Scales",
                     y=1.02, fontsize=16)
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
        plt.show()

    def _get_default_region(self, data):
        """Get default region coordinates (bottom-right quarter)"""
        h, w = data.shape
        region_h, region_w = max(3, h // 4), max(3, w // 4)
        return (w - region_w, h - region_h, region_w, region_h)


class HeatmapGUI(QMainWindow):
    """PyQt5 GUI for the heatmap visualization tool"""

    def __init__(self):
        super().__init__()
        self.visualizer = HeatmapVisualizer()
        self.config_file = 'config.json'
        self.default_config = {
            "sep": "\t",
            "filepath": "data/Co_loading_calculated-after HNO3.txt",
            "region": [140, 120, 85, 100]
        }
        self.current_config = self.default_config.copy()

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('Heatmap Visualization Tool')
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Config display/edit area
        config_label = QLabel('Configuration:')
        self.config_edit = QTextEdit()
        self.config_edit.setAcceptRichText(False)
        self.config_edit.setPlaceholderText("Edit JSON configuration here...")
        main_layout.addWidget(config_label)
        main_layout.addWidget(self.config_edit)

        # Button row 1: File operations
        file_btn_layout = QHBoxLayout()

        self.load_btn = QPushButton('Load Config')
        self.load_btn.clicked.connect(self.load_config)
        file_btn_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton('Save Config')
        self.save_btn.clicked.connect(self.save_config)
        file_btn_layout.addWidget(self.save_btn)

        self.browse_btn = QPushButton('Browse Data File')
        self.browse_btn.clicked.connect(self.browse_data_file)
        file_btn_layout.addWidget(self.browse_btn)

        main_layout.addLayout(file_btn_layout)

        # Button row 2: Visualization options
        viz_btn_layout1 = QHBoxLayout()

        self.single_btn = QPushButton('Single Heatmap')
        self.single_btn.clicked.connect(lambda: self.run_visualization('single'))
        viz_btn_layout1.addWidget(self.single_btn)

        self.single_rolling_diff_btn = QPushButton('Single + Rolling (Diff Units)')
        self.single_rolling_diff_btn.clicked.connect(lambda: self.run_visualization('single_rolling_diff'))
        viz_btn_layout1.addWidget(self.single_rolling_diff_btn)

        self.single_rolling_same_btn = QPushButton('Single + Rolling (Same Units)')
        self.single_rolling_same_btn.clicked.connect(lambda: self.run_visualization('single_rolling_same'))
        viz_btn_layout1.addWidget(self.single_rolling_same_btn)

        main_layout.addLayout(viz_btn_layout1)

        # Button row 3: More visualization options
        viz_btn_layout2 = QHBoxLayout()

        self.whole_btn = QPushButton('Whole + Region')
        self.whole_btn.clicked.connect(lambda: self.run_visualization('whole'))
        viz_btn_layout2.addWidget(self.whole_btn)

        self.whole_rolling_diff_btn = QPushButton('Whole + Rolling (Diff Units)')
        self.whole_rolling_diff_btn.clicked.connect(lambda: self.run_visualization('whole_rolling_diff'))
        viz_btn_layout2.addWidget(self.whole_rolling_diff_btn)

        self.whole_rolling_same_btn = QPushButton('Whole + Rolling (Same Units)')
        self.whole_rolling_same_btn.clicked.connect(lambda: self.run_visualization('whole_rolling_same'))
        viz_btn_layout2.addWidget(self.whole_rolling_same_btn)

        main_layout.addLayout(viz_btn_layout2)

        # Status bar
        self.statusBar().showMessage('Ready')

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.current_config = json.load(f)
            else:
                self.current_config = self.default_config.copy()
                self.save_config()  # Create default config file

            self.update_config_display()
            self.statusBar().showMessage('Configuration loaded successfully')
        except json.JSONDecodeError:
            QMessageBox.warning(self, 'Error', 'Invalid JSON in config file')
            self.statusBar().showMessage('Error loading configuration')

    def save_config(self):
        """Save configuration to file"""
        try:
            # Validate JSON before saving
            new_config = json.loads(self.config_edit.toPlainText())
            self.current_config = new_config

            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=4)

            self.statusBar().showMessage('Configuration saved successfully')
        except json.JSONDecodeError:
            QMessageBox.warning(self, 'Error', 'Invalid JSON format')
            self.statusBar().showMessage('Error saving configuration')

    def update_config_display(self):
        """Update the config display with current config"""
        self.config_edit.setPlainText(json.dumps(self.current_config, indent=4))

    def browse_data_file(self):
        """Open file dialog to select data file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select Data File', '', 'Text Files (*.txt);;All Files (*)')

        if file_path:
            self.current_config['filepath'] = file_path
            self.update_config_display()
            self.statusBar().showMessage(f'Selected file: {file_path}')

    def run_visualization(self, viz_type):
        """Run the selected visualization"""
        try:
            # Ensure we have the latest config
            self.save_config()

            # Generate output filename
            base_name = os.path.splitext(self.current_config['filepath'])[0]
            output_map = {
                'single': f"{base_name}-heatmap-s.png",
                'single_rolling_diff': f"{base_name}-heatmap-sdu.png",
                'single_rolling_same': f"{base_name}-heatmap-ssu.png",
                'whole': f"{base_name}-heatmap-w.png",
                'whole_rolling_diff': f"{base_name}-heatmap-wdu.png",
                'whole_rolling_same': f"{base_name}-heatmap-wsu.png"
            }
            output_path = output_map[viz_type]

            # Run the appropriate visualization
            viz_methods = {
                'single': self.visualizer.visualize_single,
                'single_rolling_diff': self.visualizer.visualize_single_rolling_diff_unit,
                'single_rolling_same': self.visualizer.visualize_single_rolling_same_unit,
                'whole': self.visualizer.visualize_whole,
                'whole_rolling_diff': self.visualizer.visualize_whole_rolling_diff_unit,
                'whole_rolling_same': self.visualizer.visualize_whole_rolling_same_unit
            }

            viz_methods[viz_type](self.current_config, output_path)
            self.statusBar().showMessage(f'Visualization completed. Saved to {output_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Error during visualization: {str(e)}')
            self.statusBar().showMessage(f'Error: {str(e)}')


if __name__ == '__main__':
    app = QApplication([])

    # Set style for better appearance
    app.setStyle('Fusion')

    # Create and show the main window
    window = HeatmapGUI()
    window.show()

    # Start the event loop
    app.exec_()