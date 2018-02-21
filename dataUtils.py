
import pandas as pd
from pathlib import Path
import psycopg2
from psycopg2 import sql



#conn = psycopg2.connect("dbname=reyman64_trenum user=reyman64_trenum")

p = Path('.').resolve()
geocacheFile = p / 'data' / 'fullGeochache.json'

pd.set_option('display.width', 4000)
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_row', 1000)

df = pd.read_json(geocacheFile.as_uri(), orient='index', lines=True)
dfT = df.transpose()

# https://stackoverflow.com/questions/38895856/python-pandas-how-to-compile-all-lists-in-a-column-into-one-unique-list
uniqueAttributes = (list(set([a for b in dfT.cacheAttributs.tolist() for a in b])))

dfTExtracted = dfT[['code','logsAttributs']]
print(dfT)
#def generate_input_attributes(row):

#    print(row['code'])
#    query = sql.SQL("insert into {} values (%s, %s)").format(sql.Identifier('my_table'))
#    print(query.as_string(conn))
#dfTExtracted.apply(generate_input_attributes , axis=1)



#df = df.apply(pd.Series, index=df[0].keys())

#df1 = pd.DataFrame(df, columns=['code','logsAttributs'])
#print(df1)