"""Build dbt models on synthetic edge cases; never reads real complaint data."""
from pathlib import Path
from tempfile import TemporaryDirectory
import duckdb
import yaml
from dbt.cli.main import dbtRunner
ROOT=Path(__file__).resolve().parents[1]
def main():
    with TemporaryDirectory(prefix='fci-smoke-') as folder:
        temp=Path(folder); database=temp/'smoke.duckdb'
        columns=['Date received','Product','Sub-product','Issue','Sub-issue','Consumer complaint narrative','Company public response','Company','State','ZIP code','Tags','Submitted via','Date sent to company','Company response to consumer','Timely response?','Complaint ID','_source_archive','_source_csv','_source_record_number','_ingested_at']
        outcomes=['Closed with explanation','Closed with monetary relief','Closed with non-monetary relief','In progress','Untimely response','']
        rows=[]
        for i,outcome in enumerate(outcomes):
            row=['2025-01-01','Credit card','General','Payment','','Synthetic evidence only','',f'Company {i%2}','TX','001XX','Older American, Servicemember' if i==0 else '','Web','2025-01-02',outcome,'No' if i==4 else 'Yes',str(100+i),'synthetic.zip','synthetic.csv',str(i+1),'2026-10-04']
            if i==1:
                row[0]='12/30/2024';row[12]='12/31/2024';row[7]='Company | unusual label';row[9]='00001'
            if i==2:
                row[1]='Loan';row[2]='';row[3]='';row[8]='';row[9]='';row[5]='   '
            if i==3:
                row[12]='2024-12-31';row[5]=''
            rows.append(row)
        with duckdb.connect(str(database)) as con:
            con.execute('CREATE TABLE main.bronze_complaints ('+', '.join('"'+c+'" VARCHAR' for c in columns)+')')
            con.executemany('INSERT INTO main.bronze_complaints VALUES ('+','.join('?' for _ in columns)+')',rows)
        profile={'financial_complaint_intelligence':{'target':'dev','outputs':{'dev':{'type':'duckdb','path':str(database),'schema':'main','threads':1,'settings':{'memory_limit':'2GB','temp_directory':str(temp/'spill')}}}}}
        (temp/'profiles.yml').write_text(yaml.safe_dump(profile))
        result=dbtRunner().invoke(['build','--project-dir',str(ROOT/'dbt'),'--profiles-dir',str(temp),'--target-path',str(temp/'target')])
        if not result.success: raise RuntimeError(f'Synthetic dbt build failed: {result.exception}')
        with duckdb.connect(str(database)) as con:
            assert con.execute('SELECT COUNT(*) FROM main_star.fact_complaints').fetchone()[0]==6
            assert con.execute('SELECT COUNT(*) FROM main_gold.narrative_search_documents').fetchone()[0]==4
            assert con.execute('SELECT COUNT(*) FROM main_silver.complaint_tags').fetchone()[0]==2
            assert con.execute('SELECT SUM(sent_before_received_count) FROM main_gold.complaint_metrics').fetchone()[0]==1
            assert con.execute("SELECT COUNT(*) FROM main_star.dim_geography WHERE zip_code='00001'").fetchone()[0]==1
            assert con.execute("SELECT iso_year FROM main_star.dim_date WHERE calendar_date='2024-12-30'").fetchone()[0]==2025
        print('Synthetic smoke test passed: models built and edge-case assertions passed.')
if __name__=='__main__':main()
