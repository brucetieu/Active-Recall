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
# fig=plt.figure(1)
# a4_dims = (11.7, 8.27)
# fig, ax = plt.subplots(figsize=a4_dims)
# plt.figure(figsize=(15,8))
plt.figure(figsize=(10,5))
sns.swarmplot(x='Class', y='Duration', hue='Topic', data=newdata, size=10)

# sns.catplot(x='Class', y='Confidence', hue='Topic', kind='swarm', height=5, aspect=2,
#             s=15, data=newdata,
#             legend_out=False)
plt.legend(ncol=3, loc='center left', bbox_to_anchor=(1, 0.5))
# plt.legend(ncol=3, loc='upper right', bbox_to_anchor=(25, 0),
#            fontsize='medium', markerscale=3)
# plt.savefig('/Users/bruce/RecallAttmp2/static/image_output.png', dpi=300, format='png', bbox_inches='tight')
# sns.set(rc={'figure.figsize':(8,4),"font.size":20,"axes.titlesize":20,"axes.labelsize":20},style="white")


plt.title('Total Study Duration in Hours of Each Topic by Class')
plt.xticks(size=10)
plt.yticks(size=10)
plt.ylabel("Duration (hours)")
plt.show()