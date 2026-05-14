import matplotlib.pyplot as plt
import pandas as pd
from itertools import islice
import io
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re



class WindDataAnalyzer:
    def __init__(self, asc_path, hed_path: str):
        self.asc_path = asc_path
        self.hed_path = hed_path
        self.df = None

    def get_wind_dataframe(self, header_info:str, header_data):
        """This function parses the hed file to generate a df for a plot"""
        
        start_line = 0
        num_entities = 0

        with open (self.hed_path, 'r') as f:
            for i, line in enumerate(f):
                if header_info in line:
                    match = re.search(r'\[\s*(\d+)', line)
                    if match:
                        num_entities = int(match.group(1))
                        start_line = i + 1
                        break

            new_df = pd.read_csv(
                self.hed_path,
                skiprows=start_line,
                nrows=num_entities,
                sep='\s+',
                header=None,
                names=header_data,
                on_bad_lines='skip', 
                engine='python'
            )

            return new_df
        

    def get_wind_frame_plot_3D(self, tap_df, frame_df, corners_df, output_path: str):
        fig = plt.figure(figsize=(10,8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(corners_df['X'], corners_df['Y'], corners_df['Z'], 
           color='darkorange', s=60, label='Corners')
        

        for _, line in frame_df.iterrows():
            start_id = int(line['Start']) - 1
            end_id = int(line['End']) - 1


            start_node = corners_df.iloc[start_id]
            end_node = corners_df.iloc[end_id]

        
            xs = [start_node['X'], end_node['X']]
            ys = [start_node['Y'], end_node['Y']]
            zs = [start_node['Z'], end_node['Z']]

            ax.plot(xs, ys, zs, color='black', linewidth=2)

        for i, row in corners_df.iterrows():
            ax.text(row['X'], row['Y'], row['Z'], str(i), fontsize=12, fontweight='bold')

        scatter = ax.scatter(tap_df['X'], tap_df['Y'], tap_df['Z'], 
                     c=tap_df['Face_No'], 
                     cmap='tab10', 
                     s=15, 
                     label='Pressure Taps')
        
        cbar = plt.colorbar(scatter, ax = ax, pad=0.1)
        cbar.set_label('Face Number')


        ax.set_xlabel('X (Width)')
        ax.set_ylabel('Y (Length)')
        ax.set_zlabel('Z (Height)')
        ax.set_title('Building Wireframe Model with Face-Coded Taps')

        ax.set_box_aspect([80, 125, 20]) 
        ax.legend()

        plt.savefig(output_path)
        plt.close()
        return output_path

    
    


        

    
