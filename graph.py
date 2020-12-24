import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import seaborn as sns

data = pd.read_excel("/Users/bruce/study.xlsx")

newdata = data.drop(columns=['Username', 'Session'])

newdata = newdata.groupby(['Class', 'Topic']).Duration.sum()
newdata = newdata.reset_index()
newdata['Duration'] = newdata['Duration'] / 60

plt.figure(figsize=(10,5))
sns.swarmplot(x='Class', y='Duration', hue='Topic', data=newdata, size=10)

plt.legend(ncol=3, loc='center left', bbox_to_anchor=(1, 0.5))


plt.title('Total Study Duration in Hours of Each Topic by Class')
plt.xticks(size=10)
plt.yticks(size=10)
plt.ylabel("Duration (hours)")
plt.show()
