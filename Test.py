import csv
import pandas as pd

df = pd.read_csv('node.csv')
# print(df)
node = df.loc[0]
node = node.to_dict()

for i in node:
    print(type(i))


# with open('node.csv', 'r', encoding='UTF-8') as node:
#     file_reader = csv.DictReader(node)
#     for row in file_reader:
#         node = row
#
# for key in node:
#     if type(node[key]) == str:
#         node[key] = int(node[key])