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

annotation_fields = ["content_type", "assembly", "source"]
experiment_fields = ['source', 'data_type', 'assembly', 'tissue', 'cell', 'disease', 'is_healthy', 'target','dataset_name']
experiment_fields_old =['data_type', 'tissue', 'disease', 'is_healthy','dataset_name']
#ann_db = AnnotationDB()

class database:
    def __init__(self):
        self.fields = ['source', 'data_type', 'assembly', 'file_format', 'biosample_type', 'tissue', 'cell', 'disease', 'is_healthy', 'technique', 'feature', 'target', 'content_type']
        self.get_all_values()
        #self.find_all_keys()

    def get_all_values(self):
        self.fields_names = []
        self.values = {}
        res = db.engine.execute("select * from dw.flatten_gecoagent")
        values = res.fetchall()
        self.table = pd.DataFrame(values, columns=res.keys())
        self.table = self.table[self.table['source'].isin(['tcga', 'encode', 'roadmap epigenomics', '1000 genomes', 'refseq'])]
        for f in self.fields:
            if f !='source':
                res = db.engine.execute("select {} from dw.flatten_gecoagent group by {}".format(f,f)).fetchall()
                res = [i[0] for i in res]
                if res!=[]:
                    self.fields_names.append(f)
                    self.values[f]= res
                    setattr(self, (str(f) + '_db'), res)
            else:
                self.fields_names.append('source')
                self.values['source'] = ['tcga', 'encode', 'roadmap epigenomics', '1000 genomes', 'refseq']
                setattr(self, 'source_db', ['tcga', 'encode', 'roadmap epigenomics', '1000 genomes', 'refseq'])


    def find_all_keys(self):
        print("sei dentro")
        keys = db.engine.execute("select item_id, key, value from dw.unified_pair_gecoagent Limit 10").fetchall()
        print('finito keys')
        self.metadata = pd.DataFrame(keys, columns=['item_id','key','value'])
        print("finito self")
        print(self.metadata)


