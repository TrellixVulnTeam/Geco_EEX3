import pandas as pd
from tqdm import tqdm
import numpy as np

class PivotRes:
    def __init__(self, pivot, labels):
        self.ds = pivot
        self.labels = labels

class PivotLogic:
    def __init__(self, op):
        self.op = op
        self.ds = self.op.depends_on.result
        self.run()

    def run(self):
        if self.op.meta_col != None:
            items = list(self.ds.meta['item_id'])
            items.sort()
            temp_meta = pd.DataFrame(index=items, columns=self.op.meta_col)
            for i in self.op.meta_col:
                temp_meta[i] = self.ds.meta[self.ds.meta['key'] == i]['value']
        else:
            items = list(self.ds.meta['item_id'])
            items.sort()
            temp_meta = pd.DataFrame(index=items, columns=self.op.meta_row)

            for i in self.op.meta_row:
                temp_meta[i] = self.ds.meta[self.ds.meta['key'] == i]['value']

        temp_reg = self.ds.region.merge(temp_meta, left_on='item_id', right_index=True)
        items_reg = pd.DataFrame(index=list(set(temp_reg['item_id'])))
        # if (self.op.region_col!=None) and (self.op.meta_col!=None):
        #    col = self.op.region_col.append(self.op.meta_col)
        if self.op.region_col != None:
            col = self.op.region_col
        else:
            col = self.op.meta_col
        if (self.op.region_row != None) and (self.op.meta_row != None):
            row = self.op.region_row.append(self.op.meta_row)
        elif self.op.region_row != None:
            row = self.op.region_row
        else:
            row = self.op.meta_row
        pivot = temp_reg.pivot_table(index=row, columns=col, values=self.op.value)
        pivot.columns = pivot.columns.droplevel(0)

        if self.op.other_region != None:
            labels_reg = temp_reg[self.op.other_region]

        if (self.op.meta_col != None):
            if self.op.other_meta != None:
                pivot = pivot.T
                for i in self.op.other_meta:
                    pivot[i] = ""
                    temp = self.ds.meta[self.ds.meta['key'] == i]
                    for x in pivot.index:
                        pivot.at[x, i] = temp[self.ds.meta['item_id'] == x]['value'].values[0]
                pivot = pivot.T
            elif self.op.other_region != None:
                for i in self.op.other_region:
                    pivot[i] = list(labels_reg[i])
        else:
            if self.op.other_meta != None:
                for i in self.op.other_meta:
                    temp = self.ds.meta[self.ds.meta['key'] == i]
                    for x in pivot.index:
                        pivot.at[x, i] = temp[self.ds.meta['item_id'] == x][
                            'value'].values[0]
            elif self.op.other_region != None:
                pivot = pivot.T
                for i in self.op.other_region:
                    pivot[i] = list(labels_reg[i])
                pivot = pivot.T
        # pivot.index= pivot.index.droplevel(0)
        pivot.to_csv('pivot.csv')
        self.op.result = pivot
        self.op.executed = True
        self.write()

    def write(self):
        with open('jupyter_notebook.ipynb', 'a') as f:
            f.write('{ "cell_type": "code",' +
                    '"execution_count": 0,' +
                    '"metadata": {},' +
                    '"outputs": [],' +
                    '"source": [' +
                    'import pandas as pd\n' +
                    'table = pd.read_csv("pivot.csv")' +
                    ']},')
        f.close()

        with open('python_script.py', 'a') as f:
            f.write('import pandas as pd\n' +
                    'table = pd.read_csv("pivot.csv")')
        f.close()