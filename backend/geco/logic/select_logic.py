#from data_structure.database import db
from sqlalchemy import create_engine
import pandas as pd

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
        query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id where {}".format(filter)
        #query = "select distinct(item_id) from dw.flatten_gecoagent where {} group by item_id".format(filter)
        return query

    def query_key(self):
        query = ""
        i = 1
        for k in self.op.depends_on.fields.metadata:
            if i < len(self.op.depends_on.fields.metadata):
                query += "item_id in (select distinct(item_id) from dw.unified_pair_gecoagent where key='{}' and value in {}) and ".format(
                    k, ['{}'.format(x) for x in self.op.depends_on.fields.metadata[k]]).replace('[', '(').replace(']', ')')
            else:
                query += "item_id in (select distinct(item_id) from dw.unified_pair_gecoagent where key='{}' and value in {})".format(
                    k, ['{}'.format(x) for x in self.op.depends_on.fields.metadata[k]]).replace('[', '(').replace(']', ')')
            i += 1
        return query

    def run(self):

        query = self.query_field()
        print("select rr.* from rr.{} as rr {}".format(self.ds.fields['dataset_name'][0],query))
        res = db.engine.execute("select rr.* from rr.{} as rr {}".format(self.ds.fields['dataset_name'][0],query))
        values = res.fetchall()
        reg = pd.DataFrame(values, columns=res.keys())
        print(reg.head())
        self.ds.add_region_table(reg)
        self.ds.add_region_schema(list(res.keys()))
        if hasattr(self.op.depends_on.fields, 'metadata'):
             query2 = self.query_key()
             res = db.engine.execute(
                 "select rr.* from dw.unified_pair_gecoagent as rr {} where ({})".format(
                     query, query2))
        else:
             res = db.engine.execute(
                 "select rr.* from dw.unified_pair_gecoagent as rr {}".format(
                     query))
        values = res.fetchall()
        meta = pd.DataFrame(values, columns=res.keys())
        print('meta')
        print(meta.head())
        self.ds.add_meta_table(meta)
        #res = db.engine.execute("select * from rr.gene_expression_hg19 where item_id in ({}) limit 100".format(query))
        #values = res.fetchall()
        #reg = pd.DataFrame(values, columns = res.keys())
        #print(reg.head())
        #self.ds.add_region_table(reg)
        #self.ds.add_region_schema(list(res.keys()))
        self.op.result = self.ds
        self.op.executed = True

