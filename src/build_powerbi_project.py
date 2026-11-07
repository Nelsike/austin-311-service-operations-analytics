"""Build the native Power BI project from typed exports and reviewed measures.

Open powerbi/desktop/A311.pbip in Desktop and refresh. Set pProjectFolder to
the repository folder if it was moved. --portable writes a generic parameter.
"""
import argparse
import csv
import json
import re
import shutil
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi/desktop'
REPORT=OUT/'A311.Report'
MODEL=OUT/'A311.SemanticModel'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
NAVY='#152F45'
TEAL='#087F8C'
GRAY='#536B7B'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8')


def js(path,value):
    write(path,json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'austin311/'+value))


def lit(value):
    if isinstance(value,bool):
        value='true' if value else 'false'
    elif isinstance(value,str):
        value="'"+value.replace("'","''")+"'"
    else:
        value=str(value)+'D'
    return {'expr':{'Literal':{'Value':value}}}


def color(value):
    return {'solid':{'color':lit(value)}}


def field(table,name,measure=False):
    return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}


def projection(table,name,measure=False,label=None):
    result={'field':field(table,name,measure),'queryRef':table+'.'+name,'nativeQueryRef':name}
    if label:
        result['displayName']=label
    return result


def categorical(table,column,value,name):
    literal=(str(value)+'L') if isinstance(value,int) else "'"+value.replace("'","''")+"'"
    return {'name':name,'field':field(table,column),'type':'Categorical','howCreated':'User',
      'filter':{'Version':2,'From':[{'Name':'s','Entity':table,'Type':0}],
      'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':column}}],
        'Values':[[{'Literal':{'Value':literal}}]]}}}]}}


def container(title):
    return {'title':[{'properties':{'show':lit(True),'text':lit(title),'fontColor':color(NAVY),
        'fontSize':lit(12),'fontFamily':lit('Segoe UI Semibold')}}],
        'subTitle':[{'properties':{'show':lit(False)}}],
        'background':[{'properties':{'show':lit(True),'color':color('#FFFFFF'),'transparency':lit(0)}}],
        'border':[{'properties':{'show':lit(True),'color':color('#DAE4EB')}}]}


