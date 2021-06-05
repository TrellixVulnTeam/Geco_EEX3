#from data_structure.database import db
from sqlalchemy import create_engine
import pandas as pd
import time

def get_db_uri():
    postgres_url = "localhost"
    postgres_user = "geco_ro"
    postgres_pw = "geco78"
    postgres_db = "gmql_meta_new16_geco_agent"
    return 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=postgres_user,
                                                                 pw=postgres_pw,
                                                                 url=postgres_url,
                                                                 db=postgres_db)

#db = SQLAlchemy()
db_string = get_db_uri()
db = create_engine(db_string)


class SelectLogic:
    def __init__(self, select):
        self.op = select
        self.ds = self.op.depends_on
        self.run()

    def query_field(self):
        filter = ' and '.join(['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                 self.op.depends_on.fields.items()if k!='metadata'])
        if self.ds.items!=[]:
            items = ','.join(str(i) for i in self.ds.items)
            if 'metadata' in self.op.depends_on.fields and self.op.depends_on.fields['metadata'] != None:
                keys = ','.join([f'\'{str(i)}\'' for i in list(self.op.depends_on.fields['metadata'].keys())])
                values = ','.join([f'\'{str(i)}\'' for k, v in self.op.depends_on.fields['metadata'].items() for i in v])
                query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id join dw.unified_pair_gecoagent as du on rr.item_id = du.item_id " \
                        "where df.item_id in ({}) and du.key in ({}) and du.value in ({})".format(items, keys, values)
            else:
                query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id " \
                        "where df.item_id in ({})".format(items)
        else:
            if 'metadata' in self.op.depends_on.fields and self.op.depends_on.fields['metadata'] != None:
                keys = ','.join([f'\'{str(i)}\'' for i in list(self.op.depends_on.fields['metadata'].keys())])
                values = ','.join([f'\'{str(i)}\'' for k, v in self.op.depends_on.fields['metadata'].items() for i in v])
                query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id join dw.unified_pair_gecoagent as du on rr.item_id = du.item_id " \
                        "where {} and du.key in ({}) and du.value in ({})".format(filter, keys, values)
            else:
                query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id " \
                        "where {}".format(filter)
        #print(query)
        #query = "select distinct(item_id) from dw.flatten_gecoagent where {} group by item_id".format(filter)
        return query


    def run(self):
        # pre = time.time()
        # items = ','.join(str(i) for i in self.ds.items)
        # #query = self.query_field()
        # query =  "select item_id, gene_symbol, fpkm  from rr.{} as rr where item_id in ({})".format(self.ds.fields['dataset_name'][0],items)
        # print(query)
        # #res = db.engine.execute("select rr.* from rr.{} as rr {}".format(self.ds.fields['dataset_name'][0],query))
        # #print('time-first select:', time.time() - pre)
        # #values = res.fetchall()
        # #print('time-first select fetchall:', time.time() - pre)
        # #reg = pd.DataFrame(values, columns=res.keys())
        # #reg = pd.read_sql("select rr.* from rr.{} as rr {}".format(self.ds.fields['dataset_name'][0],query), db.engine)
        # reg = pd.read_sql(query, db.engine)
        # print(reg.head())
        # print('time-first select df:', time.time() - pre)
        # #print(reg.head())
        #
        # self.ds.add_region_table(reg)
        # #self.ds.add_region_schema(list(res.keys()))
        # self.ds.add_region_schema(list(reg.columns))
        # print('time-add schema:', time.time() - pre)
        # if hasattr(self.op.depends_on.fields, 'metadata'):
        #      query2 = self.query_key()
        #      res = db.engine.execute(
        #          "select rr.* from dw.unified_pair_gecoagent as rr {} where ({})".format(
        #              query, query2))
        # else:
        #      query_meta =  "select * from dw.unified_pair_gecoagent where item_id in ({})".format(items)
        #      print(query_meta)
        #      res = db.engine.execute(query_meta)
        # print('time-second select:', time.time() - pre)
        # values = res.fetchall()
        # print('time-second fetchall:', time.time() - pre)
        # meta = pd.DataFrame(values, columns=res.keys())
        # print('time-second df:', time.time() - pre)
        # del values
        # #print('meta')
        # #print(meta.head())
        # self.ds.add_meta_table(meta)
        # print('time-second add schema:', time.time() - pre)
        # #res = db.engine.execute("select * from rr.gene_expression_hg19 where item_id in ({}) limit 100".format(query))
        # #values = res.fetchall()
        # #reg = pd.DataFrame(values, columns = res.keys())
        # #print(reg.head())
        #self.ds.add_region_table(reg)
        #self.ds.add_region_schema(list(res.keys()))
        self.op.result = self.ds
        #print('time-save result:', time.time() - pre)
        self.op.executed = True
        #print('time:', time.time()-pre)
        #print('fine select')
        #reg.to_csv('region_lung.csv')
        #meta.to_csv('meta_lung.csv')

