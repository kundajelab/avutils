import matplotlib.pyplot as plt
import sys
import os
import numpy as np
from collections import defaultdict

def plot_hist(data, bins=None, figsize=(7,7), title="", **kwargs):
    if (bins==None):
        bins=len(data)
    plt.figure(figsize=figsize);
    plt.hist(data,bins=bins, **kwargs)
    plt.title(title)
    plt.show()
