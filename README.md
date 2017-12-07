# Data-correction-and-analysis-for-XML-data-in-OpenStreetMap
下载 OpenStreetMap 项目中一个区域的OSM XML文件，利用 Python 对 XML 文件进行数据审查及清洗，再导入 SQL，最后利用 SQL 对数据进行查询分析。
原始数据下载地址如下  
https://www.openstreetmap.org/relation/2315704   
https://mapzen.com/data/metro-extracts/metro/boston_massachusetts/   
“boston_massachusetts.osm”文件由"extract.py"对原始数据抽样1/40所得 
"audit.py"程序用于检测数据 
“data.py”提取数据中的一级元素节点和路径及其二级元素的信息并存入csv文件 
