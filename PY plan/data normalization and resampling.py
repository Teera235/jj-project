import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename

Tk().withdraw()
file_path = askopenfilename(filetypes=[("Excel files", "*.xlsx")])
if not file_path:
    raise ValueError("no,more")

df = pd.read_excel(file_path)

df.columns = ['time', 'kgf', 'thrust']

df['time'] = df['time'].astype(float)
df['kgf'] = df['kgf'].astype(float)
df['thrust'] = df['thrust'].astype(float)

df = df.drop_duplicates(subset='time')

df.set_index('time', inplace=True)
df = df.sort_index()

new_time = np.arange(df.index.min(), df.index.max(), 0.01)

df_interp = df.reindex(df.index.union(new_time))
df_interp = df_interp.interpolate(method='index')
df_interp = df_interp.loc[new_time]  

plt.figure(figsize=(10, 6))
plt.plot(df_interp.index, df_interp['thrust'], label='Interpolated Thrust (N)', color='blue')
plt.plot(df_interp.index, df_interp['kgf'], label='Interpolated Thrust (kgf)', color='green', linestyle='--')
plt.xlabel("Time (s)")
plt.ylabel("Thrust")
plt.title("Interpolated Thrust Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
