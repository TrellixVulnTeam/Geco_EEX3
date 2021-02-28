from flask_sqlalchemy import SQLAlchemy
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

annotation_fields = ["content_type", "assembly", "source", 'dataset_name']
experiment_fields = ['source', 'data_type', 'assembly', 'tissue', 'cell', 'disease', 'is_healthy', 'target',  'dataset_name']
fields = ["content_type", 'source', 'data_type', 'tissue', 'cell', 'disease', 'is_healthy', 'target',  'dataset_name']
sources = ['tcga', 'encode', 'roadmap epigenomics', '1000 genomes', 'refseq']
datasets = ['grch38_tcga_gene_expression_2019_10', 'grch38_tcga_somatic_mutation_masked_2019_10',
            'grch38_tcga_methylation_2019_10', 'grch38_tcga_copy_number_masked_2019_10', 'grch38_tcga_mirna_expression_2019_10']


class database:
    def __init__(self):
        self.fields = fields
        self.get_all_values()
        #self.find_all_keys()

    def get_all_values(self):
        self.fields_names = []
        self.values = {}
        res = db.engine.execute("select item_id, " + ', '.join(fields)
 + " from dw.flatten_gecoagent where source in {} and dataset_name in {}".format(tuple(sources), tuple(datasets)))
        values = res.fetchall()
        self.table = pd.DataFrame(values, columns=res.keys())

        for f in self.fields:
            res = list(set(self.table[f]))
            if res!=[] and len(res)>1:
                self.fields_names.append(f)
                self.values[f]= res
                setattr(self, (str(f) + '_db'), res)
            else:
                self.table = self.table.drop(f,axis=1)

        meta = db.engine.execute("select distinct(key) from dw.unified_pair_gecoagent group by key")
        self.meta_schema = meta.fetchall()