class DB:
    def __init__(self, fields, is_ann, all_db):
        self.is_ann = is_ann
        #self.is_ann_gcm = 'true' if is_ann else 'false'
        self.is_ann_gcm = 'is_annotation=true' if is_ann else 'is_annotation=false'
        self.fields = fields
        self.db = all_db
        self.table = self.db.table.copy()
        #self.metadata = self.db.metadata.copy()
        self.table = self.table[self.table['is_annotation']==self.is_ann]
        self.values = {x:set(self.table[x].values) for x in fields if len(set(self.table[x].values))>1}
        self.fields_names = list(self.values.keys())
        #self.get_values()

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
        query= "select item_id from dw.flatten_gecoagent where {} group by item_id".format(filter)
        print('Query in query_field:', query)

        return query


    def query_key(self, gcm):
        query=""
        i = 1
        for k in gcm:
            if i<len(gcm):
                query += "item_id in (select item_id from dw.unified_pair_gecoagent where key='{}' and value in {} group by item_id) and ".format(k, ['{}'.format(x) for x in gcm[k]]).replace('[','(').replace(']',')')
            else:
                query += "item_id in (select item_id from dw.unified_pair_gecoagent where key='{}' and value in {} group by item_id)".format(k, ['{}'.format(x) for x in gcm[k]]).replace('[','(').replace(']',')')
            i+=1
        return query

    # Retrieves all keys based on a user input string
    def find_all_keys1(self, filter, filter2={}):
        for f in filter:
            self.table = self.table[self.table[f].isin(filter[f])]
            print(self.table)
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
        items = ','.join(str(i) for i in item_id)
        #print("items:",items)
        query = self.query_field(filter)
        if filter2!={}:
            query2 = self.query_key(filter2)
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) and {} group by key".format(query, query2)).fetchall()
            keys = db.engine.execute(
                "select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({}) and {}".format(
                    items, query2)).fetchall()
        else:
            #keys = db.engine.execute("select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({})".format(items)).fetchall()
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) group by key".format(query)).fetchall()
            keys = db.engine.execute(
                "select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({}) Limit 50 ".format(query)).fetchall()

        #keys = {i[0]:i[1] for i in keys}
        self.metadata = pd.DataFrame(keys, columns=['item_id', 'key', 'value'])
        #self.metadata = self.metadata[self.metadata['item_id'].isin(item_id)]
       # print('metadata',self.metadata)
        set_keys = list(set(self.metadata['key']))
        keys = {i: len(self.metadata[self.metadata['key'] == i]) for i in set_keys if len(self.metadata[self.metadata['key'] == i]) >1}
        #keys = {i: len(self.metadata[self.metadata['key'] == i]) for i in set_keys}
        print({'   - ': i for i in set_keys})
        return keys


    def find_all_keys_old(self, filter, filter2={}):
        item_id = list(self.table['item_id'].values)
        items = ','.join(str(i) for i in item_id)
        #print("items:",items)
        query = self.query_field(filter)
        if filter2!={}:
            query2 = self.query_key(filter2)
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) and {} group by key".format(query, query2)).fetchall()
            keys = db.engine.execute(
                "select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({}) and {}".format(
                    items, query2)).fetchall()
        else:
            #keys = db.engine.execute("select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({})".format(items)).fetchall()
            #keys = db.engine.execute("select key, count(distinct(value)) from dw.unified_pair_gecoagent where item_id in ({}) group by key".format(query)).fetchall()
            keys = db.engine.execute(
                "select item_id, key, value from dw.unified_pair_gecoagent where item_id in ({}) Limit 50 ".format(query)).fetchall()

        #keys = {i[0]:i[1] for i in keys}
        self.metadata = pd.DataFrame(keys, columns=['item_id', 'key', 'value'])
        #self.metadata = self.metadata[self.metadata['item_id'].isin(item_id)]
       # print('metadata',self.metadata)
        set_keys = list(set(self.metadata['key']))
        #keys = {i: len(self.metadata[self.metadata['key'] == i]) for i in set_keys if len(self.metadata[self.metadata['key'] == i]) >1}
        keys = {i: len(self.metadata[self.metadata['key'] == i]) for i in set_keys}
        print({'   - ': i for i in set_keys})
        return keys




    def find_keys(self, filter, string):
        query = self.query_field(filter)
        keys = db.engine.execute("select key from dw.unified_pair_gecoagent where key like '%{}%' and item_id in ({}) group by key".format(string, query)).fetchall()
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
            values = db.engine.execute(
                "select value, count(distinct(item_id)) from dw.unified_pair_gecoagent where item_id in ({}) and key in ('{}') group by value limit 100".format(query, str(key))).fetchall()
        val = [{"value": i[0], "count": i[1]} for i in values]
        #print('val1',val)
        number = True
        for i in values:
            if str(i[0]).isnumeric()!=True and i[0]!=None:
                #print('i[0]:',i[0])
                number = False
       # print('val', val)
       # print('number', number)
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

    def retrieve_metadata(self, gcm, filter2 ={}):
        query = self.query_field(gcm)
        if filter2 != {}:
            query2 = self.query_key(filter2)
            res = db.engine.execute(
                "select * from dw.unified_pair_gecoagent where (item_id in (select item_id from dw.flatten_gecoagent where {})) and ({})".format(
                    query, query2))
        else:
            res = db.engine.execute(
                "select * from dw.unified_pair_gecoagent where (item_id in (select item_id from dw.flatten_gecoagent where {}))".format(
                    query))
        values = res.fetchall()
        x = pd.DataFrame(values, columns=res.keys())
        return x


    def retrieve_meta(self,gcm,filter2):
        query = self.query_field(gcm)
        if filter2!={}:
            query2 = self.query_key(filter2)
            res = db.engine.execute(
                "select * from dw.unified_pair_gecoagent where (item_id in ({})) and ({})".format(
                    query, query2))
        else:
            res = db.engine.execute(
                "select * from dw.unified_pair_gecoagent where (item_id in ({}))".format(
                    query))
        values = res.fetchall()
        meta = pd.DataFrame(values, columns=res.keys())
        return meta


'''    def update(self, gcm):
        self.all_values = []
        for f in self.fields:
            print(f, "f")
            print("sono in update", self.fields)
            values = []
            if f in gcm:
                print("f in gmc")
                self.table = self.table[self.table[f].isin(gcm[f])]
            val = list(self.table[f])
            if (val != []) and (len(val) > 1):
                print("appendo")
                self.fields_names.append(f)
                for i in range(len(val)):
                    if val[i] != None:
                        values.append(val[i])
                        self.all_values.append(val[i])
            elif len(val) == 1:
                values = [val[0]]

            if values != []:
                self.values[f]=values 


    
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