def visual(page,name,kind,x,y,w,h,query=None,title='',objects=None,filters=None):
    config={'$schema':BASE+'visualContainer/2.3.0/schema.json','name':name,
      'position':{'x':x,'y':y,'z':len(list((REPORT/'definition/pages'/page/'visuals').glob('*')))*1000 if (REPORT/'definition/pages'/page/'visuals').exists() else 0,
                  'width':w,'height':h,'tabOrder':0},
      'visual':{'visualType':kind,'drillFilterOtherVisuals':True,'visualContainerObjects':container(title)}}
    if query:
        config['visual']['query']={'queryState':{role:{'projections':items} for role,items in query.items()}}
    if objects:
        config['visual']['objects']=objects
    if filters:
        config['filterConfig']={'filters':filters}
    js(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',config)
    return config


def textbox(page,name,text,x,y,w,h,size=12,bold=False,ink=GRAY):
    config=visual(page,name,'textbox',x,y,w,h,objects={'general':[{'properties':{'paragraphs':[
      {'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','fontWeight':'bold' if bold else 'normal','color':ink}}]}]}}]})
    config['visual']['visualContainerObjects']={'background':[{'properties':{'show':lit(False)}}]}
    js(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',config)


def card(page,name,measure,label,x,y,w=234,h=108,precision=0):
    visual(page,name,'card',x,y,w,h,{'Values':[projection('fact_requests',measure,True)]},label,
      {'labels':[{'properties':{'fontSize':lit(29),'color':color(TEAL),'labelDisplayUnits':lit(1),'labelPrecision':lit(precision)}}],
       'categoryLabels':[{'properties':{'show':lit(False)}}]})


def slicer(page,name,table,column,label,x,w):
    visual(page,name,'slicer',x,105,w,67,{'Values':[projection(table,column)]},label,
      {'data':[{'properties':{'mode':lit('Dropdown')}}],
       'header':[{'properties':{'show':lit(False)}}],
       'selection':[{'properties':{'singleSelect':lit(False),'selectAllCheckboxEnabled':lit(True)}}],
       'items':[{'properties':{'fontSize':lit(10),'fontColor':color(NAVY)}}]})


EXTRA={
'Mean Closure Days':'AVERAGEX(FILTER(fact_requests, fact_requests[in_primary] = 1 && fact_requests[valid_closure] = 1), fact_requests[closure_days])',
'Oldest Reported Open Age Days':'MAXX(FILTER(fact_requests, fact_requests[in_primary] = 1 && fact_requests[is_open] = 1), fact_requests[open_age_days])',
'Ambiguous Timestamps':'CALCULATE([Primary Requests], KEEPFILTERS(fact_requests[timestamp_ambiguity] = 1))',
'Missing Geography All Intake':'COALESCE(COUNTROWS(FILTER(fact_requests, ISBLANK(fact_requests[latitude]))), 0)',
'Top Eight Intake':'VAR Position = RANKX(ALLSELECTED(dim_service[service_description]), [Primary Requests], , DESC, DENSE) RETURN IF(Position <= 8 && [Primary Requests] > 0, [Primary Requests], BLANK())',
'Open Age By Request':'IF([Reported Open Backlog] > 0, MAX(fact_requests[open_age_days]), BLANK())'
}


def measures():
    source='\n'.join(line for line in (ROOT/'powerbi/measures.dax').read_text(encoding='utf-8').splitlines() if not line.strip().startswith('//'))
    matches=list(re.finditer(r'^([A-Za-z][A-Za-z0-9 ]*)\s*=\s*',source,re.M))
    result={m.group(1).strip():source[m.end():matches[i+1].start() if i+1<len(matches) else len(source)].strip() for i,m in enumerate(matches)}
    result.update(EXTRA)
    return result


def make_model(portable):
    (MODEL/'definition/tables').mkdir(parents=True,exist_ok=True)
    js(MODEL/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.2','settings':{}})
    write(MODEL/'definition/database.tmdl','database\n\tcompatibilityLevel: 1606\n')
    folder=r'C:\Austin311' if portable else str(ROOT)
    write(MODEL/'definition/expressions.tmdl',f'expression pProjectFolder = "{folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\tlineageTag: {uid("pProjectFolder")}\n')
    tables=['fact_requests','dim_service','dim_organization','dim_channel','dim_date','snapshot']
    model='model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tvalueFilterBehavior: independent\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n'
    model+='\n'.join('ref table '+t for t in tables)+'\n\nref expression pProjectFolder\n'
    write(MODEL/'definition/model.tmdl',model)
    integer={'service_key','organization_key','channel_key','date_key','created_date_key','closed_date_key','deadline_date_key','year','quarter','month','month_sort','source_fiscal_year'}
    decimal={'closure_days','open_age_days','source_response_days','source_age_days','longitude','latitude'}
    for table in tables:
        with (ROOT/f'data/powerbi/{table}.csv').open(encoding='utf-8',newline='') as stream:
            columns=next(csv.reader(stream))
        lines=[f'table {table}',f'\tlineageTag: {uid(table)}']
        if table=='dim_date':
            lines.append('\tdataCategory: Time')
        types=[]
        for column in columns:
            dt='int64' if column in integer or column.startswith(('is_','source_is_')) or column in {'in_primary','valid_closure','valid_deadline_closure','closed_by_deadline','open_past_deadline','source_closed_on_time','status_flag_conflict','deadline_flag_conflict','timestamp_ambiguity'} else 'double' if column in decimal else 'dateTime' if column.endswith('_local') or (table=='dim_date' and column=='date') or (table=='snapshot' and column in {'snapshot_date','cohort_start','cohort_end_exclusive'}) else 'string'
            # Snapshot cutoff contains an explicit offset, retained as source text.
            if table=='snapshot' and column=='age_cutoff_local':
                dt='string'
            lines+=['',f'\tcolumn {column}',f'\t\tdataType: {dt}',f'\t\tlineageTag: {uid(table+"/"+column)}',f'\t\tsourceColumn: {column}','\t\tsummarizeBy: none']
            if column.endswith('_key') or column in {'in_primary','is_test','valid_closure','valid_deadline_closure','is_business_duplicate'}:
                lines.append('\t\tisHidden')
            if table=='dim_date' and column=='date':
                lines+=['\t\tisKey','\t\tformatString: M/d/yyyy']
            elif dt=='dateTime':
                lines.append('\t\tformatString: M/d/yyyy')
            elif dt=='double':
                lines.append('\t\tformatString: 0.00')
            if column=='month_name':
                lines.append('\t\tsortByColumn: month')
            if column=='year_month':
                lines.append('\t\tsortByColumn: month_sort')
            mtype={'int64':'Int64.Type','double':'type number','dateTime':'type datetime','string':'type text'}[dt]
            if table=='dim_date' and column=='date':
                mtype='type date'
            types.append('{"'+column+'", '+mtype+'}')
        if table=='fact_requests':
            for name,expression in measures().items():
                fmt='0.00' if any(s in name for s in ['Days','Hours']) else '0.00%' if 'Share' in name else '#,0'
                lines+=['',f"\tmeasure '{name}' ="]+['\t\t\t'+line for line in expression.splitlines()]
                if name not in {'Scope Label','Snapshot Date'}:
                    lines.append('\t\tformatString: '+fmt)
                lines+=['\t\tdisplayFolder: Portfolio metrics',f'\t\tlineageTag: {uid("measure/"+name)}']
        query=[f'Source = Csv.Document(File.Contents(pProjectFolder & "\\data\\powerbi\\{table}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          'Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
          'Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
          'Typed = Table.TransformColumnTypes(Nulls, {'+', '.join(types)+'}, "en-US")']
        lines+=['',f'\tpartition {table} = m','\t\tmode: import','\t\tsource =','\t\t\t\tlet']+['\t\t\t\t\t'+line for line in query]+['\t\t\t\tin','\t\t\t\t\tTyped','']
        write(MODEL/f'definition/tables/{table}.tmdl','\n'.join(lines))
    relationships=[]
    for table,key in [('dim_service','service_key'),('dim_organization','organization_key'),('dim_channel','channel_key'),('dim_date','created_date_key'),('dim_date','closed_date_key'),('dim_date','deadline_date_key')]:
        target='date_key' if table=='dim_date' else key
        relationships+=[f'relationship {uid("relationship/"+key)}',f'\tfromColumn: fact_requests.{key}',f'\ttoColumn: {table}.{target}']
        if key in {'closed_date_key','deadline_date_key'}:
            relationships.append('\tisActive: false')
        relationships.append('')
    write(MODEL/'definition/relationships.tmdl','\n'.join(relationships))


def build(portable=False):
    OUT.mkdir(parents=True,exist_ok=True)
    js(OUT/'A311.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'A311.Report'}}],'settings':{'enableAutoRecovery':True}})
    js(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../A311.SemanticModel'}}})
    # Desktop-created base theme and supported report metadata are preserved.
    template=ROOT.parents[1]/'work/pbi-native-template/Template.Report'
    if not template.exists():
        template=Path(__file__).resolve().parents[3]/'work/pbi-native-template/Template.Report'
    saved_base=ROOT/'powerbi/base-report'
    if not saved_base.exists():
        shutil.copytree(template,saved_base,ignore=shutil.ignore_patterns('.pbi','pages'))
    for relative in ['definition/report.json','definition/version.json','StaticResources/SharedResources/BaseThemes/Fluent2-CY26SU10.json']:
        target=REPORT/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(saved_base/relative,target)
    pages=[('Overview','Operations overview'),('Service','Service comparisons'),('Backlog','Reported backlog and quality')]
    js(REPORT/'definition/pages/pages.json',{'$schema':BASE+'pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages],'activePageName':'Overview'})
    for page,label in pages:
        page_filters=[categorical('dim_date','year',2025,'creation_year_'+page)]
        js(REPORT/f'definition/pages/{page}/page.json',{'$schema':BASE+'page/2.0.0/schema.json','name':page,'displayName':label,'displayOption':'FitToPage','height':720,'width':1280,
          'filterConfig':{'filters':page_filters},'objects':{'background':[{'properties':{'color':color('#F3F6F8'),'transparency':lit(0)}}]}})
        textbox(page,'heading','AUSTIN 311  |  '+label,24,12,1232,45,24,True,NAVY)
        textbox(page,'scope','Requests created in 2025  |  Statuses observed in Nov 7, 2026 export  |  Closure does not verify resolution',24,59,1232,33,11)
        slicer(page,'month','dim_date','year_month','Creation month',24,250)
        slicer(page,'service','dim_service','service_description','Service type',290,630)
        slicer(page,'channel','dim_channel','method_received','Receiving channel',936,320)
        textbox(page,'source','City of Austin · Dataset 38mr-dwji  |  Primary cohort excludes duplicate-marked and testing requests  |  Fixed age cutoff: Nov 7, 2026, 00:00 CT',24,678,1232,28,9)
    for i,(m,label,p) in enumerate([('Primary Requests','Primary requests',0),('Reported Closed Requests','Reported closed',0),('Reported Open Backlog','Reported open',0),('Median Closure Hours','Median closure · hours',2),('P90 Closure Days','P90 closure · days',2)]):
        card('Overview','kpi'+str(i),m,label,24+250*i,190,234,108,p)
    bar=visual('Overview','volume','barChart',24,318,608,344,{'Category':[projection('dim_service','service_description')],'Y':[projection('fact_requests','Top Eight Intake',True)]},'Leading services · primary request count',
      {'dataPoint':[{'properties':{'defaultColor':color(TEAL)}}],
       'categoryAxis':[{'properties':{'fontSize':lit(10),'showAxisTitle':lit(False)}}],
       'valueAxis':[{'properties':{'showAxisTitle':lit(False)}}],
       'labels':[{'properties':{'show':lit(True),'labelDisplayUnits':lit(1),'labelPrecision':lit(0),'fontSize':lit(10)}}]})
    bar['visual']['query']['sortDefinition']={'sort':[{'field':field('fact_requests','Top Eight Intake',True),'direction':'Descending'}],'isDefaultSort':False}
    js(REPORT/'definition/pages/Overview/visuals/volume/visual.json',bar)
    visual('Overview','monthly','lineChart',648,318,608,344,{'Category':[projection('dim_date','year_month')],'Y':[projection('fact_requests','Primary Requests',True)]},'Monthly intake · creation month',
      {'dataPoint':[{'properties':{'defaultColor':color(TEAL)}}], 'categoryAxis':[{'properties':{'fontSize':lit(10),'showAxisTitle':lit(False),'axisType':lit('Categorical')}}],
       'valueAxis':[{'properties':{'showAxisTitle':lit(False),'start':lit(0)}}]})
    for i,(m,label,p) in enumerate([('Duration Eligible Closed','Eligible closed requests',0),('Median Closure Days','Median closure · days',2),('P90 Closure Days','P90 closure · days',2),('Mean Closure Days','Mean closure · days',2),('Closed By Recorded Deadline Share','By recorded deadline',2)]):
        card('Service','kpi'+str(i),m,label,24+250*i,190,234,108,p)
    fields=[projection('dim_service','service_description',False,'Service type')]+[
      projection('fact_requests',m,True,label) for m,label in [('Primary Requests','Requests'),('Duration Eligible Closed','Eligible N'),('Median Closure Days','Median days'),('P90 Closure Days','P90 days'),('Closed By Recorded Deadline Share','By deadline'),('Reported Open Backlog','Reported open')]]
    visual('Service','performance','tableEx',24,318,1232,310,{'Values':fields},'Compare service types using volume, elapsed time and recorded targets',
      {'grid':[{'properties':{'gridVertical':lit(False),'gridHorizontal':lit(True),'rowPadding':lit(3)}}],
       'values':[{'properties':{'fontSize':lit(10)}}],'columnHeaders':[{'properties':{'fontSize':lit(10),'fontColor':color(NAVY)}}],
       'total':[{'properties':{'totals':lit(False)}}]})
    textbox('Service','interpretation','Long durations alone do not establish a missed target. Recorded deadlines vary by service; verified repair outcomes are unavailable.',24,637,1232,30,11)
    for i,(m,label,p) in enumerate([('Reported Open Backlog','Reported open · primary',0),('Reported Open Past Deadline','Open past recorded deadline',0),('Oldest Reported Open Age Days','Oldest reported open · days',1),('Flag Conflicts In Primary','Open/closed flag conflicts',0)]):
        card('Backlog','kpi'+str(i),m,label,24+312*i,190,296,95,p)
    detail=[projection('fact_requests',c,False,label) for c,label in [('request_number','Request'),('created_local','Created'),('last_updated_local','Last update'),('deadline_local','Recorded due')]]
    detail.insert(1,projection('dim_service','service_description',False,'Service type'))
    detail.append(projection('fact_requests','Open Age By Request',True,'Age days'))
    visual('Backlog','detail','tableEx',24,300,1232,304,{'Values':detail},'Reported open records · verify status in the live system',
      {'grid':[{'properties':{'gridVertical':lit(False),'gridHorizontal':lit(True),'rowPadding':lit(2)}}],
       'values':[{'properties':{'fontSize':lit(10)}}],'columnHeaders':[{'properties':{'fontSize':lit(10),'fontColor':color(NAVY)}}],
       'total':[{'properties':{'totals':lit(False)}}]},
      [categorical('fact_requests','in_primary',1,'backlog_primary'),categorical('fact_requests','is_open',1,'backlog_open')])
    textbox('Backlog','quality','Quality review: 4 ambiguous creation times excluded from durations; 378 gross-intake records lack geography. All 18 primary open records have old update dates.',24,615,1232,30,11)
    textbox('Backlog','verification','16 of the 18 primary open records were created May 1–5, 2025. Confirm current status before assigning recovery work.',24,646,1232,27,11,True,TEAL)
    make_model(portable)
    print(json.dumps({'project':str(OUT/'A311.pbip'),'pages':len(pages),'measures':len(measures()),'portable':portable},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--portable',action='store_true')
    build(p.parse_args().portable)