class DB:
    def __init__(self, fields, is_ann, all_db):
        self.is_ann = is_ann
        self.is_ann_gcm = 'is_annotation=true' if is_ann else 'is_annotation=false'
        #self.fields = fields
        self.db = all_db
        self.table = self.db.table.copy()
        #self.table = self.table[self.table['is_annotation']==self.is_ann]
        self.fields = [i for i in self.table.columns.values if
                       i != 'item_id' and len(list(set(self.table[i].values))) > 1]
        self.values = {x:set(self.table[x].values) for x in fields if (x in self.table.columns.values) and len(set(self.table[x].values))>1}
        self.fields_names = list(self.values.keys())
        #self.get_values()
        self.meta_schema = self.db.meta_schema

    def get_values(self):
        self.fields_names = []
        for f in self.fields:
            res = getattr(self.db, (str(f) + '_db'))
            if res!=[]:
                self.fields_names.append(f)
                setattr(self, (str(f) + '_db'), res)

    def update(self, gcm):
        self.all_values = []
        for f in self.fields:
            values = []
            if f in gcm:
                self.table = self.table[self.table[f].isin(gcm[f])]
            val = list(self.table[f])
            if (val != []) and (len(val) > 1):
                self.fields_names.append(f)
                for i in range(len(val)):
                    if val[i] != None:
                        values.append(val[i])
                        self.all_values.append(val[i])
            elif len(val) == 1:
                values = [val[0]]

            if values != []:
                self.values[f]=values

    def retrieve_values(self, gcm, f):
        values = list(self.table[f])
        set_val = list(set(values))
        val = [{"value": i, "count": values.count(i)} for i in set_val]
        return val

    def check_existance(self, gcm):

        for f in gcm:
            self.table = self.table[self.table[f].isin(gcm[f])]
        if len(self.table)>0:
            return len(self.table)
        else:
            print("error")
            return 0

    def download(self, gcm):
        links = list(set(self.table['local_url']))
        return links

    def go_back(self, gcm):
        self.table = self.db.table.copy()
        for f in gcm:
            self.table = self.table[self.table[f].isin(gcm[f])]

    def query_field(self, gcm):
        filter = ' and '.join(
            [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                 gcm.items()])
        query = "join dw.flatten_gecoagent as df on rr.item_id = df.item_id where {}".format(filter)
        #query= "select item_id from dw.flatten_gecoagent where {}".format(filter)
        return query

    def query_key(self, gcm):
        query=""
        i = 1
        for k in gcm:
            if i<len(gcm):
                query += "item_id in (select item_id from dw.unified_pair_gecoagent where key='{}' and value in {}) and ".format(k, ['{}'.format(x) for x in gcm[k]]).replace('[','(').replace(']',')')
            else:
                query += "item_id in (select item_id from dw.unified_pair_gecoagent where key='{}' and value in {})".format(k, ['{}'.format(x) for x in gcm[k]]).replace('[','(').replace(']',')')
            i+=1
        return query

    # Retrieves all keys based on a user input string
    def find_all_keys1(self, filter, filter2={}):
        for f in filter:
            self.table = self.table[self.table[f].isin(filter[f])]
        for f in filter2:
            self.metadata = self.metadata.loc[(self.metadata['key']!=f)|(self.metadata['key']==f & self.metadata['value'].isin(filter2[f]))]
        item_id = self.table['item_id']
        self.metadata = self.metadata[self.metadata['item_id'].isin(item_id)]
        set_keys = list(set(self.metadata['key']))
        keys = {i: len(self.metadata[self.metadata['key']==i]) for i in set_keys}
      #  keys = {i[0]:i[1] for i in keys}
        return keys

    def find_all_keys(self, filter, filter2={}):
        item_id = list(self.table['item_id'].values)
        #items = ','.join(str(i) for i in item_id)
        query = self.query_field(filter)
        if filter2!={}:
            query2 = self.query_key(filter2)
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) and {} group by key".format(query, query2)).fetchall()
            keys = db.engine.execute(
                "select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({}) and {}".format(
                    query, query2)).fetchall()
        else:
            #keys = db.engine.execute("select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({})".format(items)).fetchall()
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) group by key".format(query)).fetchall()
            #keys = db.engine.execute("select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({})".format(query)).fetchall()
            keys = db.engine.execute(
                "select rr.item_id, rr.key, rr.value from dw.unified_pair_gecoagent as rr {}".format(
                    query)).fetchall()

        self.metadata = pd.DataFrame(keys, columns=['item_id', 'key', 'value'])
        self.metadata = self.metadata[self.metadata['item_id'].isin(item_id)]
        set_keys = list(set(self.metadata['key']))
        keys = {i: len(self.metadata[self.metadata['key'] == i]) for i in set_keys}
        return keys

    def find_keys(self, filter, string):
        query = self.query_field(filter)
        #keys = db.engine.execute("select key from dw.unified_pair_gecoagent where key like '%{}%' and item_id in ({}) group by key".format(string, query)).fetchall()
        keys = db.engine.execute(
            "select rr.key from dw.unified_pair_gecoagent as rr {} where key like '%{}%' group by key".format(
                query, string)).fetchall()

        keys = [i[0] for i in keys]
        return keys

    # Retrieves all values based on a user input string
    def find_values(self, filter, string):
        query = self.query_field(filter)
        values = db.engine.execute(
            "select distinct(key), value  from dw.unified_pair_gecoagent where item_id in ({}) and value like '%{}%'".format(query, string)).fetchall()

        val = [{"key":i[0],"value":i[1]} for i in values]
        return val

    def find_key_values(self, key, filter, filter2={}):
        query = self.query_field(filter)
        if filter2!={}:
            query2 = self.query_key(filter2)
            values = db.engine.execute(
                "select value, count(distinct(item_id)) from dw.unified_pair_gecoagent where item_id in ({}) and {} and key in ('{}') group by value".format(
                    query, query2, str(key))).fetchall()
        else:
            #values = db.engine.execute("select value, count(distinct(item_id)) from dw.unified_pair_gecoagent where item_id in ({}) and key in ('{}') group by value".format(query, str(key))).fetchall()
            values = db.engine.execute(
                "select rr.value, count(distinct(rr.item_id)) from dw.unified_pair_gecoagent as rr {} and rr.key in ('{}') group by value".format(
                    query, str(key))).fetchall()

        val = [{"value": i[0], "count": i[1]} for i in values]
        number = True
        for i in values:
            if str(i[0]).isnumeric()!=True and i[0]!=None:
                number = False
        return val, number

    def download_filter_meta(self, gcm, filter2):
        filter = ' and '.join(
            [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                 gcm.items()])
        if filter2!={}:
            query = self.query_key(filter2)
            links = db.engine.execute("select local_url from dw.flatten_gecoagent where {} and {} group by local_url".format(filter, query)).fetchall()
        else:
            links = db.engine.execute(
                "select local_url  from dw.flatten_gecoagent where {} group by local_url".format(filter)).fetchall()

        val = [i[0] for i in links]
        return val

    def find_regions(self,gcm,filter2):
        ds_name = gcm['dataset_name'][0]
        query = self.query_field(gcm)
        if filter2 != {}:
            query2 = self.query_key(filter2)
            res = db.engine.execute(
                "select * from rr.{} where (item_id in ({})) and ({}) limit 1".format(ds_name,
                    query, query2))
        else:
            #res = db.engine.execute("select * from rr.{} where (item_id in ({})) limit 1".format(ds_name,query))
            res = db.engine.execute("select rr.* from rr.{} as rr {} limit 1".format(ds_name, query))

        self.region_schema = res.keys()
        return self.region_schema
    '''
     def update1(self, gcm):
        gcm_source = "source in ('tcga','encode','roadmap epigenomics','1000 genomes','refseq')"
        if 'source' not in gcm:
            filter = ' and '.join(
                [self.is_ann_gcm] + [gcm_source] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v]))
                                                    for (k, v) in gcm.items()])
        else:
            filter = ' and '.join(
                [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                     gcm.items()])

        self.fields_names = []
        self.all_values = []
        for f in self.fields:
            val = db.engine.execute("select {} from dw.flatten_gecoagent where {} group by {}".format(f, filter, f)).fetchall()
            val = [i[0] for i in val]
            values = []
            if (val != []) and (len(val) > 1):
                self.fields_names.append(f)
                for i in range(len(val)):
                    if val[i] != None:
                        values.append(val[i])
                        self.all_values.append(val[i])
            elif len(val) == 1:
                values = [val[0]]

            if values != []:
                self.values[f]=values
                #setattr(self, (str(f) + '_db'), values)

    

    def retrieve_values1(self, gcm, f):
        filter = ' and '.join(
            [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                 gcm.items()])
        val = db.engine.execute("select {}, count({}) from dw.flatten_gecoagent where {} group by {}".format(f, f, filter, f)).fetchall()

        val = [{"value":i[0],"count":i[1]} for i in val]

        return val

    def check_existance1(self, gcm):
        filter = ' and '.join(
                [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                     gcm.items()])

        val = db.engine.execute(
            "select count(*) from dw.flatten_gecoagent where {} ".format(filter)).fetchall()

        if val[0][0]>0:
            return val[0][0]
        else:
            print("error")
            return 0

    def download1(self, gcm):
        filter = ' and '.join(
            [self.is_ann_gcm] + ['{} in ({})'.format(k, ",".join(['\'{}\''.format(x) for x in v])) for (k, v) in
                                 gcm.items()])

        links = db.engine.execute(
            "select local_url  from dw.flatten_gecoagent where {} group by local_url".format(filter)).fetchall()
        val = [i[0] for i in links]
        return val'''