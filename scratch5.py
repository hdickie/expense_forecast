
import pandas as pd

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import numpy as np

if __name__ == '__main__':
    figure(figsize=(28, 6), dpi=80)

    ind = np.arange(10)
    width = 1/12

    col_names = ['A','B','C','D']
    values = [[1,1,1],
              [2,2,2],
              [3,3,3],
              [4,4,4]]

    fig, ax = plt.subplots()
    for i in range(0, 4):
        for j in range(0, 3):
            y_value = ind[i] + width * j
            plot_value = values[i][j]
            ax.barh(y_value, plot_value, width, label=col_names[i])

    plt.savefig('testplot.png')
    plt.close()
