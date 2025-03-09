# encoding: utf8
# date: 2024-12-18
# usage: 用于从wikidata上下载数据的脚本

import SPARQLWrapper
import json

if __name__ == "__main__":
    # 设置sparql查询的endpoint
    sparql = SPARQLWrapper.SPARQLWrapper("https://query.wikidata.org/sparql")

    # 设置查询语句
    sparql.setQuery("""
    SELECT ?item ?itemLabelZh ?itemLabelEn ?eventType ?eventTypeLabel ?startTime ?endTime 
    WHERE {
    ?item 
        wdt:P31 ?eventType;         # 词条类型是事件
        wdt:P580 ?startTime;      # 具有开始时间属性
        wdt:P582 ?endTime.       # 具有结束时间属性
    
    
    # 获取中文的itemLabel
    ?item rdfs:label ?itemLabelZh.
    FILTER(LANG(?itemLabelZh) = "zh")
    
    # 获取英文的itemLabel
    ?item rdfs:label ?itemLabelEn.
    FILTER(LANG(?itemLabelEn) = "en")
    
    FILTER (?startTime >= "1900-01-01T00:00:00Z"^^xsd:dateTime && ?startTime <= "2010-12-31T23:59:59Z"^^xsd:dateTime)
    FILTER (?endTime >= "1900-01-01T00:00:00Z"^^xsd:dateTime && ?endTime <= "2010-12-31T23:59:59Z"^^xsd:dateTime)
    
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    # LIMIT 100
    """)

    # 设置返回结果的格式
    sparql.setReturnFormat(SPARQLWrapper.JSON)

    # 执行查询并获取结果
    query_results: dict = sparql.query().convert()
    # 获取查询结果
    results: list[dict] = query_results["results"]["bindings"]
    print(f"查询到{len(results)}个结果")
    # 按照语言筛选结果
    filtered_results = []
    for result in results:
        try:
            itemLabelZh = result.get("itemLabelZh", {}).get("value")
            itemLabelEn = result.get("itemLabelEn", {}).get("value")
            if itemLabelZh and itemLabelEn:
                filtered_results.append(result)
        except Exception as e:
            print(f"处理结果时出现异常: {e}")
    
    print(f"筛选后的结果数量为: {len(filtered_results)}")
    # 将结果写入文件
    with open("wikidata_results.json", "w", encoding="utf8") as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=4)